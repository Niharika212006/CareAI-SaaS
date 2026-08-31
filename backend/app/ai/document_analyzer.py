"""Responsible LLM-Powered Medical Document Analysis Engine with Pydantic Output Validation."""
import re
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from app.ai.client import ai_client, AIProviderUnavailableError, AIInvalidResponseError

logger = logging.getLogger("healthcare.ai.document_analyzer")

DOCUMENT_ANALYSIS_DISCLAIMER = (
    "This AI-generated analysis is for informational and educational purposes only "
    "and does not constitute a medical diagnosis, clinical prognosis, or treatment plan. "
    "Always consult a qualified physician or healthcare professional for diagnosis, "
    "test interpretation, and medical advice."
)

SYSTEM_PROMPT = """You are a responsible Clinical AI Health Assistant assisting in structuring and summarizing medical records.

STRICT INSTRUCTIONS:
1. Analyze ONLY the text explicitly provided between the delimiters.
2. DO NOT invent, assume, extrapolate, or hallucinate medications, test values, numbers, or clinical conditions.
3. If information is missing or unclear, state "Not clearly available in the document."
4. DO NOT diagnose diseases or state definitive clinical conclusions.
5. DO NOT recommend starting, changing, or stopping medications.
6. DO NOT provide emergency medical instructions.
7. Distinguish observed numbers/facts from potential discussion points.
8. Maintain a responsible, calm, non-alarmist tone.
9. Return a STRICT JSON object conforming to the required schema with no additional commentary.

JSON Schema format:
{
  "summary": "High-level informational overview of the document (2-3 sentences)",
  "document_category": "Category such as Complete Blood Count, Metabolic Panel, Radiology Report, Prescription, etc.",
  "key_findings": ["Bullet point finding 1", "Bullet point finding 2"],
  "detected_medications": [
    {"name": "Medication Name", "dosage": "Dosage if present or 'Not specified'"}
  ],
  "detected_test_values": [
    {"test": "Test Name", "value": "Value with units", "reference_context": "Standard reference context or Flagged"}
  ],
  "potential_concerns": [
    {"level": "low|medium|high", "message": "Non-alarmist observation to discuss with doctor"}
  ],
  "patient_friendly_explanation": "Clear non-technical explanation for the patient",
  "recommended_next_step": "Advisory recommendation to discuss findings with their doctor",
  "disclaimer": "This AI-generated analysis is for informational and educational purposes only and does not constitute a medical diagnosis, clinical prognosis, or treatment plan. Always consult a qualified physician or healthcare professional for diagnosis, test interpretation, and medical advice."
}
"""


class ParsedMedication(BaseModel):
    name: str
    dosage: Optional[str] = "Not specified"


class ParsedTestValue(BaseModel):
    test: str
    value: str
    reference_context: Optional[str] = None


class ParsedConcern(BaseModel):
    level: str = "low"  # low, medium, high
    message: str


class DocumentAnalysisResult(BaseModel):
    summary: str
    document_category: str = "General Medical Record"
    key_findings: List[str] = Field(default_factory=list)
    detected_medications: List[ParsedMedication] = Field(default_factory=list)
    detected_test_values: List[ParsedTestValue] = Field(default_factory=list)
    potential_concerns: List[ParsedConcern] = Field(default_factory=list)
    patient_friendly_explanation: str
    recommended_next_step: str
    disclaimer: str = DOCUMENT_ANALYSIS_DISCLAIMER
    ai_model_name: str


