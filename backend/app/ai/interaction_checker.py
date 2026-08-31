"""Deterministic Clinical Interaction and Safety Analysis Engine."""
from typing import Dict, List, Optional, Set, Tuple
from app.models.ai_report import InteractionSeverity
from app.ai.normalizer import normalize_medication_name
from app.ai.knowledge_base import knowledge_base
from app.schemas.ai import SafetyFinding, AIInteractionCheckRequest, AISafetyReportResponse

DISCLAIMER_TEXT = (
    "This analysis is intended for informational and clinical decision support purposes only. "
    "It does not replace professional medical advice, diagnosis, or treatment. "
    "Consult a qualified healthcare professional before making decisions about medications."
)


class InteractionChecker:
    """
    Core Deterministic Safety Evaluation Engine.
    Executes rule-based multi-drug cross referencing against clinical knowledge bases,
    patient hypersensitivities, food restrictions, and therapeutic duplication.
    """

    @staticmethod
    def run_safety_analysis(
        medications: List[str],
        patient_allergies: Optional[List[str]] = None,
        patient_conditions: Optional[List[str]] = None,
        prescription_id: Optional[int] = None,
        patient_id: Optional[int] = None,
    ) -> AISafetyReportResponse:
        """
        Execute comprehensive multi-vector safety audit.
        """
        if not medications:
            return AISafetyReportResponse(
                prescription_id=prescription_id,
                patient_id=patient_id,
                overall_risk_level=InteractionSeverity.NONE,
                total_findings=0,
                findings=[],
                drug_drug_interactions=[],
                drug_food_interactions=[],
                drug_allergy_interactions=[],
                summary="No medications provided for safety analysis.",
                clinical_summary="No medications provided for safety analysis.",
                ai_recommendations=[],
                disclaimer=DISCLAIMER_TEXT,
            )

        # 1. Normalize medications while retaining original display names
        normalized_meds: List[Tuple[str, str]] = []  # (original, normalized)
        for raw_med in medications:
            norm = normalize_medication_name(raw_med)
            if norm:
                normalized_meds.append((raw_med.strip(), norm))

        all_findings: List[SafetyFinding] = []
        ddi_findings: List[SafetyFinding] = []
        dfi_findings: List[SafetyFinding] = []
        dai_findings: List[SafetyFinding] = []
        dup_findings: List[SafetyFinding] = []
        recommendations: List[str] = []

        # -----------------------------------------------------------------
        # Category A: Drug-Drug Interactions (DDI)
        # -----------------------------------------------------------------
        for i in range(len(normalized_meds)):
            for j in range(i + 1, len(normalized_meds)):
                raw_a, norm_a = normalized_meds[i]
                raw_b, norm_b = normalized_meds[j]

                # Match against knowledge base rules
                current_pair = {norm_a, norm_b}
                for rule in knowledge_base.DRUG_DRUG_RULES:
                    if rule["drugs"] == current_pair:
                        finding = SafetyFinding(
                            category="DRUG_DRUG",
                            severity=rule["severity"],
                            medications=[raw_a, raw_b],
                            title=rule.get("title", f"{raw_a} + {raw_b}"),
                            explanation=rule["explanation"],
                            recommended_action=rule["recommended_action"],
                        )
                        ddi_findings.append(finding)
                        all_findings.append(finding)
                        recommendations.append(
                            f"[{finding.severity.value} DDI] {finding.medications[0]} + {finding.medications[1]}: {finding.explanation}"
                        )

        # -----------------------------------------------------------------
        # Category B: Drug-Food / Dietary Interactions (DFI)
        # -----------------------------------------------------------------
        for raw_med, norm_med in normalized_meds:
            for rule in knowledge_base.DRUG_FOOD_RULES:
                if rule["drug"] == norm_med:
                    finding = SafetyFinding(
                        category="DRUG_FOOD",
                        severity=rule["severity"],
                        medications=[raw_med],
                        title=rule.get("title", f"{raw_med} Dietary Restriction"),
                        explanation=rule["explanation"],
                        recommended_action=rule["recommended_action"],
                    )
                    dfi_findings.append(finding)
                    all_findings.append(finding)
                    recommendations.append(
                        f"[{finding.severity.value} Food Advisory] {raw_med}: {rule['title']}"
                    )

        # -----------------------------------------------------------------
        # Category C: Drug-Allergy Contraindications (DAI)
        # -----------------------------------------------------------------
        cleaned_allergies: List[str] = []
        if patient_allergies:
            for allergy_entry in patient_allergies:
                if allergy_entry and isinstance(allergy_entry, str):
                    for sub_allergy in allergy_entry.replace(";", ",").split(","):
                        cleaned = sub_allergy.lower().strip()
                        if cleaned and cleaned not in ["none", "nil", "n/a", "no"]:
                            cleaned_allergies.append(cleaned)

        for raw_med, norm_med in normalized_meds:
            for allergy in cleaned_allergies:
                # 1. Check Class Cross-Reactivity (e.g., Penicillin -> Amoxicillin)
                matched_class = None
                for class_name, class_info in knowledge_base.ALLERGY_CLASS_MAP.items():
                    if class_name in allergy or allergy in class_name:
                        if norm_med in class_info["cross_reactive_drugs"] or any(
                            d in raw_med.lower() for d in class_info["cross_reactive_drugs"]
                        ):
                            matched_class = class_info
                            break

                if matched_class:
                    finding = SafetyFinding(
                        category="DRUG_ALLERGY",
                        severity=matched_class["severity"],
                        medications=[raw_med, allergy.capitalize()],
                        title=f"Allergy Contraindication: {raw_med} (Allergy: {allergy.capitalize()})",
                        explanation=matched_class["explanation"],
                        recommended_action=matched_class["recommended_action"],
                    )
                    dai_findings.append(finding)
                    all_findings.append(finding)
                    recommendations.append(
                        f"[CRITICAL ALLERGY ALERT] Patient recorded allergy '{allergy}' conflicts with prescribed '{raw_med}'."
                    )
                # 2. Direct name matching if not caught by class map
                elif allergy in norm_med or norm_med in allergy:
                    finding = SafetyFinding(
                        category="DRUG_ALLERGY",
                        severity=InteractionSeverity.CRITICAL,
                        medications=[raw_med, allergy.capitalize()],
                        title=f"Direct Allergy Conflict: {raw_med}",
                        explanation=f"Prescribed medication '{raw_med}' directly matches patient recorded allergy '{allergy.capitalize()}'.",
                        recommended_action="Critical contraindication. Consult physician immediately to select an alternative medication class.",
                    )
                    dai_findings.append(finding)
                    all_findings.append(finding)
                    recommendations.append(
                        f"[CRITICAL ALLERGY ALERT] Direct match between '{raw_med}' and patient allergy '{allergy}'."
                    )

        # -----------------------------------------------------------------
        # Category D: Duplicate Medications & Therapeutic Overlap
        # -----------------------------------------------------------------
        # Check identical active ingredient
        seen_ingredients: Dict[str, str] = {}
        for raw_med, norm_med in normalized_meds:
            if norm_med in seen_ingredients:
                first_raw = seen_ingredients[norm_med]
                finding = SafetyFinding(
                    category="DUPLICATE_MEDICATION",
                    severity=InteractionSeverity.HIGH,
                    medications=[first_raw, raw_med],
                    title=f"Duplicate Active Ingredient: {norm_med.capitalize()}",
                    explanation=f"Both '{first_raw}' and '{raw_med}' resolve to the same active ingredient '{norm_med.capitalize()}', presenting a risk of accidental overdose or supratherapeutic dosing.",
                    recommended_action="Potential therapeutic duplication. Consult the prescribing doctor or pharmacist to confirm dosing and avoid redundant medication.",
                )
                dup_findings.append(finding)
                all_findings.append(finding)
                recommendations.append(
                    f"[DUPLICATION ALERT] Multiple entries for active ingredient '{norm_med.capitalize()}' ({first_raw} and {raw_med})."
                )
            else:
                seen_ingredients[norm_med] = raw_med

        # Check pharmacological class duplication (e.g. dual NSAIDs, dual PPIs)
        for class_name, drug_set in knowledge_base.DRUG_CLASSES.items():
            matched_in_class = [(raw, norm) for raw, norm in normalized_meds if norm in drug_set]
            if len(matched_in_class) > 1:
                # Check if this isn't already reported under duplicate active ingredient
                distinct_norms = {norm for _, norm in matched_in_class}
                if len(distinct_norms) > 1:
                    names_str = " + ".join([r for r, _ in matched_in_class])
                    finding = SafetyFinding(
                        category="DUPLICATE_MEDICATION",
                        severity=InteractionSeverity.MODERATE,
                        medications=[r for r, _ in matched_in_class],
                        title=f"Class Overlap: Dual {class_name}",
                        explanation=f"Prescription includes multiple agents belonging to the same pharmacological class ({class_name}: {names_str}), potentially increasing adverse effect liability without therapeutic benefit.",
                        recommended_action=f"Review dual {class_name} combination with the prescribing clinician to ensure concurrent therapy is intended.",
                    )
                    dup_findings.append(finding)
                    all_findings.append(finding)

        # -----------------------------------------------------------------
        # Determine Overall Risk Level
        # -----------------------------------------------------------------
        overall_risk = InteractionSeverity.NONE
        if any(f.severity == InteractionSeverity.CRITICAL for f in all_findings):
            overall_risk = InteractionSeverity.CRITICAL
        elif any(f.severity == InteractionSeverity.HIGH for f in all_findings):
            overall_risk = InteractionSeverity.HIGH
        elif any(f.severity == InteractionSeverity.MODERATE for f in all_findings):
            overall_risk = InteractionSeverity.MODERATE
        elif any(f.severity == InteractionSeverity.LOW for f in all_findings):
            overall_risk = InteractionSeverity.LOW

        # Formulate clinical summary
        if not all_findings:
            summary = (
                f"No potential interactions or contraindications were identified in the available demonstration knowledge base "
                f"for the {len(normalized_meds)} evaluated medication(s)."
            )
        else:
            summary = (
                f"Prescription safety audit identified {len(all_findings)} potential consideration(s) across {len(normalized_meds)} medication(s): "
                f"{len(ddi_findings)} drug-drug, {len(dfi_findings)} drug-food, {len(dai_findings)} allergy alert(s), and {len(dup_findings)} duplication notice(s). "
                f"Overall risk assessment: {overall_risk.value}."
            )

        return AISafetyReportResponse(
            prescription_id=prescription_id,
            patient_id=patient_id,
            overall_risk_level=overall_risk,
            total_findings=len(all_findings),
            findings=all_findings,
            drug_drug_interactions=ddi_findings,
            drug_food_interactions=dfi_findings,
            drug_allergy_interactions=dai_findings,
            clinical_summary=summary,
            summary=summary,
            ai_recommendations=recommendations,
            disclaimer=DISCLAIMER_TEXT,
        )


interaction_checker = InteractionChecker()
