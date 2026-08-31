"""Modular Clinical Drug Interaction & Contraindication Demonstration Knowledge Base."""
from typing import Dict, List, Optional, Set, Tuple
from app.models.ai_report import InteractionSeverity


class KnowledgeBase:
    """
    Demonstration Knowledge Base containing structured clinical rules for:
    - Drug-Drug Interactions (DDI)
    - Drug-Food & Dietary Interactions (DFI)
    - Drug-Allergy Contraindications (DAI)
    - Therapeutic Duplication & Active Ingredient Overlap

    LIMITATION NOTE:
    This demonstration dataset contains curated clinical rules for prototyping and academic validation.
    In an enterprise production deployment, this layer is designed to be backed or augmented by an
    authorized clinical pharmacology database (e.g., First Databank, RxNorm, DrugBank, or ClinicalTrials API).
    """

    # Drug-Drug Interaction Rules: Set of 2 normalized generic drug names -> Details
    DRUG_DRUG_RULES: List[Dict] = [
        {
            "drugs": {"warfarin", "aspirin"},
            "severity": InteractionSeverity.HIGH,
            "title": "Warfarin + Aspirin (Antiplatelet / Anticoagulant Hemorrhage Hazard)",
            "explanation": "Concurrent administration of Warfarin and Aspirin produces synergistic anticoagulant and antiplatelet inhibition, significantly elevating the risk of major gastrointestinal and systemic bleeding.",
            "recommended_action": "Potential high-risk interaction. Consult the prescribing physician to evaluate clinical indication, adjust dosages, or monitor INR and hemoglobin levels closely.",
        },
        {
            "drugs": {"warfarin", "ibuprofen"},
            "severity": InteractionSeverity.HIGH,
            "title": "Warfarin + Ibuprofen (NSAID-Induced Mucosal Hemorrhage)",
            "explanation": "Ibuprofen inhibits platelet cyclooxygenase and promotes gastric mucosal injury, compounding the anticoagulant effects of Warfarin and greatly increasing gastrointestinal ulceration and bleeding risk.",
            "recommended_action": "Potential high-risk interaction. Consider acetaminophen as an alternative analgesic if clinically appropriate, or consult the prescribing physician.",
        },
        {
            "drugs": {"warfarin", "ciprofloxacin"},
            "severity": InteractionSeverity.HIGH,
            "title": "Warfarin + Ciprofloxacin (CYP1A2/CYP3A4 Inhibition & Coagulopathy)",
            "explanation": "Ciprofloxacin inhibits hepatic CYP enzymes responsible for Warfarin metabolism and alters gut flora synthesis of Vitamin K, leading to sudden prolongation of INR and bleeding vulnerability.",
            "recommended_action": "Potential interaction detected. Frequent INR monitoring is advised. Consult the prescribing doctor regarding dose titration.",
        },
        {
            "drugs": {"simvastatin", "clarithromycin"},
            "severity": InteractionSeverity.HIGH,
            "title": "Simvastatin + Clarithromycin (CYP3A4 Inhibition & Rhabdomyolysis)",
            "explanation": "Clarithromycin is a potent CYP3A4 inhibitor that markedly increases systemic exposure to Simvastatin, dramatically escalating the danger of severe myopathy and rhabdomyolysis.",
            "recommended_action": "Potential high-risk interaction. Avoid concurrent therapy. Temporary suspension of statin therapy or selection of an alternative macrolide/antibiotic is recommended under physician guidance.",
        },
        {
            "drugs": {"atorvastatin", "clarithromycin"},
            "severity": InteractionSeverity.HIGH,
            "title": "Atorvastatin + Clarithromycin (Statin Toxicity & Myopathy Hazard)",
            "explanation": "Clarithromycin substantially increases Atorvastatin plasma concentrations, elevating the risk of severe musculoskeletal toxicity and acute renal injury.",
            "recommended_action": "Potential interaction detected. Consult the healthcare provider to evaluate temporary statin dose capping or alternative antibiotic selection.",
        },
        {
            "drugs": {"lisinopril", "spironolactone"},
            "severity": InteractionSeverity.HIGH,
            "title": "Lisinopril + Spironolactone (Dual Potassium Retention & Hyperkalemia)",
            "explanation": "Combining an ACE inhibitor (Lisinopril) with a potassium-sparing diuretic (Spironolactone) causes synergistic potassium retention, risking life-threatening cardiac arrhythmias.",
            "recommended_action": "Potential interaction detected. Regular serum potassium and renal function monitoring is recommended. Consult the treating practitioner.",
        },
        {
            "drugs": {"fluoxetine", "tramadol"},
            "severity": InteractionSeverity.CRITICAL,
            "title": "Fluoxetine + Tramadol (Serotonin Syndrome & Seizure Hazard)",
            "explanation": "Fluoxetine inhibits Tramadol metabolism via CYP2D6 and adds additive serotonergic stimulation, creating a severe risk of Serotonin Syndrome and lowering the seizure threshold.",
            "recommended_action": "Critical safety alert. Co-administration should generally be avoided. Immediately consult the prescribing doctor for alternative pain management.",
        },
        {
            "drugs": {"sertraline", "tramadol"},
            "severity": InteractionSeverity.CRITICAL,
            "title": "Sertraline + Tramadol (Serotonin Toxicity Alert)",
            "explanation": "Additive serotonergic enhancement can trigger central and peripheral serotonin receptor hyperstimulation resulting in neuromuscular and autonomic instability.",
            "recommended_action": "Critical interaction concern. Consult the prescribing doctor or pharmacist before combining these medications.",
        },
        {
            "drugs": {"digoxin", "amiodarone"},
            "severity": InteractionSeverity.HIGH,
            "title": "Digoxin + Amiodarone (P-gp Efflux Inhibition & Digitalis Toxicity)",
            "explanation": "Amiodarone inhibits P-glycoprotein efflux transport, frequently doubling serum digoxin concentrations and inducing fatal cardiac dysrhythmias and bradycardia.",
            "recommended_action": "Potential high-risk interaction. Digoxin dosage reduction by 30-50% and therapeutic drug monitoring are standard clinical practices. Consult the cardiologist.",
        },
        {
            "drugs": {"methotrexate", "ibuprofen"},
            "severity": InteractionSeverity.HIGH,
            "title": "Methotrexate + Ibuprofen (Reduced Renal Excretion & Bone Marrow Toxicity)",
            "explanation": "NSAIDs decrease renal prostaglandin synthesis and competitive tubular clearance of Methotrexate, leading to elevated serum levels, severe pancytopenia, and nephrotoxicity.",
            "recommended_action": "Potential interaction. Avoid concurrent non-steroidal anti-inflammatory use during methotrexate regimens without specialist supervision.",
        },
        {
            "drugs": {"clopidogrel", "omeprazole"},
            "severity": InteractionSeverity.MODERATE,
            "title": "Clopidogrel + Omeprazole (CYP2C19 Competitive Bioactivation Impairment)",
            "explanation": "Omeprazole competitively inhibits CYP2C19, diminishing conversion of Clopidogrel into its active antiplatelet metabolite and potentially compromising cardiovascular protection.",
            "recommended_action": "Potential interaction. Consider pantoprazole or an H2 blocker as an alternative gastroprotective agent in consultation with the physician.",
        },
        {
            "drugs": {"metformin", "cimetidine"},
            "severity": InteractionSeverity.MODERATE,
            "title": "Metformin + Cimetidine (Organic Cation Transporter Blockade)",
            "explanation": "Cimetidine competes with Metformin for renal tubular secretion, increasing circulating Metformin levels and slightly elevating the risk of lactic acidosis.",
            "recommended_action": "Potential interaction detected. Monitor blood glucose and renal parameters. Consult healthcare provider.",
        },
    ]

    # Drug-Food / Substance Interaction Rules: Normalized drug name -> List of food triggers & details
    DRUG_FOOD_RULES: List[Dict] = [
        {
            "drug": "warfarin",
            "food_triggers": ["vitamin k", "spinach", "kale", "broccoli", "leafy greens", "green tea", "cranberry"],
            "severity": InteractionSeverity.MODERATE,
            "title": "Warfarin + Vitamin K-Rich Diet / Cranberry",
            "explanation": "High dietary intake of Vitamin K directly antagonizes the anticoagulant mechanism of Warfarin, causing fluctuating INR and suboptimal therapeutic anticoagulation.",
            "recommended_action": "Maintain consistent daily dietary Vitamin K intake rather than making abrupt dietary shifts. Discuss dietary habits with the clinical team.",
        },
        {
            "drug": "simvastatin",
            "food_triggers": ["grapefruit", "grapefruit juice", "pomelo"],
            "severity": InteractionSeverity.HIGH,
            "title": "Simvastatin + Grapefruit Juice (Intestinal CYP3A4 Furanocoumarin Inhibition)",
            "explanation": "Furanocoumarins in grapefruit irreversibly inhibit intestinal CYP3A4, dramatically increasing Simvastatin systemic absorption by up to 16-fold and heightening myopathy risk.",
            "recommended_action": "Avoid consumption of grapefruit and grapefruit juice while undergoing treatment with Simvastatin. Consult healthcare provider for alternative fruit options.",
        },
        {
            "drug": "atorvastatin",
            "food_triggers": ["grapefruit", "grapefruit juice"],
            "severity": InteractionSeverity.MODERATE,
            "title": "Atorvastatin + Grapefruit Juice",
            "explanation": "Grapefruit compounds can elevate circulating Atorvastatin concentrations, increasing potential muscle aches and liver enzyme elevations.",
            "recommended_action": "Limit or avoid large quantities of grapefruit juice while taking Atorvastatin.",
        },
        {
            "drug": "metronidazole",
            "food_triggers": ["alcohol", "ethanol", "wine", "beer", "liquor"],
            "severity": InteractionSeverity.HIGH,
            "title": "Metronidazole + Alcohol (Disulfiram-Like Acetaldehyde Toxicity)",
            "explanation": "Metronidazole inhibits aldehyde dehydrogenase, causing toxic acetaldehyde accumulation when consumed with alcohol, triggering severe abdominal cramping, vomiting, flushing, and tachycardia.",
            "recommended_action": "Strictly avoid all alcoholic beverages, mouthwashes containing alcohol, and liquid medications containing ethanol during therapy and for at least 48 hours afterward.",
        },
        {
            "drug": "ciprofloxacin",
            "food_triggers": ["dairy", "milk", "cheese", "yogurt", "calcium-fortified juice"],
            "severity": InteractionSeverity.MODERATE,
            "title": "Ciprofloxacin + Dairy Products / Calcium",
            "explanation": "Multivalent calcium cations in dairy products bind to Ciprofloxacin molecules, creating insoluble chelate complexes that impair gastrointestinal absorption by up to 40%.",
            "recommended_action": "Take Ciprofloxacin at least 2 hours before or 4 hours after consuming milk, yogurt, or calcium-rich meals.",
        },
        {
            "drug": "levothyroxine",
            "food_triggers": ["coffee", "espresso", "soy", "dietary fiber", "calcium supplements"],
            "severity": InteractionSeverity.LOW,
            "title": "Levothyroxine + Coffee / Calcium / High Fiber",
            "explanation": "Coffee, soy protein, and fiber bind to Levothyroxine in the stomach, reducing optimal hormonal absorption and causing thyroid level instability.",
            "recommended_action": "Take Levothyroxine on an empty stomach with a full glass of water at least 30 to 60 minutes before breakfast or morning coffee.",
        },
        {
            "drug": "lisinopril",
            "food_triggers": ["potassium salt substitutes", "high potassium foods"],
            "severity": InteractionSeverity.MODERATE,
            "title": "Lisinopril + Potassium Salt Substitutes",
            "explanation": "ACE inhibitors reduce aldosterone secretion, decreasing potassium excretion. Potassium-based salt substitutes can precipitate rapid hyperkalemia.",
            "recommended_action": "Avoid potassium chloride salt substitutes unless explicitly approved by your treating physician.",
        },
    ]

    # Drug-Allergy Class Cross-Reactivity Mapping
    ALLERGY_CLASS_MAP: Dict[str, Dict] = {
        "penicillin": {
            "cross_reactive_drugs": {
                "penicillin", "amoxicillin", "ampicillin", "amoxicillin-clavulanate",
                "augmentin", "piperacillin", "ticarcillin", "oxacillin", "cloxacillin",
                "nafcillin", "amoxil"
            },
            "severity": InteractionSeverity.CRITICAL,
            "explanation": "The prescribed medication is a member of the Penicillin / Beta-Lactam class, presenting a high probability of severe Type I hypersensitivity (anaphylaxis, angioedema, urticaria).",
            "recommended_action": "Critical safety contraindication. Do not administer or take this medication if confirmed allergic. Immediately consult the prescribing doctor for a non-beta-lactam alternative.",
        },
        "sulfa": {
            "cross_reactive_drugs": {
                "sulfamethoxazole", "bactrim", "septra", "sulfasalazine",
                "dapsone", "sulfadiazine"
            },
            "severity": InteractionSeverity.CRITICAL,
            "explanation": "The prescribed compound contains an arylamine sulfonamide moiety that is contraindicated in patients with known sulfa hypersensitivity.",
            "recommended_action": "Critical contraindication. Consult prescribing healthcare provider immediately for an alternative antimicrobial agent.",
        },
        "aspirin": {
            "cross_reactive_drugs": {
                "aspirin", "ibuprofen", "naproxen", "diclofenac", "ketorolac",
                "indomethacin", "meloxicam", "celecoxib", "advil", "aleve"
            },
            "severity": InteractionSeverity.HIGH,
            "explanation": "Cross-reactivity occurs among non-steroidal anti-inflammatory drugs (NSAIDs) due to shared cyclooxygenase-1 inhibition and leukotriene shifting, which can precipitate bronchospasm or urticaria.",
            "recommended_action": "Potential severe allergic reaction. Verify tolerance or consult healthcare professional regarding non-NSAID analgesics (e.g. acetaminophen).",
        },
        "nsaid": {
            "cross_reactive_drugs": {
                "aspirin", "ibuprofen", "naproxen", "diclofenac", "ketorolac",
                "indomethacin", "meloxicam", "celecoxib", "advil", "aleve"
            },
            "severity": InteractionSeverity.HIGH,
            "explanation": "Patient has documented NSAID intolerance or allergy, conflicting with the prescribed anti-inflammatory agent.",
            "recommended_action": "Potential allergic contraindication. Consult prescribing physician prior to taking.",
        },
    }

    # Pharmacological Drug Classes for Therapeutic Duplication Checking
    DRUG_CLASSES: Dict[str, Set[str]] = {
        "NSAID": {"ibuprofen", "naproxen", "diclofenac", "ketorolac", "indomethacin", "meloxicam", "celecoxib", "aspirin"},
        "Proton Pump Inhibitor (PPI)": {"omeprazole", "esomeprazole", "lansoprazole", "pantoprazole", "rabeprazole"},
        "ACE Inhibitor": {"lisinopril", "enalapril", "ramipril", "captopril", "benazepril"},
        "Angiotensin II Receptor Blocker (ARB)": {"losartan", "valsartan", "candesartan", "irbesartan", "telmisartan"},
        "Statin (HMG-CoA Reductase Inhibitor)": {"atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin"},
        "Benzodiazepine": {"alprazolam", "diazepam", "lorazepam", "clonazepam", "temazepam"},
        "SSRI Antidepressant": {"fluoxetine", "sertraline", "escitalopram", "citalopram", "paroxetine"},
        "Fluoroquinolone Antibiotic": {"ciprofloxacin", "levofloxacin", "moxifloxacin", "ofloxacin"},
    }


knowledge_base = KnowledgeBase()