class DocumentAnalyzer:
    """Orchestrates genuine LLM prompt framing, inference, and Pydantic validation."""

    def analyze_extracted_text(
        self,
        extracted_text: str,
        document_title: str = "Medical Document",
        document_type_hint: Optional[str] = None,
        force_heuristic_fallback: bool = False,
    ) -> DocumentAnalysisResult:
        """
        Execute LLM analysis on extracted document text.
        Invokes AIClient for foundation model inference (Gemini/OpenAI) and validates schema with Pydantic.
        """
        clean_text = (extracted_text or "").strip()
        if not clean_text:
            raise ValueError("No extractable text provided for analysis.")

        # If explicit heuristic mode is requested (for testing/development fallback)
        if force_heuristic_fallback:
            return self.analyze_with_heuristic_rules(clean_text, document_title, document_type_hint)

        # 1. Delimited Prompt Construction
        user_prompt = (
            f"Please analyze the following extracted medical document text:\n\n"
            f"Document Title: {document_title}\n"
            f"Document Type Hint: {document_type_hint or 'Unknown'}\n\n"
            f"=== DOCUMENT TEXT START ===\n"
            f"{clean_text}\n"
            f"=== DOCUMENT TEXT END ===\n\n"
            f"Provide the structured JSON analysis adhering strictly to the system instructions."
        )

        # 2. Invoke Genuine AIClient
        raw_response = ai_client.generate_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_mime_type="application/json",
        )

        # 3. Clean & Parse JSON Response
        parsed_json = self._extract_and_parse_json(raw_response)

        # 4. Enforce Real Model Identifier
        parsed_json["ai_model_name"] = ai_client.model_name
        parsed_json["disclaimer"] = DOCUMENT_ANALYSIS_DISCLAIMER

        # 5. Validate Schema with Pydantic
        try:
            result = DocumentAnalysisResult.model_validate(parsed_json)
            return result
        except ValidationError as val_err:
            logger.error(f"LLM structured output failed Pydantic validation: {val_err}")
            raise AIInvalidResponseError("AI model response did not conform to the expected clinical schema.") from val_err

    def _extract_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Extract and parse JSON object from LLM response text."""
        if not raw_text or not raw_text.strip():
            raise AIInvalidResponseError("Received empty response from AI model.")

        text = raw_text.strip()
        # Handle markdown JSON codeblocks (e.g. ```json ... ```)
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise AIInvalidResponseError("AI response is not a valid JSON object.")
            return data
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to decode LLM JSON: {json_err}. Raw text: {raw_text[:200]}")
            raise AIInvalidResponseError("AI model returned malformed JSON.") from json_err

    def analyze_with_heuristic_rules(
        self,
        clean_text: str,
        document_title: str,
        document_type_hint: Optional[str] = None,
    ) -> DocumentAnalysisResult:
        """
        Transparently labeled deterministic heuristic parser.
        Used strictly when explicit fallback is chosen.
        """
        lab_patterns = [
            (r"(?i)(fasting\s*blood\s*glucose|glucose|blood\s*sugar)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|mmol/L)?)", "Glucose"),
            (r"(?i)(hba1c|glycated\s*hemoglobin)\s*[:=\-]?\s*([\d\.]+\s*%)", "HbA1c"),
            (r"(?i)(total\s*cholesterol)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|mmol/L)?)", "Total Cholesterol"),
            (r"(?i)(triglycerides)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|mmol/L)?)", "Triglycerides"),
            (r"(?i)(hdl\s*cholesterol|hdl)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|mmol/L)?)", "HDL Cholesterol"),
            (r"(?i)(ldl\s*cholesterol|ldl)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|mmol/L)?)", "LDL Cholesterol"),
            (r"(?i)(hemoglobin|hgb)\s*[:=\-]?\s*([\d\.]+\s*(?:g/dL|g/L)?)", "Hemoglobin"),
            (r"(?i)(white\s*blood\s*cell|wbc)\s*[:=\-]?\s*([\d\.]+\s*(?:x10\^3/\u00b5L|/\u00b5L|k/\u00b5L)?)", "White Blood Cells"),
            (r"(?i)(platelets?|plt)\s*[:=\-]?\s*([\d\.]+\s*(?:x10\^3/\u00b5L|/\u00b5L|k/\u00b5L)?)", "Platelets"),
            (r"(?i)(creatinine)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL|\u00b5mol/L)?)", "Creatinine"),
            (r"(?i)(blood\s*urea\s*nitrogen|bun)\s*[:=\-]?\s*([\d\.]+\s*(?:mg/dL)?)", "BUN"),
            (r"(?i)(tsh|thyroid\s*stimulating\s*hormone)\s*[:=\-]?\s*([\d\.]+\s*(?:mIU/L|\u00b5IU/mL)?)", "TSH"),
            (r"(?i)(blood\s*pressure|bp)\s*[:=\-]?\s*(\d{2,3}\s*/\s*\d{2,3}\s*(?:mmHg)?)", "Blood Pressure"),
            (r"(?i)(sgpt|alt)\s*[:=\-]?\s*([\d\.]+\s*(?:U/L|IU/L)?)", "ALT (Liver Enzyme)"),
            (r"(?i)(sgot|ast)\s*[:=\-]?\s*([\d\.]+\s*(?:U/L|IU/L)?)", "AST (Liver Enzyme)"),
        ]

        medication_keywords = [
            "amoxicillin", "penicillin", "metformin", "lisinopril", "atorvastatin", "amlodipine",
            "omeprazole", "levothyroxine", "losartan", "azithromycin", "ciprofloxacin", "aspirin",
            "ibuprofen", "paracetamol", "acetaminophen", "warfarin", "clopidogrel", "sertraline",
            "metoprolol", "pantoprazole", "gabapentin", "hydrochlorothiazide", "furosemide"
        ]

        detected_tests: List[ParsedTestValue] = []
        for pattern, test_name in lab_patterns:
            match = re.search(pattern, clean_text)
            if match:
                val = match.group(2).strip()
                context = "Recorded Value"
                context_window = clean_text[max(0, match.start() - 30): min(len(clean_text), match.end() + 30)].lower()
                if "high" in context_window or "elevated" in context_window:
                    context = "Flagged: Higher than standard reference range"
                elif "low" in context_window or "decreased" in context_window:
                    context = "Flagged: Lower than standard reference range"
                elif "normal" in context_window:
                    context = "Within standard reference range"
                detected_tests.append(ParsedTestValue(test=test_name, value=val, reference_context=context))

        detected_meds: List[ParsedMedication] = []
        for med in medication_keywords:
            med_match = re.search(rf"(?i)\b({med})\b(?:\s+(\d+\s*(?:mg|mcg|g|ml)))?", clean_text)
            if med_match:
                med_name = med_match.group(1).capitalize()
                dosage = med_match.group(2) if med_match.group(2) else "Not specified"
                detected_meds.append(ParsedMedication(name=med_name, dosage=dosage))

        category = "General Medical Record"
        if "cbc" in clean_text.lower() or "hemoglobin" in clean_text.lower():
            category = "Hematology / Complete Blood Count (CBC)"
        elif "glucose" in clean_text.lower() or "lipid" in clean_text.lower():
            category = "Clinical Biochemistry / Metabolic Panel"
        elif document_type_hint:
            category = document_type_hint.replace("_", " ").title()

        key_findings = [f"{t.test} was recorded at {t.value}." for t in detected_tests]
        if not key_findings:
            key_findings = ["No standard laboratory markers isolated."]

        concerns = [
            ParsedConcern(
                level="low",
                message="Deterministic rule engine did not flag critical values. Consult a physician for clinical review.",
            )
        ]

        return DocumentAnalysisResult(
            summary=f"Rule-based extraction for '{document_title}'. Contains {len(detected_tests)} test measurement(s).",
            document_category=category,
            key_findings=key_findings,
            detected_medications=detected_meds,
            detected_test_values=detected_tests,
            potential_concerns=concerns,
            patient_friendly_explanation="Rule-based heuristic parsing extracted key terms from this document.",
            recommended_next_step="Consult a qualified healthcare provider for clinical evaluation.",
            disclaimer=DOCUMENT_ANALYSIS_DISCLAIMER,
            ai_model_name="CareAI-Heuristic-Ruleset-v1",
        )


document_analyzer = DocumentAnalyzer()
