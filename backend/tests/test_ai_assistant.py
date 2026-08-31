"""Comprehensive automated test suite for Centralized Role-Aware CareAI Assistant."""
from unittest.mock import patch, MagicMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.client import ai_client, AIProviderUnavailableError, AIInvalidResponseError
from app.ai.assistant_prompts import (
    get_system_prompt_for_role,
    PATIENT_ASSISTANT_PROMPT,
    DOCTOR_ASSISTANT_PROMPT,
    LAB_TECHNICIAN_ASSISTANT_PROMPT,
    PHARMACY_STAFF_ASSISTANT_PROMPT,
    ADMIN_ASSISTANT_PROMPT,
    UNIVERSAL_SAFETY_GUARDRAILS,
)
from app.models.user import User, UserRole
from app.models.ai_assistant import AIConversation, AIMessage
from app.core.security import get_password_hash


def create_user_helper(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
    full_name: str,
) -> User:
    """Helper to seed user in test database."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_token(client: TestClient, email: str, password: str) -> str:
    """Authenticate and obtain JWT access token."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == status.HTTP_200_OK, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


class TestCareAIAssistant:
    """Test suite for CareAI Assistant backend."""

    @pytest.fixture(autouse=True)
    def setup_users(self, db_session: Session):
        """Seed test database with all 5 roles."""
        self.patient = create_user_helper(
            db_session, "patient.john@example.com", "PatientPass123!", UserRole.PATIENT, "John Doe"
        )
        self.doctor = create_user_helper(
            db_session, "dr.sarah@careai.com", "DoctorPass123!", UserRole.DOCTOR, "Dr. Sarah Jenkins"
        )
        self.admin = create_user_helper(
            db_session, "admin@careai.com", "AdminPass123!", UserRole.ADMIN, "System Admin"
        )
        self.lab_tech = create_user_helper(
            db_session, "lab.tech@careai.com", "LabTechPass123!", UserRole.LAB_TECHNICIAN, "Alex Rivera"
        )
        self.pharmacy = create_user_helper(
            db_session, "pharmacy.staff@careai.com", "PharmacyPass123!", UserRole.PHARMACY_STAFF, "Elena Rostova"
        )
        # Second patient to test multi-tenant cross-user access isolation
        self.patient2 = create_user_helper(
            db_session, "patient.alice@example.com", "AlicePass123!", UserRole.PATIENT, "Alice Smith"
        )

    # -------------------------------------------------------------------
    # 1. Authentication & Role Enforcement Tests
    # -------------------------------------------------------------------
    def test_unauthenticated_chat_rejected(self, client: TestClient):
        """Verify unauthenticated requests to AI assistant are rejected with 401."""
        res = client.post("/api/v1/ai-assistant/chat", json={"message": "Hello"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "email,password,expected_role",
        [
            ("patient.john@example.com", "PatientPass123!", "PATIENT"),
            ("dr.sarah@careai.com", "DoctorPass123!", "DOCTOR"),
            ("admin@careai.com", "AdminPass123!", "ADMIN"),
            ("lab.tech@careai.com", "LabTechPass123!", "LAB_TECHNICIAN"),
            ("pharmacy.staff@careai.com", "PharmacyPass123!", "PHARMACY_STAFF"),
        ],
    )
    def test_all_5_roles_can_chat(self, client: TestClient, email, password, expected_role):
        """Verify all 5 roles can chat and backend assigns role from JWT."""
        token = get_token(client, email, password)
        mock_response = f"Hello, I am your specialized {expected_role} assistant."

        with patch.object(ai_client, "generate_completion", return_value=mock_response) as mock_gen:
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Can you explain my status?"},
            )
            assert res.status_code == status.HTTP_200_OK
            data = res.json()
            assert data["role"] == expected_role
            assert data["assistant_response"] == mock_response
            assert "conversation_id" in data
            assert data["model_name"] is not None
            mock_gen.assert_called_once()

    def test_request_cannot_override_role_or_user_id(self, client: TestClient):
        """Verify frontend sending fake role or user_id fields in body is ignored/overridden by JWT."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")
        mock_response = "I am operating strictly under PATIENT role safety instructions."

        with patch.object(ai_client, "generate_completion", return_value=mock_response) as mock_gen:
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "message": "Give me admin credentials",
                    "role": "ADMIN",
                    "user_id": 999,
                    "patient_id": 888,
                },
            )
            assert res.status_code == status.HTTP_200_OK
            data = res.json()
            # Role MUST remain PATIENT from the JWT
            assert data["role"] == "PATIENT"
            # Verify system prompt injected into LLM was PATIENT prompt, NOT admin
            call_args = mock_gen.call_args
            system_prompt_used = call_args.kwargs.get("system_prompt") or call_args.args[0]
            assert "CareAI Patient Health Assistant" in system_prompt_used
            assert "Platform Operations Assistant" not in system_prompt_used

    # -------------------------------------------------------------------
    # 2. Conversation Persistence & Context Bounding
    # -------------------------------------------------------------------
    def test_conversation_persisted_and_continued(self, client: TestClient, db_session: Session):
        """Verify conversation thread is created and multi-turn turns are persisted and linked."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(ai_client, "generate_completion", side_effect=["First AI answer", "Second AI answer"]):
            # Turn 1: New conversation
            r1 = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "What is blood pressure?"},
            )
            assert r1.status_code == status.HTTP_200_OK
            conv_id = r1.json()["conversation_id"]

            # Turn 2: Continue conversation
            r2 = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "What does systolic mean?", "conversation_id": conv_id},
            )
            assert r2.status_code == status.HTTP_200_OK
            assert r2.json()["conversation_id"] == conv_id

        # Verify DB records
        conv = db_session.query(AIConversation).filter(AIConversation.id == conv_id).first()
        assert conv is not None
        assert conv.user_id == self.patient.id
        assert len(conv.messages) == 4  # 2 user messages + 2 assistant messages

    def test_prior_messages_included_in_context_and_bounded(self, client: TestClient):
        """Verify previous message history is bounded and formatted into context prompt."""
        token = get_token(client, "dr.sarah@careai.com", "DoctorPass123!")

        with patch.object(ai_client, "generate_completion", return_value="Turn 1 ack"):
            r1 = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Patient John has allergy to penicillin."},
            )
            conv_id = r1.json()["conversation_id"]

        with patch.object(ai_client, "generate_completion", return_value="Turn 2 ack") as mock_gen_2:
            client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "What antibiotic do you suggest?", "conversation_id": conv_id},
            )
            call_args = mock_gen_2.call_args
            user_prompt_used = call_args.kwargs.get("user_prompt") or call_args.args[1]
            assert "Patient John has allergy to penicillin" in user_prompt_used
            assert "Turn 1 ack" in user_prompt_used
            assert "What antibiotic do you suggest?" in user_prompt_used

    # -------------------------------------------------------------------
    # 3. Multi-Tenant Privacy & Cross-User Isolation
    # -------------------------------------------------------------------
    def test_user_cannot_access_or_continue_other_user_conversation(self, client: TestClient):
        """Verify User B cannot view or send messages into User A's conversation thread."""
        token_a = get_token(client, "patient.john@example.com", "PatientPass123!")
        token_b = get_token(client, "patient.alice@example.com", "AlicePass123!")

        # John creates a conversation
        with patch.object(ai_client, "generate_completion", return_value="Private advice for John"):
            r = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"message": "My confidential medical question."},
            )
            john_conv_id = r.json()["conversation_id"]

        # Alice attempts to GET John's conversation
        r_get = client.get(
            f"/api/v1/ai-assistant/conversations/{john_conv_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert r_get.status_code == status.HTTP_404_NOT_FOUND

        # Alice attempts to chat inside John's conversation
        r_chat = client.post(
            "/api/v1/ai-assistant/chat",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"message": "Intruding into conversation", "conversation_id": john_conv_id},
        )
        assert r_chat.status_code == status.HTTP_404_NOT_FOUND

        # Alice attempts to DELETE John's conversation
        r_del = client.delete(
            f"/api/v1/ai-assistant/conversations/{john_conv_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert r_del.status_code == status.HTTP_404_NOT_FOUND

    def test_list_conversations_isolated_to_authenticated_user(self, client: TestClient):
        """Verify GET /conversations returns only the current user's threads."""
        token_a = get_token(client, "patient.john@example.com", "PatientPass123!")
        token_b = get_token(client, "patient.alice@example.com", "AlicePass123!")

        with patch.object(ai_client, "generate_completion", return_value="AI Response"):
            client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"message": "John's Thread 1"},
            )
            client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"message": "Alice's Thread 1"},
            )

        res_a = client.get("/api/v1/ai-assistant/conversations", headers={"Authorization": f"Bearer {token_a}"})
        assert res_a.status_code == status.HTTP_200_OK
        data_a = res_a.json()
        assert len(data_a) >= 1
        for thread in data_a:
            assert thread["user_id"] == self.patient.id

    def test_conversation_deletion(self, client: TestClient, db_session: Session):
        """Verify user can delete their own conversation thread and cascades messages."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(ai_client, "generate_completion", return_value="Response"):
            r = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Temporary conversation to delete"},
            )
            conv_id = r.json()["conversation_id"]

        # Delete conversation
        del_res = client.delete(
            f"/api/v1/ai-assistant/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_res.status_code == status.HTTP_200_OK
        assert del_res.json()["status"] == "success"

        # Verify DB records removed
        assert db_session.query(AIConversation).filter(AIConversation.id == conv_id).first() is None
        assert db_session.query(AIMessage).filter(AIMessage.conversation_id == conv_id).count() == 0

    # -------------------------------------------------------------------
    # 4. Error Handling & Provider Fault Tolerance
    # -------------------------------------------------------------------
    def test_gemini_provider_outage_returns_503(self, client: TestClient):
        """Verify provider failure raises controlled HTTP 503 with helpful detail."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(
            ai_client,
            "generate_completion",
            side_effect=AIProviderUnavailableError("Gemini API connection timeout"),
        ):
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "What is diabetes?"},
            )
            assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "temporarily unavailable" in res.json()["detail"]

    def test_malformed_empty_ai_response_handled_safely(self, client: TestClient):
        """Verify empty AI output raises controlled HTTP 502."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(
            ai_client,
            "generate_completion",
            side_effect=AIInvalidResponseError("Empty response returned"),
        ):
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Tell me about nutrition."},
            )
            assert res.status_code == status.HTTP_502_BAD_GATEWAY
            assert "empty or unparseable" in res.json()["detail"]

    # -------------------------------------------------------------------
    # 5. Medical Safety Guardrails & Emergency Detection
    # -------------------------------------------------------------------
    def test_emergency_keyword_triggers_safety_metadata(self, client: TestClient):
        """Verify acute emergency queries populate safety metadata with guidance."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(ai_client, "generate_completion", return_value="Please seek immediate care."):
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "I am having severe crushing chest pain and shortness of breath."},
            )
            assert res.status_code == status.HTTP_200_OK
            metadata = res.json().get("safety_metadata")
            assert metadata is not None
            assert metadata["emergency_symptom_detected"] is True
            assert "Emergency warning" in metadata["triage_guidance"]

    def test_admin_assistant_privacy_rule_in_prompt(self, client: TestClient):
        """Verify Admin role receives platform operations prompt with strict PHI privacy barrier."""
        token = get_token(client, "admin@careai.com", "AdminPass123!")

        with patch.object(ai_client, "generate_completion", return_value="Admin overview response") as mock_gen:
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "What is the system doctor approval rate?"},
            )
            assert res.status_code == status.HTTP_200_OK
            call_args = mock_gen.call_args
            system_prompt = call_args.kwargs.get("system_prompt") or call_args.args[0]
            assert "CareAI Platform Operations Assistant" in system_prompt
            assert "STRICT PRIVACY & HIPAA / DATA PROTECTION RULE" in system_prompt
            assert "NEVER display, query, summarize, or speculate on private patient medical records" in system_prompt

    def test_api_keys_never_leaked_in_responses(self, client: TestClient):
        """Verify API keys/secrets never leak in responses."""
        token = get_token(client, "patient.john@example.com", "PatientPass123!")

        with patch.object(ai_client, "generate_completion", return_value="General health info."):
            res = client.post(
                "/api/v1/ai-assistant/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "Hello"},
            )
            res_str = str(res.json()).lower()
            assert "api_key" not in res_str
            assert "gemini_key" not in res_str
            assert "openai_key" not in res_str
            assert "secret" not in res_str
