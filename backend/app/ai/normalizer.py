"""Medication name normalization and brand-to-generic alias mapping."""
import re
from typing import Dict, List, Set

# Comprehensive brand-name and trade-name to generic active ingredient dictionary
BRAND_TO_GENERIC_MAP: Dict[str, str] = {
    # NSAIDs & Analgesics
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "brufen": "ibuprofen",
    "nurofen": "ibuprofen",
    "aleve": "naproxen",
    "naprosyn": "naproxen",
    "tylenol": "paracetamol",
    "panadol": "paracetamol",
    "calpol": "paracetamol",
    "crocin": "paracetamol",
    "acetaminophen": "paracetamol",
    "aspirin": "aspirin",
    "bayer": "aspirin",
    "ecotrin": "aspirin",
    "disprin": "aspirin",
    "voltaren": "diclofenac",
    "cataflam": "diclofenac",
    "celebrex": "celecoxib",

    # Anticoagulants & Antiplatelets
    "coumadin": "warfarin",
    "jantoven": "warfarin",
    "marevan": "warfarin",
    "plavix": "clopidogrel",
    "eliquis": "apixaban",
    "xarelto": "rivaroxaban",
    "pradaxa": "dabigatran",
    "brilinta": "ticagrelor",
    "heparin": "heparin",
    "lovenox": "enoxaparin",

    # Antibiotics & Antifungals & Antiprotozoals
    "amoxil": "amoxicillin",
    "augmentin": "amoxicillin-clavulanate",
    "ampicillin": "ampicillin",
    "penicillin": "penicillin",
    "penicillin v": "penicillin",
    "penicillin vk": "penicillin",
    "cipro": "ciprofloxacin",
    "cipro xr": "ciprofloxacin",
    "levoquin": "levofloxacin",
    "avelox": "moxifloxacin",
    "zithromax": "azithromycin",
    "z-pak": "azithromycin",
    "biaxin": "clarithromycin",
    "erythrocin": "erythromycin",
    "keflex": "cephalexin",
    "rocephin": "ceftriaxone",
    "flagyl": "metronidazole",
    "diflucan": "fluconazole",
    "sporanox": "itraconazole",
    "bactrim": "sulfamethoxazole",
    "septra": "sulfamethoxazole",

    # Statins & Lipid Lowering
    "lipitor": "atorvastatin",
    "zocor": "simvastatin",
    "crestor": "rosuvastatin",
    "pravachol": "pravastatin",
    "tricor": "fenofibrate",

    # Cardiovascular & Blood Pressure
    "zestril": "lisinopril",
    "prinivil": "lisinopril",
    "vasotec": "enalapril",
    "altace": "ramipril",
    "cozaar": "losartan",
    "diovan": "valsartan",
    "norvasc": "amlodipine",
    "cardizem": "diltiazem",
    "calan": "verapamil",
    "lopressor": "metoprolol",
    "toprol": "metoprolol",
    "tenormin": "atenolol",
    "coreg": "carvedilol",
    "lasix": "furosemide",
    "aldactone": "spironolactone",
    "lanoxin": "digoxin",
    "cordarone": "amiodarone",
    "pacerone": "amiodarone",

    # Gastrointestinal
    "prilosec": "omeprazole",
    "nexium": "esomeprazole",
    "prevacid": "lansoprazole",
    "protonix": "pantoprazole",
    "pepcid": "famotidine",

    # Endocrine & Diabetes
    "glucophage": "metformin",
    "fortamet": "metformin",
    "amaryl": "glimepiride",
    "glucotrol": "glipizide",
    "januvia": "sitagliptin",
    "synthroid": "levothyroxine",

    # Neuropsychiatric
    "prozac": "fluoxetine",
    "zoloft": "sertraline",
    "lexapro": "escitalopram",
    "celexa": "citalopram",
    "paxil": "paroxetine",
    "xanax": "alprazolam",
    "valium": "diazepam",
    "ativan": "lorazepam",
    "klonopin": "clonazepam",
    "lithobid": "lithium",
    "tegretol": "carbamazepine",
    "depakote": "valproate",

    # Respiratory & Allergy
    "zyrtec": "cetirizine",
    "claritin": "loratadine",
    "allegra": "fexofenadine",
    "singulair": "montelukast",
    "ventolin": "albuterol",
    "proair": "albuterol",
}

# Regex to strip dosage strengths (e.g. 500mg, 10 mg/ml, 2.5mcg, 100iu)
DOSAGE_PATTERN = re.compile(
    r"\b\d+(\.\d+)?\s*(mg|g|mcg|ug|ml|l|iu|units|meq|%|tablets?|capsules?|drops?|puff|puffs)\b",
    re.IGNORECASE,
)

# Common formulation descriptors to remove
FORMULATION_WORDS = {
    "tablet", "tablets", "tab", "tabs", "capsule", "capsules", "cap", "caps",
    "syrup", "suspension", "solution", "injection", "inj", "infusion", "cream",
    "ointment", "gel", "lotion", "patch", "inhaler", "spray", "oral", "iv", "im",
    "hcl", "hydrochloride", "sodium", "potassium", "calcium", "sulfate", "succinate",
    "tartrate", "maleate", "monohydrate", "dihydrate", "extended", "release", "er",
    "xr", "sr", "cr", "xl", "dr", "ir", "forte", "plus", "extra", "strength",
}


def normalize_medication_name(raw_name: str) -> str:
    """
    Normalize clinical medication strings into canonical generic active ingredient names:
    1. Lowercase and trim.
    2. Strip numerical dosages and units (e.g. '500 mg', '10ml').
    3. Remove formulation suffixes (e.g. 'HCL', 'Tablet', 'XR').
    4. Strip non-alphanumeric punctuation.
    5. Resolve brand/trade names to generic active ingredients using dictionary lookup.
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    text = raw_name.lower().strip()

    # Remove dosage patterns
    text = DOSAGE_PATTERN.sub(" ", text)

    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s-]", " ", text)
    tokens = text.replace("-", " ").split()

    # Filter out formulation stop words
    filtered_tokens = [t for t in tokens if t not in FORMULATION_WORDS and not t.isdigit()]
    cleaned_name = " ".join(filtered_tokens).strip()

    if not cleaned_name:
        # Fallback to original stripped lower if all tokens were filtered
        cleaned_name = re.sub(r"[^\w\s]", "", raw_name.lower()).strip()

    # Direct match in brand map
    if cleaned_name in BRAND_TO_GENERIC_MAP:
        return BRAND_TO_GENERIC_MAP[cleaned_name]

    # Check individual token matches for compound brand names
    for token in cleaned_name.split():
        if token in BRAND_TO_GENERIC_MAP:
            return BRAND_TO_GENERIC_MAP[token]

    return cleaned_name
