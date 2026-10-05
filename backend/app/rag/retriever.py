"""Security-first, Role-Aware Medical RAG Retriever.

Enforces pre-retrieval authorization boundaries:
NEVER executes unrestricted semantic vector search across all documents.
Filters documents strictly BEFORE vector similarity retrieval.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.rag.embeddings import embedding_service
from app.rag.vector_store import vector_store

logger = logging.getLogger("healthcare.rag.retriever")


class RoleAwareRetriever:
    """
    Enforces HIPAA / PHI privacy boundaries and RBAC rules prior to vector similarity computation.
    """

    @classmethod
    def resolve_authorized_document_ids(
        cls,
        db: Session,
        user: User,
        target_patient_id: Optional[int] = None,
    ) -> List[int]:
        """
        Compute the exact set of KnowledgeDocument IDs the authenticated user is authorized to read.
        
        Strict Rules:
        1. PATIENT:
           - Allowed general reference documents (patient_id IS NULL and allowed_roles includes PATIENT or ALL).
           - Allowed OWN patient documents (patient_id == my_patient_profile.id).
           - FORBIDDEN from all other patients' documents.
        2. DOCTOR:
           - Allowed general clinical guidelines and protocols (patient_id IS NULL and allowed_roles includes DOCTOR or ALL).
           - If target_patient_id is requested, allowed ONLY IF doctor has an active clinical appointment relationship with that patient.
           - If no target_patient_id specified, allowed records of patients with whom they have an appointment relationship.
           - FORBIDDEN from unassigned/unrelated patients' records.
        3. LAB_TECHNICIAN:
           - Allowed laboratory reference intervals, testing protocols, specimen guidelines, LOINC dictionaries.
           - FORBIDDEN from private patient records / doctor notes.
        4. PHARMACY_STAFF:
           - Allowed drug monographs, pharmacology references, interaction guidelines, formulary data.
           - FORBIDDEN from private patient records / doctor notes.
        5. ADMIN:
           - Allowed operational guidelines, system policies, governance documents.
           - STRICT PRIVACY RULE: Admins are NEVER allowed access to patient clinical health records.
        """
        role = user.role
        user_id = user.id

        authorized_ids: Set[int] = set()

        # ---------------------------------------------------------------------
        # 1. PATIENT SCOPE
        # ---------------------------------------------------------------------
        if role == UserRole.PATIENT:
            patient_profile = (
                db.query(PatientProfile)
                .filter(PatientProfile.user_id == user_id)
                .first()
            )
            my_patient_id = patient_profile.id if patient_profile else None

            # General reference documents
            general_docs = (
                db.query(KnowledgeDocument.id, KnowledgeDocument.allowed_roles)
                .filter(KnowledgeDocument.patient_id.is_(None))
                .all()
            )
            for doc_id, roles in general_docs:
                if cls._role_permitted(roles, "PATIENT"):
                    authorized_ids.add(doc_id)

            # Own patient documents
            if my_patient_id:
                own_docs = (
                    db.query(KnowledgeDocument.id)
                    .filter(KnowledgeDocument.patient_id == my_patient_id)
                    .all()
                )
                for (doc_id,) in own_docs:
                    authorized_ids.add(doc_id)

            logger.info(
                f"RAG authorization filter applied: Patient #{user_id} authorized for {len(authorized_ids)} documents."
            )
            return list(authorized_ids)

        # ---------------------------------------------------------------------
        # 2. DOCTOR SCOPE
        # ---------------------------------------------------------------------
        elif role == UserRole.DOCTOR:
            doctor_profile = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.user_id == user_id)
                .first()
            )
            doctor_profile_id = doctor_profile.id if doctor_profile else None

            # General clinical guidelines and protocols
            general_docs = (
                db.query(KnowledgeDocument.id, KnowledgeDocument.allowed_roles)
                .filter(KnowledgeDocument.patient_id.is_(None))
                .all()
            )
            for doc_id, roles in general_docs:
                if cls._role_permitted(roles, "DOCTOR"):
                    authorized_ids.add(doc_id)

            # Patient-specific documents with verified appointment relationship
            if doctor_profile_id:
                if target_patient_id is not None:
                    # Explicit patient queried: verify clinical relationship
                    has_rel = (
                        db.query(Appointment)
                        .filter(
                            Appointment.doctor_id == doctor_profile_id,
                            Appointment.patient_id == target_patient_id,
                        )
                        .first()
                    )
                    if has_rel:
                        p_docs = (
                            db.query(KnowledgeDocument.id)
                            .filter(KnowledgeDocument.patient_id == target_patient_id)
                            .all()
                        )
                        for (doc_id,) in p_docs:
                            authorized_ids.add(doc_id)
                    else:
                        logger.warning(
                            f"Doctor #{user_id} attempted access to Patient #{target_patient_id} without clinical relationship."
                        )
                else:
                    # Doctor can access documents of all patients they actively treat
                    related_patient_ids = [
                        appt.patient_id
                        for appt in db.query(Appointment.patient_id)
                        .filter(Appointment.doctor_id == doctor_profile_id)
                        .distinct()
                        .all()
                    ]
                    if related_patient_ids:
                        p_docs = (
                            db.query(KnowledgeDocument.id)
                            .filter(KnowledgeDocument.patient_id.in_(related_patient_ids))
                            .all()
                        )
                        for (doc_id,) in p_docs:
                            authorized_ids.add(doc_id)

            logger.info(
                f"RAG authorization filter applied: Doctor #{user_id} authorized for {len(authorized_ids)} documents."
            )
            return list(authorized_ids)

        # ---------------------------------------------------------------------
        # 3. LAB TECHNICIAN SCOPE
        # ---------------------------------------------------------------------
        elif role == UserRole.LAB_TECHNICIAN:
            general_docs = (
                db.query(KnowledgeDocument.id, KnowledgeDocument.allowed_roles)
                .filter(KnowledgeDocument.patient_id.is_(None))
                .all()
            )
            for doc_id, roles in general_docs:
                if cls._role_permitted(roles, "LAB_TECHNICIAN"):
                    authorized_ids.add(doc_id)

            logger.info(
                f"RAG authorization filter applied: Lab Tech #{user_id} authorized for {len(authorized_ids)} documents."
            )
            return list(authorized_ids)

        # ---------------------------------------------------------------------
        # 4. PHARMACY STAFF SCOPE
        # ---------------------------------------------------------------------
        elif role == UserRole.PHARMACY_STAFF:
            general_docs = (
                db.query(KnowledgeDocument.id, KnowledgeDocument.allowed_roles)
                .filter(KnowledgeDocument.patient_id.is_(None))
                .all()
            )
            for doc_id, roles in general_docs:
                if cls._role_permitted(roles, "PHARMACY_STAFF"):
                    authorized_ids.add(doc_id)

            logger.info(
                f"RAG authorization filter applied: Pharmacy Staff #{user_id} authorized for {len(authorized_ids)} documents."
            )
            return list(authorized_ids)

        # ---------------------------------------------------------------------
        # 5. ADMIN SCOPE (STRICT PRIVACY - NO PATIENT CLINICAL DATA)
        # ---------------------------------------------------------------------
        elif role == UserRole.ADMIN:
            general_docs = (
                db.query(KnowledgeDocument.id, KnowledgeDocument.allowed_roles)
                .filter(KnowledgeDocument.patient_id.is_(None))
                .all()
            )
            for doc_id, roles in general_docs:
                if cls._role_permitted(roles, "ADMIN"):
                    authorized_ids.add(doc_id)

            logger.info(
                f"RAG authorization filter applied: Admin #{user_id} authorized for {len(authorized_ids)} administrative documents (0 patient records)."
            )
            return list(authorized_ids)

        return []

    @staticmethod
    def _role_permitted(allowed_roles: Any, role_str: str) -> bool:
        """Check if role_str or wildcard is in allowed_roles list/JSON."""
        if not allowed_roles:
            return True
        if isinstance(allowed_roles, list):
            upper_roles = [str(r).upper() for r in allowed_roles]
            return "ALL" in upper_roles or "*" in upper_roles or role_str.upper() in upper_roles
        if isinstance(allowed_roles, str):
            clean = allowed_roles.upper().strip()
            return clean in ("ALL", "*", role_str.upper())
        return False

    @classmethod
    def retrieve(
        cls,
        db: Session,
        query: str,
        user: User,
        target_patient_id: Optional[int] = None,
        document_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        top_k: int = 5,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Execute fully authorized semantic retrieval pipeline:
        1. Resolve allowed document IDs strictly by user RBAC and patient relationship.
        2. If 0 documents are authorized, returns empty list immediately without querying vectors.
        3. Embed query text once using isolated embedding service.
        4. Query vector store constrained by allowed_document_ids and temporal filters.
        """
        logger.info(f"RAG retrieval started for user #{user.id} ({user.role.value}). Query length: {len(query)}")

        # Step 1: Pre-authorization filtering
        allowed_doc_ids = cls.resolve_authorized_document_ids(
            db=db,
            user=user,
            target_patient_id=target_patient_id,
        )

        if not allowed_doc_ids:
            logger.info("RAG pre-authorization: No documents authorized for this user/scope.")
            return []

        # Step 2: Generate single query embedding
        query_embedding = embedding_service.embed_query(query)
        if not query_embedding:
            logger.warning("RAG embedding failed to generate query vector.")
            return []

        # Step 3: Vector search constrained strictly to allowed documents
        chunks_with_scores = vector_store.similarity_search(
            db=db,
            query_embedding=query_embedding,
            allowed_document_ids=allowed_doc_ids,
            document_type=document_type,
            date_from=date_from,
            date_to=date_to,
            top_k=top_k,
        )

        logger.info(f"RAG retrieval completed. Retrieved chunks: {len(chunks_with_scores)}")
        return chunks_with_scores


role_aware_retriever = RoleAwareRetriever()
