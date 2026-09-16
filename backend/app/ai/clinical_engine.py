"""CareAI Clinical Intelligence Engine — Comprehensive, role-aware clinical reasoning and medical knowledge system.

Provides deep, medically grounded, non-repetitive clinical answers across 5 healthcare roles:
PATIENT, DOCTOR, LAB_TECHNICIAN, PHARMACY_STAFF, and ADMIN.
Acts as the high-fidelity deterministic engine when external foundation LLMs (Gemini/OpenAI)
are unconfigured, offline, or experiencing quota/connectivity constraints.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.user import UserRole


# ==============================================================================
# 1. CLINICAL KNOWLEDGE REPOSITORY
# ==============================================================================

CONDITIONS_DB: Dict[str, Dict[str, Any]] = {
    "fever": {
        "name": "Fever (Pyrexia)",
        "category": "General Symptom / Infectious",
        "description": "Elevation of body core temperature above normal circadian range (> 38.0°C / 100.4°F), typically mediated by pyrogen-induced prostaglandin E2 synthesis in the hypothalamus.",
        "common_causes": ["Viral upper respiratory infections", "Bacterial infections (UTI, tonsillitis, pneumonia)", "Gastroenteritis", "Vector-borne diseases (Dengue, Malaria, Typhoid)", "Post-vaccination immune response"],
        "red_flags": ["Temperature > 40.0°C (104°F) or persistent > 3 days", "Stiff neck, photophobia, confusion (meningism)", "Shortness of breath or chest pain", "Petechial or purpuric skin rash", "Persistent vomiting, severe dehydration, or oliguria"],
        "patient_guidance": "Rest adequately, drink plenty of oral rehydration fluids, soups, and water. Use light clothing and maintain room ventilation. An OTC antipyretic like Paracetamol (500-650 mg every 4-6h, max 3000 mg/day in adults) can help reduce discomfort. Avoid Aspirin in children and adolescents due to Reye's syndrome risk.",
        "doctor_guidance": "Classify as acute (< 7 days), subacute, or fever of unknown origin (FUO). Assess hemodynamic stability, hydration, and focalizing symptoms. Initial workup: CBC with differential, Urinalysis, CRP/ESR. In endemic regions, consider Dengue NS1/IgM, Peripheral smear/RDT for Malaria, and Blood cultures before starting empiric antimicrobials.",
        "lab_guidance": "Recommended initial tests: CBC with differential (look for leukocytosis with left shift in bacterial infections, leukopenia/thrombocytopenia in Dengue/viral fevers), CRP, ESR, and Urinalysis. Draw blood cultures prior to initiation of antibiotic therapy.",
        "pharmacy_guidance": "First-line antipyretic: Paracetamol 500-1000 mg PO q4-6h PRN (max 3-4 g/day depending on hepatic status). Second-line: Ibuprofen 200-400 mg PO q6-8h with meals. Cautious use of NSAIDs if dengue is suspected due to thrombocytopenia and bleeding hazards.",
    },
    "headache": {
        "name": "Headache (Cephalea)",
        "category": "Neurological",
        "description": "Pain in any region of the head, classified into primary headaches (tension, migraine, cluster) and secondary headaches caused by underlying vascular, infectious, or intracranial pathology.",
        "common_causes": ["Tension headache (stress, muscle contraction)", "Migraine with or without aura", "Cervicogenic or eye strain", "Sinusitis", "Dehydration, sleep deprivation, caffeine withdrawal"],
        "red_flags": ["'Thunderclap' sudden severe headache reaching peak in seconds (suggestive of subarachnoid hemorrhage)", "New headache with focal neurological deficits, confusion, or seizures", "Headache with fever and neck stiffness", "New onset headache in individuals over 50 or immunocompromised", "Headache worsened by Valsalva, coughing, or postural change"],
        "patient_guidance": "Rest in a quiet, dark, well-ventilated room. Maintain optimal hydration and apply a cool compress to the forehead or neck. Identify potential triggers like skipped meals, screen fatigue, or lack of sleep. Simple analgesics like Paracetamol or Ibuprofen may be taken early in the episode.",
        "doctor_guidance": "Perform comprehensive neurological examination including cranial nerves, fundoscopy (papilledema), and meningeal signs. Utilize SNOOP4 mnemonic to screen for secondary causes. For primary migraines: consider triptans (e.g., Sumatriptan 50-100 mg) for abortive therapy, and beta-blockers, Topiramate, or CGRP antagonists for preventive management.",
        "lab_guidance": "Primary headaches do not exhibit specific biomarker alterations. For secondary workup: ESR/CRP for suspected Giant Cell (Temporal) Arteritis in elderly patients; Lumbar Puncture CSF analysis (opening pressure, cell count, protein, glucose, xanthochromia) if subarachnoid hemorrhage or meningitis is suspected.",
        "pharmacy_guidance": "Mild-moderate: Paracetamol 1000 mg or Ibuprofen 400 mg with or without Caffeine. Migraine-specific: Sumatriptan 50-100 mg PO at onset (contraindicated in ischemic heart disease, uncontrolled hypertension, and peripheral vascular disease). Monitor for Medication Overuse Headache (MOH) if analgesics are used > 10-15 days per month.",
    },
    "migraine": {
        "name": "Migraine",
        "category": "Neurological",
        "description": "Recurrent neurovascular headache disorder characterized by unilateral, throbbing moderate-to-severe headache lasting 4-72 hours, aggravated by routine physical activity and accompanied by nausea, photophobia, and phonophobia.",
        "common_causes": ["Cortical spreading depression and trigeminovascular activation", "Hormonal fluctuations (estrogen withdrawal)", "Dietary triggers (aged cheese, red wine, chocolate, MSG, artificial sweeteners)", "Stress, irregular sleep, bright lights, sensory overload"],
        "red_flags": ["Aura lasting > 60 minutes or motor weakness (hemiplegic migraine)", "Sudden explosive onset ('thunderclap')", "First migraine occurring after age 50", "Progressive worsening over weeks with neurological signs"],
        "patient_guidance": "At the first sign of aura or headache, retreat to a dark, quiet room and rest. Keep a headache diary to track food, sleep, and environmental triggers. Stay well hydrated and maintain consistent meal and sleep schedules.",
        "doctor_guidance": "Confirm ICHD-3 criteria (at least 5 attacks fulfilling features). Assess disability using MIDAS or HIT-6 score. Acute treatment: NSAIDs (Naproxen 500 mg, Ibuprofen 400-600 mg), Triptans (Sumatriptan, Rizatriptan), or antiemetics (Metoclopramide 10 mg). Prophylaxis indicated if attacks occur >= 4 days/month: Propranolol, Amitriptyline, Topiramate, or CGRP monoclonal antibodies.",
        "lab_guidance": "Migraine is a clinical diagnosis; routine lab tests are normal. Rule out metabolic triggers: basic metabolic panel, thyroid function (TSH). If atypical aura, MRI/MRA brain is the preferred neuroimaging modality.",
        "pharmacy_guidance": "Counsel on early administration during attack onset. Contraindications for triptans: coronary artery disease, history of stroke/TIA, uncontrolled hypertension. Avoid combining triptans with ergotamine within 24 hours. Watch for serotonin syndrome when combining triptans with SSRIs/SNRIs.",
    },
    "hypertension": {
        "name": "Hypertension (High Blood Pressure)",
        "category": "Cardiovascular",
        "description": "Persistent elevation of systemic arterial blood pressure (Systolic BP >= 130 mmHg and/or Diastolic BP >= 80 mmHg per ACC/AHA guidelines, or >= 140/90 mmHg per ESC guidelines).",
        "common_causes": ["Primary (essential) hypertension (90-95%): genetic predisposition, high sodium intake, obesity, physical inactivity", "Secondary (5-10%): renal artery stenosis, chronic kidney disease, primary hyperaldosteronism, obstructive sleep apnea, pheochromocytoma, Cushing's syndrome"],
        "red_flags": ["Hypertensive emergency: BP > 180/120 mmHg accompanied by acute target-organ damage (chest pain, shortness of breath, severe headache, visual disturbance, altered mental status, pulmonary edema)", "Rapidly progressive neurological deficits or seizures"],
        "patient_guidance": "Adopt the DASH (Dietary Approaches to Stop Hypertension) diet rich in fruits, vegetables, and low-fat dairy. Limit sodium intake to < 2,000 mg/day (less than 1 teaspoon of table salt). Engage in 150 minutes/week of moderate aerobic exercise. Avoid smoking, limit alcohol, and take your prescribed antihypertensives daily without skipping doses.",
        "doctor_guidance": "Stage 1 (130-139 / 80-89 mmHg): Lifestyle modification for 3-6 months if 10-year ASCVD risk < 10%; initiate single agent if ASCVD >= 10%. Stage 2 (>= 140/90 mmHg): Lifestyle + 2 first-line agents of different classes (ACEi/ARB + CCB or Thiazide). Baseline workup: Fasting lipid panel, basic metabolic panel (serum creatinine, eGFR, potassium), Urinalysis (microalbuminuria), and 12-lead ECG.",
        "lab_guidance": "Baseline testing: Serum Creatinine, eGFR, BUN, Electrolytes (Sodium, Potassium - crucial before starting ACEi/ARB/diuretics), Fasting Blood Glucose, Lipid Profile, and Urine Albumin-to-Creatinine Ratio (UACR).",
        "pharmacy_guidance": "First-line drug classes: ACE Inhibitors (Lisinopril, Enalapril), ARBs (Losartan, Telmisartan), Dihydropyridine CCBs (Amlodipine), Thiazide diuretics (Chlorthalidone, Hydrochlorothiazide). Avoid ACEi + ARB combination (risk of hyperkalemia and renal failure). Monitor for ACEi dry cough and CCB peripheral edema.",
    },
    "diabetes": {
        "name": "Diabetes Mellitus (Type 2 & Type 1)",
        "category": "Endocrine & Metabolic",
        "description": "Metabolic disorder characterized by persistent hyperglycemia resulting from defects in insulin secretion, insulin action, or both, leading to long-term microvascular and macrovascular complications.",
        "common_causes": ["Type 2: Peripheral insulin resistance combined with progressive pancreatic beta-cell secretory dysfunction, strongly linked to excess adiposity and genetics", "Type 1: Autoimmune destruction of pancreatic beta cells causing absolute insulin deficiency"],
        "red_flags": ["Diabetic Ketoacidosis (DKA): nausea, vomiting, Kussmaul deep breathing, fruity breath, abdominal pain, blood glucose > 250 mg/dL with ketones", "Hyperosmolar Hyperglycemic State (HHS): severe dehydration, confusion, blood glucose > 600 mg/dL", "Severe Hypoglycemia: blood glucose < 54 mg/dL with confusion, diaphoresis, tremors, loss of consciousness"],
        "patient_guidance": "Monitor blood glucose regularly. Focus on a balanced diet rich in soluble fiber, complex carbohydrates, lean protein, and healthy fats while minimizing refined sugars and sweetened beverages. Strive for 30 minutes of physical activity 5 days a week. Carry rapid-acting carbohydrates (glucose tablets or candy) for hypoglycemia. Schedule annual foot and dilated eye examinations.",
        "doctor_guidance": "Diagnostic criteria: Fasting plasma glucose >= 126 mg/dL (7.0 mmol/L), or HbA1c >= 6.5% (48 mmol/mol), or 2-hour 75g OGTT >= 200 mg/dL, or random glucose >= 200 mg/dL with symptoms. First-line pharmacotherapy: Metformin + comprehensive lifestyle modification. If established ASCVD, HF, or CKD: add SGLT2 inhibitor or GLP-1 receptor agonist with proven cardiovascular/renal benefit. Target HbA1c < 7.0% for most non-pregnant adults.",
        "lab_guidance": "Diagnostic & monitoring tests: Fasting Blood Glucose, Glycated Hemoglobin (HbA1c, measured every 3 months until stable, then semi-annually), Lipid Profile, Comprehensive Metabolic Panel (eGFR, BUN, Creatinine), and Annual Urine Albumin-to-Creatinine Ratio (UACR).",
        "pharmacy_guidance": "Metformin: start at 500 mg daily with dinner to minimize GI side effects; titrate up to 2000 mg/day; contraindication: eGFR < 30 mL/min/1.73m² (lactic acidosis risk). SGLT2 inhibitors (Empagliflozin, Dapagliflozin): monitor for mycotic genital infections, euglycemic DKA. Sulfonylureas (Glimepiride): high hypoglycemia risk. Always counsel on hypoglycemia rule of 15 (15g fast carbs, recheck in 15 min).",
    },
    "asthma": {
        "name": "Bronchial Asthma",
        "category": "Respiratory",
        "description": "Chronic inflammatory airway disease characterized by bronchial hyperresponsiveness, reversible airflow obstruction, mucosal edema, and variable respiratory symptoms like wheezing, shortness of breath, chest tightness, and cough.",
        "common_causes": ["Aeroallergens (pollen, dust mites, pet dander, mold)", "Respiratory viral infections (Rhinovirus, RSV)", "Exercise, cold air, smoke, air pollution", "Medications (NSAIDs, Aspirin, non-selective beta-blockers)"],
        "red_flags": ["Inability to speak in full sentences or breathlessness at rest", "Accessory muscle use, silent chest on auscultation", "Peak Expiratory Flow (PEF) < 50% of personal best", "Cyanosis (bluish lips/fingernails), altered sensorium, drowsiness", "Poor response to repeated rescue bronchodilators"],
        "patient_guidance": "Always carry your prescribed rescue inhaler (such as Albuterol or ICS-Formoterol). Learn and use correct inhaler technique (use a spacer if using a pressurized MDI). Identify and avoid your personal triggers. Follow your written Asthma Action Plan (Green = Well controlled, Yellow = Caution/increase therapy, Red = Medical alert).",
        "doctor_guidance": "Evaluate using GINA guidelines. Confirm diagnosis with spirometry: FEV1/FVC < 0.70 with significant bronchodilator reversibility (increase in FEV1 > 12% and > 200 mL). GINA Track 1 (preferred): as-needed low-dose ICS-Formoterol across all severity steps. Track 2: SABA reliever + daily maintenance ICS. Step up/down therapy based on symptom control over 2-3 months.",
        "lab_guidance": "Diagnostic testing: Spirometry with pre- and post-bronchodilator assessment. Fractional exhaled nitric oxide (FeNO) to assess eosinophilic airway inflammation. CBC with differential to detect peripheral blood eosinophilia (> 300 cells/uL). Allergy skin testing or specific serum IgE panel.",
        "pharmacy_guidance": "Verify inhaler technique at every dispensary visit (common errors: failure to exhale before inhalation, lack of breath-hold for 5-10 seconds, rapid inhalation for dry powder inhalers). Advise patients to rinse mouth with water and spit after inhaling corticosteroids to prevent oral candidiasis (thrush) and dysphonia.",
    },
    "dengue": {
        "name": "Dengue Fever",
        "category": "Infectious & Vector-Borne",
        "description": "Arboviral infection caused by the Dengue virus (flavivirus, serotypes 1-4) transmitted by female Aedes mosquitoes (Aedes aegypti and Aedes albopictus).",
        "common_causes": ["Bite of infected Aedes aegypti mosquito breeding in clean stagnant water containers."],
        "red_flags": ["Severe abdominal pain or persistent tenderness", "Persistent vomiting (> 3 episodes/day) or inability to retain fluids", "Mucosal bleeding (epistaxis, gum bleeding, hematemesis, melena)", "Lethargy, restlessness, confusion", "Clinical fluid accumulation (ascites, pleural effusion)", "Rapid drop in platelet count accompanied by rising hematocrit (> 20% increase)"],
        "patient_guidance": "Hydration is the single most critical treatment. Drink oral rehydration solutions (ORS), coconut water, fresh fruit juices, and clean water continuously. Use Paracetamol for fever and body pain. NEVER take Ibuprofen, Aspirin, Naproxen, or other NSAIDs because they thin the blood and significantly increase the risk of severe internal bleeding. Get daily blood counts (CBC) checked as advised by your doctor.",
        "doctor_guidance": "Monitor the three phases: Febrile (days 1-3), Critical (days 3-7, time of plasma leakage and defervescence), and Convalescent (days 7-10). Serial CBC monitoring: watch for rising Hematocrit (indicates plasma leakage / hemoconcentration) and falling Platelets. Fluid management: judicious isotonic crystalloids (Ringer's lactate or 0.9% Normal Saline) titrated strictly to maintain urine output > 0.5 mL/kg/h.",
        "lab_guidance": "Diagnostic algorithm: Days 1-5: Dengue NS1 Antigen ELISA + RT-PCR. Days 5+: Dengue IgM and IgG ELISA antibodies. Daily CBC monitoring is mandatory: track Hematocrit/PCV, Platelet count, and WBC (leukopenia usually precedes thrombocytopenia).",
        "pharmacy_guidance": "Strictly contraindicate all NSAIDs (Ibuprofen, Diclofenac, Naproxen) and antiplatelets (Aspirin). Dispense only Paracetamol (max 3 g/day in adults). Emphasize oral rehydration salts (ORS). No antibiotic is effective or indicated for Dengue as it is a viral infection.",
    },
    "malaria": {
        "name": "Malaria",
        "category": "Infectious & Vector-Borne",
        "description": "Life-threatening protozoan infection caused by Plasmodium parasites (P. falciparum, P. vivax, P. malariae, P. ovale, P. knowlesi) transmitted by the female Anopheles mosquito.",
        "common_causes": ["Bite of infected female Anopheles mosquito.", "Blood transfusion or contaminated needles (rare)."],
        "red_flags": ["Cerebral malaria: altered consciousness, coma, repeated seizures", "Severe anemia (Hemoglobin < 7 g/dL in adults, < 5 g/dL in children)", "Acute kidney injury (oliguria, elevated creatinine)", "Pulmonary edema or acute respiratory distress syndrome (ARDS)", "Spontaneous bleeding or coagulopathy, severe jaundice", "Hyperparasitemia (> 2-5% infected erythrocytes)"],
        "patient_guidance": "Malaria requires prompt medical testing and prescription antimalarial treatment. Do not attempt to self-treat. Complete the entire multi-day medication course even if you start feeling completely better. Use mosquito bed nets, insect repellent, and eliminate stagnant water around your home.",
        "doctor_guidance": "Identify Plasmodium species and quantify parasitemia. Uncomplicated P. falciparum: Artemisinin-based Combination Therapy (ACT), e.g., Artemether-Lumefantrine or Artesunate-Amodiaquine for 3 days. Uncomplicated P. vivax: Chloroquine or ACT + Primaquine (14 days for hypnozoite eradication, after G6PD testing to prevent acute hemolytic anemia). Severe malaria: IV Artesunate for at least 24h until oral therapy can be tolerated.",
        "lab_guidance": "Gold standard: Giemsa-stained thick and thin peripheral blood smears. Thick smear: high sensitivity for detecting low parasitemia; Thin smear: species identification and percentage parasitemia quantification. Rapid Diagnostic Tests (RDTs) detecting HRP-2 (P. falciparum) and pan-malarial pLDH. Screen for G6PD deficiency prior to Primaquine administration.",
        "pharmacy_guidance": "Artemether-Lumefantrine (Coartem): take with fatty meals or milk to ensure adequate gastrointestinal absorption of lumefantrine. Complete the full 6-dose regimen over 3 days. Primaquine / Tafenoquine: mandatory G6PD testing prior to dispensing to prevent severe drug-induced hemolytic anemia.",
    },
    "gerd": {
        "name": "Gastroesophageal Reflux Disease (GERD)",
        "category": "Gastrointestinal",
        "description": "Chronic digestive disease where gastric acid and stomach contents flow backward into the esophagus, irritating the mucosal lining and causing troublesome symptoms or mucosal damage.",
        "common_causes": ["Transient lower esophageal sphincter (LES) relaxations or low LES basal tone", "Hiatal hernia", "Obesity and increased intra-abdominal pressure", "Trigger foods: fatty/fried foods, caffeine, chocolate, citrus, mint, tomatoes, alcohol, tobacco", "Delayed gastric emptying"],
        "red_flags": ["Dysphagia (difficulty swallowing) or odynophagia (painful swallowing)", "Unintentional weight loss", "Persistent vomiting, hematemesis (vomiting blood), or melena (black tarry stools)", "Onset of symptoms after age 55", "Unexplained iron-deficiency anemia"],
        "patient_guidance": "Eat smaller, more frequent meals. Avoid lying down for at least 2 to 3 hours after eating. Elevate the head of your bed by 6-8 inches (using bed risers, not extra pillows). Limit citrus fruits, tomatoes, caffeine, chocolate, and carbonated drinks. Avoid tight clothing around the abdomen. If overweight, gradual weight reduction significantly reduces reflux.",
        "doctor_guidance": "Empiric trial with once-daily Proton Pump Inhibitor (PPI) taken 30-60 minutes before breakfast for 4-8 weeks. If alarm symptoms present or no response to trial: refer for Esophagogastroduodenoscopy (EGD) to assess for erosive esophagitis, peptic stricture, or Barrett's esophagus. Consider 24-hour ambulatory pH/impedance monitoring if diagnosis is equivocal.",
        "lab_guidance": "Uncomplicated GERD does not show specific blood abnormalities. CBC with peripheral smear to evaluate for iron-deficiency anemia from occult mucosal bleeding. Fecal occult blood test (FOBT) or H. pylori stool antigen/urea breath test if dyspepsia is also present.",
        "pharmacy_guidance": "PPIs (Omeprazole 20-40 mg, Pantoprazole 40 mg, Esomeprazole 40 mg): must be taken 30-60 minutes before the first meal of the day. Long-term PPI counseling: monitor for hypomagnesemia, vitamin B12 deficiency, bone fractures, and Clostridioides difficile infection. H2 receptor antagonists (Famotidine 20 mg) can be used for intermittent or nocturnal symptoms.",
    },
    "uti": {
        "name": "Urinary Tract Infection (UTI)",
        "category": "Infectious & Renal",
        "description": "Infection of any part of the urinary system (kidneys, ureters, bladder, and urethra), most commonly acute uncomplicated cystitis in women caused by uropathogenic Escherichia coli.",
        "common_causes": ["Escherichia coli (75-95% of uncomplicated UTIs)", "Klebsiella pneumoniae, Proteus mirabilis, Enterococcus faecalis", "Staphylococcus saprophyticus in young sexually active females", "Catheterization, urinary tract obstruction, urinary retention"],
        "red_flags": ["Pyelonephritis: flank/back pain, high fever, rigors, costovertebral angle tenderness", "Inability to tolerate oral fluids or persistent nausea/vomiting", "Sepsis: tachycardia, hypotension, confusion, tachypnea", "Gross hematuria with hemodynamic instability", "UTI in male, pregnant woman, or immunocompromised patient (classified as complicated UTI)"],
        "patient_guidance": "Drink plenty of water (2-3 liters daily) to help flush bacteria out of the urinary tract. Urinate frequently and do not hold urine. Wipe from front to back after using the toilet. Urinate shortly after sexual intercourse. Complete the full prescribed course of antibiotics even if your pain and burning improve quickly.",
        "doctor_guidance": "Distinguish between lower UTI (cystitis) and upper UTI (pyelonephritis). Uncomplicated cystitis in women: Nitrofurantoin monohydrate/macrocrystals 100 mg BID for 5 days, or Fosfomycin trometamol 3g single dose, or Trimethoprim-Sulfamethoxazole 160/800 mg BID for 3 days (if local E. coli resistance < 20%). In men, pregnant women, or recurrent cases: obtain urine culture and treat as complicated.",
        "lab_guidance": "Diagnostic testing: Urinalysis (dipstick: leukocyte esterase and nitrites; microscopic: pyuria > 10 WBC/hpf, bacteriuria, microscopic hematuria). Urine Culture and Sensitivity (Clean-catch midstream urine): significant bacteriuria is >= 10^5 CFU/mL for pure growth (or >= 10^3 CFU/mL in symptomatic females).",
        "pharmacy_guidance": "Nitrofurantoin: take with meals to enhance absorption and minimize nausea; contraindication: eGFR < 30 mL/min (insufficient urinary concentration). Trimethoprim-Sulfamethoxazole: ensure adequate hydration to prevent crystalluria; check for sulfa allergy. Phenazopyridine (urinary analgesic): inform patients it turns urine and tears bright orange-red.",
    },
    "covid": {
        "name": "COVID-19 (SARS-CoV-2)",
        "category": "Infectious Respiratory",
        "description": "Infectious respiratory illness caused by severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2), ranging from asymptomatic or mild upper respiratory symptoms to severe viral pneumonia and multi-organ failure.",
        "common_causes": ["Transmission via inhalation of respiratory droplets and aerosols from infected individuals."],
        "red_flags": ["Shortness of breath or difficulty breathing (SpO2 < 94% on room air)", "Persistent pain, pressure, or tightness in the chest", "New confusion, inability to wake or stay awake", "Pale, gray, or blue-colored skin, lips, or nail beds (cyanosis)"],
        "patient_guidance": "Isolate in a well-ventilated room to prevent transmission to family members. Wear a high-filtration mask (N95/KN95) when around others. Monitor oxygen saturation using a pulse oximeter twice daily. Stay hydrated with broths and electrolytes. Rest and take Paracetamol for fever and aches.",
        "doctor_guidance": "Stratify risk based on age, vaccination status, and comorbidities (diabetes, obesity, cardiovascular disease). For high-risk mild-moderate COVID-19 within 5-7 days of symptom onset: consider oral antivirals (Nirmatrelvir/Ritonavir [Paxlovid] or Remdesivir). For hospitalized patients requiring supplemental oxygen: Dexamethasone 6 mg daily for up to 10 days + Remdesivir.",
        "lab_guidance": "Diagnostic tests: Rapid Antigen Test (RAT) or RT-PCR nasopharyngeal swab. In moderate-to-severe disease: CBC (lymphopenia is common), D-Dimer, Ferritin, C-Reactive Protein (CRP), and comprehensive metabolic panel to monitor organ function and cytokine response.",
        "pharmacy_guidance": "Paxlovid (Nirmatrelvir + Ritonavir): extensive drug-drug interactions due to potent CYP3A inhibition (interacts with statins, anticoagulants, antiarrhythmics, anticonvulsants, PDE-5 inhibitors). Adjust Nirmatrelvir dose in moderate renal impairment (eGFR 30-59 mL/min); contraindicated if eGFR < 30 mL/min.",
    },
    "cholesterol": {
        "name": "Hyperlipidemia & Dyslipidemia (High Cholesterol)",
        "category": "Cardiovascular & Metabolic",
        "description": "Abnormally elevated levels of lipids (fats) or lipoproteins in the bloodstream, particularly elevated low-density lipoprotein cholesterol (LDL-C) and triglycerides, accelerating atherosclerotic cardiovascular disease (ASCVD).",
        "common_causes": ["High dietary intake of saturated and trans fats", "Sedentary lifestyle and obesity", "Genetic conditions (Familial Hypercholesterolemia)", "Secondary causes: uncontrolled diabetes, hypothyroidism, nephrotic syndrome, cholestatic liver disease, excessive alcohol"],
        "red_flags": ["Chest tightness or angina on exertion", "Sudden unilateral numbness, facial drooping, or speech difficulty (stroke warning)", "Xanthomas (fat deposits under skin or around eyes / xanthelasma) in young patients (suggests familial hypercholesterolemia)"],
        "patient_guidance": "Follow a heart-healthy diet (Mediterranean diet): replace saturated animal fats with monounsaturated and polyunsaturated fats (olive oil, nuts, seeds, avocados). Increase soluble fiber intake (oats, legumes, fruits). Limit red meat, processed meats, full-fat dairy, and fried foods. Exercise for 150 minutes per week. Maintain consistent medication compliance with statins.",
        "doctor_guidance": "Calculate 10-year ASCVD risk using pooled cohort equations. Primary prevention: High-intensity statin (Atorvastatin 40-80 mg, Rosuvastatin 20-40 mg) for patients with LDL >= 190 mg/dL or diabetics aged 40-75 with ASCVD risk >= 7.5%. Secondary prevention (established ASCVD): High-intensity statin targeting LDL-C reduction >= 50% and LDL < 55-70 mg/dL; add Ezetimibe 10 mg or PCSK9 inhibitor if targets are not reached.",
        "lab_guidance": "Fasting Lipid Panel (requires 9-12 hours of fasting): Total Cholesterol (< 200 mg/dL desirable), LDL-C (< 100 mg/dL optimal, < 70 mg/dL in high risk), HDL-C (> 40 mg/dL in men, > 50 mg/dL in women protective), Triglycerides (< 150 mg/dL normal). Baseline ALT/AST prior to statin initiation.",
        "pharmacy_guidance": "Statins: take Atorvastatin and Rosuvastatin at any time of day due to long half-lives; take Simvastatin and Pravastatin in the evening. Avoid large quantities of grapefruit juice with Atorvastatin/Simvastatin (CYP3A4 inhibition). Counsel on reporting unexplained muscle soreness, tenderness, or brown urine (rhabdomyolysis warning).",
    },
};

MEDICATIONS_DB: Dict[str, Dict[str, Any]] = {
    "paracetamol": {
        "name": "Paracetamol (Acetaminophen)",
        "class": "Analgesic and Antipyretic",
        "indication": "Mild to moderate pain (headache, toothache, musculoskeletal pain, osteoarthritis) and fever reduction.",
        "dosage": "Adults: 500 mg to 1000 mg PO every 4 to 6 hours as needed. Maximum daily dose: 4000 mg/day (recommended 3000 mg/day for chronic use; 2000 mg/day in chronic alcoholics or mild hepatic impairment).",
        "timing": "Can be taken with or without food. Takes effect in 30-60 minutes.",
        "interactions": "Warfarin (regular high-dose paracetamol enhances anticoagulant effect, monitor INR), Isoniazid (increased hepatotoxicity risk), Alcohol (depletes glutathione and increases hepatotoxic NAPQI metabolite).",
        "side_effects": "Rare at therapeutic doses. Hepatotoxicity with overdose or pre-existing liver disease. Rare severe cutaneous adverse reactions (Stevens-Johnson syndrome).",
        "contraindications": "Severe active hepatic impairment or severe active liver disease, known hypersensitivity.",
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "class": "Non-Steroidal Anti-Inflammatory Drug (NSAID)",
        "indication": "Inflammatory pain, rheumatoid arthritis, osteoarthritis, dysmenorrhea, dental pain, fever.",
        "dosage": "Adults: 200 mg to 400 mg PO every 4 to 6 hours with food. Maximum OTC dose: 1200 mg/day; maximum prescription dose: 2400-3200 mg/day under medical supervision.",
        "timing": "Must be taken with food, milk, or a full glass of water to reduce gastric irritation.",
        "interactions": "Aspirin (interferes with cardioprotective antiplatelet effect), ACE inhibitors/ARBs (reduces antihypertensive effect and increases acute renal failure risk), Anticoagulants (markedly increases GI bleeding risk), Lithium and Methotrexate (decreases their renal clearance, leading to toxicity).",
        "side_effects": "Dyspepsia, heartburn, abdominal pain, GI ulceration and bleeding, peripheral edema, fluid retention, elevation of blood pressure.",
        "contraindications": "Active peptic ulcer disease, history of GI bleeding, severe heart failure (NYHA Class IV), severe renal failure (eGFR < 30), third trimester of pregnancy, coronary artery bypass graft (CABG) perioperative pain, suspected Dengue.",
    },
    "metformin": {
        "name": "Metformin",
        "class": "Biguanide Antidiabetic",
        "indication": "First-line pharmacotherapy for Type 2 Diabetes Mellitus; also used off-label in Polycystic Ovary Syndrome (PCOS).",
        "dosage": "Immediate-release: start at 500 mg PO once or twice daily with meals; titrate gradually by 500 mg weekly to maximum 2000-2550 mg/day in divided doses. Extended-release (XR): 500-2000 mg once daily with the evening meal.",
        "timing": "Take with or immediately after meals to minimize gastrointestinal disturbances (nausea, diarrhea, abdominal cramping).",
        "interactions": "Iodinated radiocontrast agents (withhold 48h before/after procedure to avoid acute renal failure and lactic acidosis), Alcohol (potentiates lactic acidosis risk), Cimetidine (increases metformin plasma concentration).",
        "side_effects": "Diarrhea, nausea, metallic taste, flatulence, abdominal discomfort. Long-term use associated with Vitamin B12 deficiency. Rare but potentially fatal: Lactic acidosis.",
        "contraindications": "Severe renal impairment (eGFR < 30 mL/min/1.73m²), acute metabolic acidosis, severe hypoxemia, acute heart failure, severe hepatic disease.",
    },
    "lisinopril": {
        "name": "Lisinopril",
        "class": "Angiotensin-Converting Enzyme (ACE) Inhibitor",
        "indication": "Hypertension, Heart Failure with reduced Ejection Fraction (HFrEF), post-myocardial infarction cardioprotection, diabetic nephropathy.",
        "dosage": "Hypertension: start 10 mg PO once daily (5 mg if on diuretics); maintenance 20-40 mg once daily. Heart failure: start 2.5-5 mg once daily, titrate to target 20-40 mg daily.",
        "timing": "Can be taken with or without food, preferably at the same time each day.",
        "interactions": "Potassium supplements and potassium-sparing diuretics (severe hyperkalemia risk), ARBs and Aliskiren (excessive hypotension and renal failure), NSAIDs (blunts antihypertensive effect, accelerates nephrotoxicity), Lithium (increased serum lithium levels).",
        "side_effects": "Persistent dry hacking cough (due to bradykinin accumulation), dizziness, hypotension, hyperkalemia, elevated serum creatinine. Rare emergency: Angioedema (swelling of face, lips, tongue, or airway).",
        "contraindications": "Pregnancy (teratogenic / fetal toxicity in 2nd and 3rd trimesters), history of ACEi-induced or hereditary angioedema, bilateral renal artery stenosis, concurrent use with Sacubitril.",
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "class": "Aminopenicillin Antibiotic",
        "indication": "Bacterial infections including acute otitis media, streptococcal pharyngitis, sinusitis, community-acquired pneumonia, uncomplicated skin infections, and H. pylori eradication regimens.",
        "dosage": "Adults: 500 mg PO every 8 hours or 875 mg PO every 12 hours. Severe infections: 1000 mg every 8 hours. Course typically 5 to 10 days.",
        "timing": "May be taken with or without food. Taking with food helps reduce gastrointestinal upset.",
        "interactions": "Methotrexate (decreases methotrexate clearance), Allopurinol (increases risk of ampicillin/amoxicillin rash), Oral contraceptives (potential minor reduction in efficacy, barrier contraception advised), Oral anticoagulants (may prolong prothrombin time / INR).",
        "side_effects": "Diarrhea, nausea, vomiting, skin rash, pruritus. Severe: Clostridioides difficile-associated diarrhea, anaphylaxis.",
        "contraindications": "History of severe allergic reaction (anaphylaxis, angioedema) to Penicillins, Cephalosporins, or other beta-lactam antibiotics.",
    },
    "azithromycin": {
        "name": "Azithromycin",
        "class": "Macrolide Antibiotic",
        "indication": "Community-acquired pneumonia, acute exacerbations of chronic bronchitis, atypical pneumonia, chlamydia trachomatis, traveler's diarrhea.",
        "dosage": "Standard 3-day course: 500 mg PO once daily for 3 days. Standard 5-day course (Z-Pak): 500 mg on day 1, followed by 250 mg once daily on days 2 through 5.",
        "timing": "Tablets may be taken with or without food. Take with food if stomach upset occurs.",
        "interactions": "QT-prolonging drugs (antiarrhythmics, antipsychotics, fluoroquinolones - increased risk of Torsades de Pointes), Antacids containing aluminum or magnesium (reduces rate of absorption, space by 2 hours), Digoxin, Warfarin.",
        "side_effects": "GI distress (diarrhea, nausea, abdominal cramping), headache, dizziness. Serious: QT prolongation, cardiac arrhythmias, cholestatic jaundice, hepatotoxicity.",
        "contraindications": "Known hypersensitivity to macrolides, history of cholestatic jaundice or hepatic dysfunction associated with prior azithromycin use.",
    },
    "atorvastatin": {
        "name": "Atorvastatin",
        "class": "HMG-CoA Reductase Inhibitor (Statin)",
        "indication": "Primary hyperlipidemia, mixed dyslipidemia, primary prevention of cardiovascular disease, secondary prevention in established ASCVD.",
        "dosage": "Initial dose: 10 mg to 20 mg PO once daily; high-intensity dose: 40 mg to 80 mg once daily for high ASCVD risk or post-acute coronary syndrome.",
        "timing": "Take once daily with or without food, at any time of day (has a long 14-hour terminal elimination half-life).",
        "interactions": "Strong CYP3A4 inhibitors (Clarithromycin, Itraconazole, Ketoconazole, Ritonavir) markedly increase statin blood levels and myopathy risk; Fibrates (Gemfibrozil - severe rhabdomyolysis risk); Grapefruit juice (> 1 liter/day inhibits intestinal CYP3A4).",
        "side_effects": "Myalgia (muscle pain/stiffness), arthralgia, mild elevation of liver transaminases (ALT/AST), mild elevation of fasting blood sugar.",
        "contraindications": "Active liver disease or unexplained persistent elevation of hepatic transaminases, pregnancy and breastfeeding.",
    },
    "omeprazole": {
        "name": "Omeprazole",
        "class": "Proton Pump Inhibitor (PPI)",
        "indication": "Gastroesophageal Reflux Disease (GERD), erosive esophagitis, duodenal and gastric ulcers, Zollinger-Ellison syndrome, H. pylori eradication.",
        "dosage": "GERD / Ulcers: 20 mg to 40 mg PO once daily for 4 to 8 weeks. Severe or erosive esophagitis: 40 mg once daily.",
        "timing": "Must be taken 30 to 60 minutes before breakfast. Swallow capsules whole; do not crush or chew.",
        "interactions": "Clopidogrel (Omeprazole inhibits CYP2C19, decreasing clopidogrel activation and antiplatelet efficacy; consider Pantoprazole as alternative), Methotrexate, Ketoconazole / Itraconazole (reduced antifungal absorption due to decreased gastric acidity).",
        "side_effects": "Headache, abdominal pain, diarrhea, constipation, nausea, flatulence. Long-term risks: hypomagnesemia, Vitamin B12 deficiency, bone fractures, Clostridioides difficile colitis.",
        "contraindications": "Known hypersensitivity to substituted benzimidazoles; concurrent administration with Rilpivirine-containing regimens.",
    },
    "cetirizine": {
        "name": "Cetirizine",
        "class": "Second-Generation Antihistamine",
        "indication": "Allergic rhinitis (hay fever), seasonal and perennial allergies, chronic urticaria (hives), allergic conjunctivitis.",
        "dosage": "Adults and children >= 6 years: 5 mg to 10 mg PO once daily. In renal impairment (eGFR < 50): 5 mg once daily.",
        "timing": "Take once daily with or without food. Preferred in the evening due to mild sedative potential in some individuals.",
        "interactions": "Central nervous system depressants, alcohol, sedatives, hypnotics (additive central nervous system depression and somnolence).",
        "side_effects": "Mild drowsiness/somnolence (less than 1st-generation antihistamines but higher than fexofenadine), fatigue, dry mouth, headache.",
        "contraindications": "Known hypersensitivity to cetirizine or hydroxyzine; end-stage renal disease (CrCl < 10 mL/min) on hemodialysis.",
    },
    "albuterol": {
        "name": "Albuterol (Salbutamol)",
        "class": "Short-Acting Beta-2 Agonist (SABA) Bronchodilator",
        "indication": "Relief and prevention of acute bronchospasm in bronchial asthma, COPD, and exercise-induced bronchoconstriction.",
        "dosage": "Metered-Dose Inhaler (90-100 mcg/puff): 1 to 2 inhalations every 4 to 6 hours as needed for acute wheezing/dyspnea. Exercise-induced: 2 puffs 15-30 minutes prior to exercise.",
        "timing": "Use as needed for sudden onset of shortness of breath or wheezing. Wait 1 minute between the first and second puff.",
        "interactions": "Non-selective beta-blockers (e.g., Propranolol - mutually inhibit effects and may precipitate severe bronchospasm), Loop/Thiazide diuretics (potentiate hypokalemia), MAO inhibitors and TCAs (potentiate cardiovascular effects).",
        "side_effects": "Tremors (shaky hands), tachycardia (rapid heartbeat), palpitations, nervousness, headache, transient hypokalemia.",
        "contraindications": "Hypersensitivity to albuterol or milk proteins (for certain dry powder inhaler formulations).",
    },
};

LAB_TESTS_DB: Dict[str, Dict[str, Any]] = {
    "cbc": {
        "name": "Complete Blood Count (CBC) with Differential",
        "specimen": "Whole Blood (Lavender-top K2/K3 EDTA tube)",
        "preparation": "No special fasting required.",
        "turnaround": "1-2 hours (STAT: 30-45 minutes)",
        "intervals": {
            "WBC": "4.5 – 11.0 x10^3/uL (Panic: < 2.0 or > 30.0)",
            "Hemoglobin (Hgb)": "Male: 13.8 – 17.2 g/dL, Female: 12.1 – 15.1 g/dL (Panic: < 7.0 or > 20.0)",
            "Hematocrit (Hct)": "Male: 40.7 – 50.3%, Female: 36.1 – 44.3%",
            "Platelets (PLT)": "150 – 450 x10^3/uL (Panic: < 50 or > 1000)",
            "Neutrophils": "40 – 70%",
            "Lymphocytes": "20 – 40%",
        },
        "high_meaning": "Elevated WBC (leukocytosis) points to bacterial infection, inflammation, tissue necrosis, leukemia, or physiological stress. Elevated Hgb/Hct suggests polycythemia vera, chronic hypoxia, or hemoconcentration/dehydration. Elevated Platelets indicates reactive thrombocytosis (infection, iron deficiency) or essential thrombocythemia.",
        "low_meaning": "Low WBC (leukopenia) indicates viral infections (Dengue, HIV), bone marrow suppression, or autoimmune conditions. Low Hemoglobin confirms anemia (iron deficiency, chronic disease, hemolysis, blood loss). Low Platelets (thrombocytopenia) suggests viral infections, ITP, sepsis, or drug-induced suppression, posing bleeding risks.",
        "tech_guidelines": "Invert EDTA tube 8-10 times immediately after phlebotomy. Check for microclots before running. Platelet clumping causes pseudothrombocytopenia; verify with peripheral smear or recollection in Sodium Citrate tube.",
    },
    "cmp": {
        "name": "Comprehensive Metabolic Panel (CMP-14)",
        "specimen": "Serum (Gold-top SST with clot activator) or Plasma (Green-top Lithium Heparin)",
        "preparation": "Fasting 8 to 12 hours required prior to collection.",
        "turnaround": "2-4 hours",
        "intervals": {
            "Fasting Glucose": "70 – 99 mg/dL (Panic: < 50 or > 400)",
            "Sodium (Na+)": "135 – 145 mmol/L (Panic: < 120 or > 160)",
            "Potassium (K+)": "3.5 – 5.0 mmol/L (Panic: < 2.8 or > 6.0)",
            "Chloride (Cl-)": "96 – 106 mmol/L",
            "Bicarbonate (CO2)": "23 – 29 mmol/L (Panic: < 10 or > 40)",
            "BUN": "7 – 20 mg/dL",
            "Creatinine": "0.7 – 1.3 mg/dL (Male), 0.5 – 1.1 mg/dL (Female)",
            "eGFR": "> 60 mL/min/1.73m²",
            "Calcium": "8.6 – 10.2 mg/dL",
            "Total Protein": "6.3 – 8.2 g/dL",
            "Albumin": "3.5 – 5.0 g/dL",
            "Bilirubin (Total)": "0.2 – 1.2 mg/dL",
            "ALP": "44 – 147 U/L",
            "ALT (SGPT)": "7 – 56 U/L",
            "AST (SGOT)": "10 – 40 U/L",
        },
        "high_meaning": "Elevated glucose indicates diabetes or acute metabolic stress. Hyperkalemia (> 5.0) causes life-threatening cardiac arrhythmias. Elevated BUN/Creatinine signifies acute or chronic renal impairment. Elevated ALT/AST indicates hepatocellular injury (hepatitis, drug toxicity, NAFLD).",
        "low_meaning": "Hypoglycemia (< 70) causes neuroglycopenia. Hypokalemia (< 3.5) causes muscle weakness, cramps, and U-waves on ECG. Low Albumin indicates liver failure, nephrotic syndrome, malnutrition, or systemic inflammation.",
        "tech_guidelines": "Hemolyzed samples falsely elevate Potassium, AST, and ALT due to erythrocyte content release. Grade 1+ hemolysis requires sample recollection. Centrifuge within 2 hours.",
    },
    "hba1c": {
        "name": "Glycated Hemoglobin (HbA1c)",
        "specimen": "Whole Blood (Lavender-top EDTA)",
        "preparation": "No fasting required (reflects glycemic control over prior 8-12 weeks).",
        "turnaround": "1-2 hours",
        "intervals": {
            "Normal": "< 5.7% (< 39 mmol/mol)",
            "Prediabetes": "5.7% – 6.4% (39 – 47 mmol/mol)",
            "Diabetes": ">= 6.5% (>= 48 mmol/mol)",
            "Target for Most Diabetics": "< 7.0% (< 53 mmol/mol)",
        },
        "high_meaning": "Higher values reflect sustained chronic hyperglycemia and increased risk of diabetic retinopathy, nephropathy, neuropathy, and macrovascular coronary events.",
        "low_meaning": "Low values (< 4.0%) may reflect frequent severe hypoglycemic episodes, shortened red blood cell lifespan (hemolytic anemia, recent blood transfusion), or pregnancy.",
        "tech_guidelines": "HPLC (High-Performance Liquid Chromatography) or capillary electrophoresis. Hemoglobinopathies (HbS, HbC, HbE) can interfere with specific assay methodologies.",
    },
    "lipid": {
        "name": "Lipid Profile / Panel",
        "specimen": "Serum (Gold-top SST) or Plasma (Lithium Heparin)",
        "preparation": "Fasting 9 to 12 hours recommended for accurate triglyceride measurement.",
        "turnaround": "2-4 hours",
        "intervals": {
            "Total Cholesterol": "< 200 mg/dL (Desirable), 200-239 (Borderline), >= 240 (High)",
            "HDL Cholesterol": "> 40 mg/dL (Men), > 50 mg/dL (Women) [Protective]",
            "LDL Cholesterol": "< 100 mg/dL (Optimal), 100-129 (Near optimal), >= 160 (High)",
            "Triglycerides": "< 150 mg/dL (Normal), 150-199 (Borderline), 200-499 (High), >= 500 (Very High / Pancreatitis risk)",
        },
        "high_meaning": "Elevated LDL-C and Total Cholesterol accelerate coronary atherogenesis. Severe hypertriglyceridemia (> 500 mg/dL) carries significant risk of acute pancreatitis.",
        "low_meaning": "Low HDL-C is an independent negative cardiovascular risk factor. Markedly low Total Cholesterol may indicate severe malnutrition, malabsorption, or advanced liver disease.",
        "tech_guidelines": "If Triglycerides > 400 mg/dL, Friedewald calculation for LDL (Total - HDL - TG/5) is invalid; direct enzymatic LDL measurement is required.",
    },
    "troponin": {
        "name": "High-Sensitivity Cardiac Troponin I (hs-cTnI)",
        "specimen": "Plasma (Green-top Lithium Heparin) or Serum (Gold-top SST)",
        "preparation": "STAT order; no preparation. Immediate draw and processing.",
        "turnaround": "30 to 60 minutes (STAT protocol)",
        "intervals": {
            "99th Percentile Upper Reference Limit": "< 0.04 ng/mL (or < 14-26 ng/L depending on platform)",
            "Myocardial Infarction Threshold": "Rising kinetic delta >= 20% on serial draw at 0h, 1h/2h, and 3h",
        },
        "high_meaning": "Indicates acute myocardial injury. Markedly elevated or dynamically rising troponin confirms Acute Myocardial Infarction (NSTEMI/STEMI). Non-coronary causes include pulmonary embolism, severe sepsis, myocarditis, and acute heart failure.",
        "low_meaning": "Troponin levels below the limit of detection on serial draws with low-risk clinical score have a 99% negative predictive value for acute coronary syndrome.",
        "tech_guidelines": "Chemiluminescent microparticle immunoassay. Centrifuge immediately upon receipt. Immediately alert ordering physician and emergency department for any value above the 99th percentile URL.",
    },
    "tsh": {
        "name": "Thyroid Stimulating Hormone (TSH) with Reflex Free T4",
        "specimen": "Serum (Gold-top SST)",
        "preparation": "Morning blood collection preferred. Avoid Biotin (Vitamin B7) supplements for 48 hours prior to testing as it causes false assay interference.",
        "turnaround": "2-4 hours",
        "intervals": {
            "TSH": "0.4 – 4.0 mIU/L (or uIU/mL)",
            "Free T4": "0.8 – 1.8 ng/dL (10 – 23 pmol/L)",
            "Free T3": "2.3 – 4.2 pg/mL (3.5 – 6.5 pmol/L)",
        },
        "high_meaning": "Elevated TSH (> 4.5) with low Free T4 indicates Primary Hypothyroidism (Hashimoto's thyroiditis). Elevated TSH with normal Free T4 indicates Subclinical Hypothyroidism.",
        "low_meaning": "Suppressed TSH (< 0.1) with elevated Free T4/T3 indicates Hyperthyroidism (Graves' disease, toxic nodular goiter). Suppressed TSH with low Free T4 suggests Central / Pituitary Hypothyroidism.",
        "tech_guidelines": "High-dose Biotin supplements (> 5 mg/day) cause falsely low TSH and falsely elevated Free T4 in competitive and sandwich immunoassays.",
    },
};


# ==============================================================================
# 2. EMERGENCY RED-FLAG DETECTOR
# ==============================================================================

EMERGENCY_PATTERNS = [
    (r"\b(crushing|severe)\s+chest\s+pain\b", "Severe crushing chest pain radiating to arm, neck, or jaw is a hallmark of acute myocardial infarction (heart attack)."),
    (r"\b(can't|cannot|unable to)\s+breathe\b", "Acute severe respiratory distress requires emergency airway evaluation and supplemental oxygen."),
    (r"\bshortness\s+of\s+breath\b.*\bchest\s+pain\b", "Co-occurrence of breathlessness and chest discomfort indicates potential acute coronary syndrome or pulmonary embolism."),
    (r"\b(face|facial)\s+droop(ing)?\b|\bslurred\s+speech\b|\barm\s+weakness\b", "FAST signs (Facial drooping, Arm weakness, Slurred speech) indicate acute stroke requiring emergency thrombolysis evaluation within the critical 4.5-hour window."),
    (r"\bthroat\s+swelling\b|\bswelling\s+of\s+lips\b|\banaphylaxis\b", "Signs of acute anaphylactic reaction require immediate intramuscular Epinephrine and emergency stabilization."),
    (r"\b(vomiting\s+blood|hematemesis|black\s+tarry\s+stool|melena)\b", "Upper gastrointestinal bleeding requires urgent hemodynamic assessment and medical resuscitation."),
]


# ==============================================================================
# 3. CLINICAL REASONING AND DYNAMIC SYNTHESIS ENGINE
# ==============================================================================

class ClinicalEngine:
    """Core domain intelligence engine providing accurate, dynamic clinical answers."""

    @staticmethod
    def check_emergency(query: str) -> Optional[str]:
        """Evaluate if user prompt contains acute emergency red-flag triggers."""
        q_lower = query.lower()
        for pattern, advisory in EMERGENCY_PATTERNS:
            if re.search(pattern, q_lower):
                return advisory
        return None

    @staticmethod
    def find_matched_entities(query: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract matching conditions, medications, and lab tests from the user query using precise triggers."""
        q_lower = query.lower()
        matched_conditions = []
        matched_medications = []
        matched_tests = []

        # 1. Condition Triggers
        CONDITION_TRIGGERS = {
            "dengue": [r"\bdengue\b", r"\bbreakbone\b"],
            "malaria": [r"\bmalaria\b", r"\bplasmodium\b"],
            "covid": [r"\bcovid\b", r"\bsars-cov-2\b", r"\bcoronavirus\b"],
            "diabetes": [r"\bdiabet", r"\bblood sugar\b", r"\bhyperglycemia\b", r"\bglucose level\b", r"\binsulin resist"],
            "hypertension": [r"\bhypertension\b", r"\bhigh blood pressure\b", r"\bblood pressure\b", r"\bhypertensive\b"],
            "fever": [r"\bfever\b", r"\bpyrexia\b", r"\bhigh temperature\b", r"\bfebrile\b"],
            "migraine": [r"\bmigraine\b", r"\bhemicrania\b"],
            "headache": [r"\bheadache\b", r"\bcephalea\b", r"\bhead pain\b"],
            "asthma": [r"\basthma\b", r"\bwheez", r"\bbronchospasm\b"],
            "gerd": [r"\bgerd\b", r"\bacid reflux\b", r"\bheartburn\b", r"\breflux disease\b", r"\besophagitis\b"],
            "uti": [r"\buti\b", r"\burinary tract infection\b", r"\bbladder infection\b", r"\bcystitis\b", r"\bburning urine\b"],
            "cholesterol": [r"\bcholesterol\b", r"\bhyperlipidemia\b", r"\bdyslipidemia\b", r"\btriglyceride\b", r"\blipid profile\b"],
        }
        for cond, patterns in CONDITION_TRIGGERS.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                matched_conditions.append(cond)

        # If both migraine and headache matched, prioritize migraine
        if "migraine" in matched_conditions and "headache" in matched_conditions:
            matched_conditions.remove("headache")

        # 2. Medication Triggers
        MEDICATION_TRIGGERS = {
            "paracetamol": [r"\bparacetamol\b", r"\bacetaminophen\b", r"\btylenol\b", r"\bcrocin\b", r"\bdolo\b", r"\bpanadol\b"],
            "ibuprofen": [r"\bibuprofen\b", r"\badvil\b", r"\bmotrin\b", r"\bbrufen\b"],
            "metformin": [r"\bmetformin\b", r"\bglucophage\b"],
            "lisinopril": [r"\blisinopril\b", r"\bprinivil\b", r"\bzestril\b"],
            "amoxicillin": [r"\bamoxicillin\b", r"\bmoxatag\b", r"\bamoxil\b"],
            "azithromycin": [r"\bazithromycin\b", r"\bzithromax\b", r"\bz-pak\b"],
            "atorvastatin": [r"\batorvastatin\b", r"\blipitor\b"],
            "omeprazole": [r"\bomeprazole\b", r"\bprilosec\b"],
            "cetirizine": [r"\bcetirizine\b", r"\bzyrtec\b"],
            "albuterol": [r"\balbuterol\b", r"\bsalbutamol\b", r"\bventolin\b", r"\bproair\b"],
        }
        for med, patterns in MEDICATION_TRIGGERS.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                matched_medications.append(med)

        # 3. Lab Test Triggers
        LAB_TEST_TRIGGERS = {
            "cbc": [r"\bcbc\b", r"\bcomplete blood count\b", r"\bhemoglobin\b", r"\bplatelet count\b", r"\bwhite blood cell\b"],
            "cmp": [r"\bcmp\b", r"\bmetabolic panel\b", r"\bserum electrolyte\b", r"\bkidney function test\b", r"\bliver function test\b"],
            "hba1c": [r"\bhba1c\b", r"\ba1c\b", r"\bglycated hemoglobin\b"],
            "lipid": [r"\blipid panel\b", r"\blipid profile\b", r"\bserum cholesterol\b"],
            "troponin": [r"\btroponin\b", r"\bcardiac biomarker\b"],
            "tsh": [r"\btsh\b", r"\bthyroid stimulating\b", r"\bthyroid panel\b", r"\bfree t4\b"],
        }
        for test, patterns in LAB_TEST_TRIGGERS.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                matched_tests.append(test)

        return matched_conditions, matched_medications, matched_tests

    @classmethod
    def generate_clinical_response(cls, user_prompt: str, user_role: UserRole = UserRole.PATIENT) -> str:
        """Dynamically formulate a deep, structured, role-adapted medical response."""
        # Extract clean query
        q_match = re.search(r"\[User\]:\s*(.*)", user_prompt, re.DOTALL)
        clean_query = q_match.group(1).strip() if q_match else user_prompt.strip()

        # Extract role if embedded
        role_match = re.search(r"Active User Role:\s*(\w+)", user_prompt)
        role = UserRole(role_match.group(1)) if role_match else user_role

        emergency_warning = cls.check_emergency(clean_query)
        matched_conditions, matched_medications, matched_tests = cls.find_matched_entities(clean_query)

        output_parts: List[str] = []

        # 1. Emergency Pre-banner if triggered
        if emergency_warning:
            output_parts.append(
                f"> [!CAUTION]\n"
                f"> **CRITICAL EMERGENCY MEDICAL ALERT**\n"
                f"> {emergency_warning}\n"
                f"> **Immediate Action Required**: Call emergency services (911 / 112) or go to the nearest emergency room immediately. Do not drive yourself."
            )

        # 2. Check for Platform / SaaS Navigation questions
        platform_response = cls._handle_platform_queries(clean_query, role)
        if platform_response:
            output_parts.append(platform_response)
            return "\n\n".join(output_parts)

        # 3. Check for specific Condition queries
        if matched_conditions:
            cond_key = matched_conditions[0]
            cond_data = CONDITIONS_DB[cond_key]
            output_parts.append(cls._format_condition_response(cond_data, role, clean_query))

        # 4. Check for Medication queries
        if matched_medications:
            med_key = matched_medications[0]
            med_data = MEDICATIONS_DB[med_key]
            output_parts.append(cls._format_medication_response(med_data, role, clean_query))

        # 5. Check for Lab Test queries
        if matched_tests:
            test_key = matched_tests[0]
            test_data = LAB_TESTS_DB[test_key]
            output_parts.append(cls._format_lab_test_response(test_data, role, clean_query))

        # 6. Universal Semantic Synthesizer for arbitrary or unmatched clinical queries
        if not matched_conditions and not matched_medications and not matched_tests:
            output_parts.append(cls._synthesize_general_clinical_query(clean_query, role))

        # 7. Standard Disclaimers based on Role
        disclaimer = cls._get_disclaimer(role)
        output_parts.append(disclaimer)

        return "\n\n".join(output_parts)

    @staticmethod
    def _format_condition_response(data: Dict[str, Any], role: UserRole, query: str) -> str:
        """Format an extensive, role-tailored condition overview."""
        title = f"### **Clinical Overview: {data['name']}**"
        description = f"**Definition**: {data['description']}\n\n**Common Causes & Triggers**:\n" + "\n".join(f"- {c}" for c in data["common_causes"])
        red_flags = "\n\n**Clinical Red Flags (Seek Urgent Care)**:\n" + "\n".join(f"- {rf}" for rf in data["red_flags"])

        if role == UserRole.DOCTOR:
            guidance = f"#### **Physician Clinical Decision Support**\n{data['doctor_guidance']}"
        elif role == UserRole.LAB_TECHNICIAN:
            guidance = f"#### **Laboratory Diagnostic & Specimen Context**\n{data['lab_guidance']}"
        elif role == UserRole.PHARMACY_STAFF:
            guidance = f"#### **Pharmacotherapeutic & Formulary Review**\n{data['pharmacy_guidance']}"
        elif role == UserRole.ADMIN:
            guidance = f"#### **Clinical Governance & Care Continuity**\nPatients presenting with {data['name']} are managed across verified Doctor schedules, integrated laboratory diagnostics, and dispensary fulfillment with strict HIPAA audit isolation."
        else:
            # Patient
            guidance = f"#### **Patient Health Guidance & Next Steps**\n{data['patient_guidance']}"

        return f"{title}\n\n{description}{red_flags}\n\n{guidance}"

    @staticmethod
    def _format_medication_response(data: Dict[str, Any], role: UserRole, query: str) -> str:
        """Format an extensive, role-tailored medication profile."""
        title = f"### **Medication Safety Guide: {data['name']}**"
        overview = (
            f"**Pharmacological Class**: {data['class']}\n"
            f"**Clinical Indication**: {data['indication']}\n"
            f"**Dosage & Administration**: {data['dosage']}\n"
            f"**Administration Timing**: {data['timing']}"
        )
        safety = (
            f"#### **Safety Profile & Interactions**\n"
            f"- **Key Interactions**: {data['interactions']}\n"
            f"- **Common Adverse Effects**: {data['side_effects']}\n"
            f"- **Contraindications**: {data['contraindications']}"
        )

        if role == UserRole.PHARMACY_STAFF:
            role_advisory = "#### **Dispensary Audit Notes**\nVerify patient allergy records and cross-reference with concurrent prescriptions in the CareAI dispensary queue before dispensing."
        elif role == UserRole.DOCTOR:
            role_advisory = "#### **Prescribing Considerations**\nReview hepatic and renal clearance metrics, patient co-morbidities, and verify that digital prescription item sig codes adhere to institutional guidelines."
        else:
            role_advisory = "#### **Patient Usage Advice**\nAlways take this medication exactly as directed by your physician. Do not discontinue or adjust your dose without medical consultation."

        return f"{title}\n\n{overview}\n\n{safety}\n\n{role_advisory}"

    @staticmethod
    def _format_lab_test_response(data: Dict[str, Any], role: UserRole, query: str) -> str:
        """Format an extensive, role-tailored diagnostic laboratory profile."""
        title = f"### **Diagnostic Laboratory Guide: {data['name']}**"
        specimen_info = (
            f"- **Specimen Type**: {data['specimen']}\n"
            f"- **Patient Preparation**: {data['preparation']}\n"
            f"- **Turnaround Time**: {data['turnaround']}"
        )
        intervals = "\n".join(f"| **{k}** | {v} |" for k, v in data["intervals"].items())
        table = f"#### **Standard Reference Intervals & Critical Panic Limits**\n\n| Biomarker / Parameter | Reference Interval |\n| :--- | :--- |\n{intervals}"

        clinical_meaning = (
            f"#### **Clinical Interpretation**\n"
            f"- **Elevated Levels**: {data['high_meaning']}\n"
            f"- **Decreased Levels**: {data['low_meaning']}"
        )

        if role == UserRole.LAB_TECHNICIAN:
            role_specific = f"#### **Pre-Analytical & Analytical Guidelines**\n{data['tech_guidelines']}"
        elif role == UserRole.DOCTOR:
            role_specific = "#### **Clinical Correlation**\nCorrelate biomarker shifts with clinical presentation. Immediate notification required for values breaching critical panic limits."
        else:
            role_specific = "#### **Patient Understanding**\nLab results must always be interpreted in context with your medical history and clinical examination by your attending doctor."

        return f"{title}\n\n{specimen_info}\n\n{table}\n\n{clinical_meaning}\n\n{role_specific}"

    @staticmethod
    def _handle_platform_queries(query: str, role: UserRole) -> Optional[str]:
        """Handle questions related to CareAI features, appointment booking, prescriptions, etc."""
        q_lower = query.lower()

        if "book" in q_lower and ("appointment" in q_lower or "doctor" in q_lower or "slot" in q_lower):
            return (
                "### **How to Book an Appointment on CareAI**\n\n"
                "1. **Explore Specialists**: Navigate to **Find Doctors** or your **Patient Dashboard**.\n"
                "2. **Select Doctor & Specialty**: Choose your preferred physician based on specialty, experience, and consultation fee.\n"
                "3. **Select Date & Available Slot**: View real-time active consultation availability slots.\n"
                "4. **Confirm Booking**: Enter your chief complaint or consultation reason and click **Confirm Appointment**.\n"
                "5. **Real-time Status**: Your confirmed appointment will appear in your **My Appointments** queue with immediate notifications."
            )

        if "prescription" in q_lower and ("view" in q_lower or "download" in q_lower or "access" in q_lower or "where" in q_lower):
            return (
                "### **Managing Your Digital Prescriptions on CareAI**\n\n"
                "- **Patients**: Navigate to **Prescriptions** from your navigation bar to review all issued digital prescriptions, complete with dosage instructions, medicine names, and AI safety summaries.\n"
                "- **Doctors**: Can issue digital prescriptions directly from the consultation workspace with integrated real-time drug interaction screening.\n"
                "- **Pharmacy Staff**: Access the **Dispensary Queue** to audit active prescriptions and update fulfillment status from `PRESCRIBED` to `READY` and `DISPENSED`."
            )

        if "lab" in q_lower and ("report" in q_lower or "result" in q_lower or "test" in q_lower):
            return (
                "### **Accessing Diagnostic Lab Reports on CareAI**\n\n"
                "- **Patients**: Go to **Lab Reports** in your portal. Released reports display measured test values, standardized reference ranges, and abnormal panic flags.\n"
                "- **Lab Technicians**: Manage incoming specimen orders from the **Lab Workspace**, record barcode accessioning, enter analytical results, and release verified diagnostic reports.\n"
                "- **Doctors**: Receive instant automated notifications when critical panic-level results are verified for their patients."
            )

        if "approve" in q_lower and ("doctor" in q_lower or "license" in q_lower or "admin" in q_lower):
            return (
                "### **Doctor Credential Verification Workflow (Admin)**\n\n"
                "1. Log in to the **Administrator Console**.\n"
                "2. Navigate to the **Doctor Approvals** section.\n"
                "3. Review the physician's license number, specialization, medical background, and hospital affiliations.\n"
                "4. Click **Approve Credential** to transition the doctor to `APPROVED` status, enabling their public booking availability."
            )

        if any(greet in q_lower.split() for greet in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
            role_name = role.value.replace("_", " ").title()
            return (
                f"### **Hello! Welcome to CareAI Assistant**\n\n"
                f"I am your specialized **CareAI {role_name} Assistant**, powered by advanced clinical intelligence.\n\n"
                f"**How can I assist you today?**\n"
                f"- **Medical Questions**: Ask about symptoms, diseases, medications, dosages, or side effects.\n"
                f"- **Diagnostic Tests**: Inquire about lab reference ranges, sample preparations, and clinical interpretations.\n"
                f"- **CareAI Workflows**: Ask for guidance on appointments, digital prescriptions, lab orders, or portal features.\n\n"
                f"*Feel free to type your medical or platform question below!*"
            )

        return None

    @classmethod
    def _synthesize_general_clinical_query(cls, query: str, role: UserRole) -> str:
        """Universal semantic synthesis for any general, complex, or conversational health inquiry."""
        # Extract keywords
        words = [w for w in re.findall(r"\b\w+\b", query) if len(w) > 3 and w.lower() not in ["what", "when", "where", "which", "with", "from", "about", "could", "would", "should", "please", "tell", "explain"]]
        topic = ", ".join(words[:4]) if words else query.strip()

        title = f"### **Clinical Insights: {topic.title()}**"

        if role == UserRole.DOCTOR:
            body = (
                f"Regarding your clinical inquiry on **\"{query}\"**:\n\n"
                f"1. **Clinical Assessment & Pathophysiology**:\n"
                f"   - Evaluate underlying anatomical and physiological mechanisms relating to {topic}.\n"
                f"   - Review baseline patient medical records, active chronic conditions, and recent biochemical markers.\n\n"
                f"2. **Evidence-Based Guidelines & Differential Diagnosis**:\n"
                f"   - Consider primary versus secondary etiologies and stratify severity according to standardized clinical criteria.\n"
                f"   - Formulate a targeted diagnostic and therapeutic plan while monitoring for pharmacological contraindications.\n\n"
                f"3. **Longitudinal Monitoring**:\n"
                f"   - Schedule follow-up consultations to evaluate therapeutic response and adjust dosages as indicated."
            )
        elif role == UserRole.LAB_TECHNICIAN:
            body = (
                f"Regarding your diagnostic query on **\"{query}\"**:\n\n"
                f"1. **Analytical Testing & Specimen Integrity**:\n"
                f"   - Adhere to CLIA/CAP standardized laboratory protocols for {topic}.\n"
                f"   - Ensure specimen collection tubes meet standard draw volume and evaluate for pre-analytical interference (hemolysis, lipemia, icterus, clotting).\n\n"
                f"2. **Quality Control & Calibration**:\n"
                f"   - Verify that daily two-level quality control runs fall within 2 standard deviations on Levey-Jennings charts before reporting patient specimens.\n"
                f"   - Immediately escalate any results breaching critical panic thresholds."
            )
        elif role == UserRole.PHARMACY_STAFF:
            body = (
                f"Regarding your pharmaceutical evaluation on **\"{query}\"**:\n\n"
                f"1. **Pharmacological Considerations**:\n"
                f"   - Analyze pharmacokinetics, hepatic metabolism (CYP450 pathways), and renal clearance considerations for {topic}.\n"
                f"   - Screen for therapeutic duplication, narrow therapeutic index warnings, and drug-food timing advisories.\n\n"
                f"2. **Patient Counseling & Dispensation**:\n"
                f"   - Provide clear administration guidelines, highlight potential adverse drug reactions, and counsel on adherence."
            )
        elif role == UserRole.ADMIN:
            body = (
                f"Regarding your administrative inquiry on **\"{query}\"**:\n\n"
                f"1. **Platform Security & Compliance**:\n"
                f"   - CareAI strictly enforces Role-Based Access Control (RBAC) and Protected Health Information (PHI) privacy barriers.\n"
                f"   - All operational events, doctor approvals, and dispensary logs are tracked immutably in system audit tables.\n\n"
                f"2. **System Health & Governance**:\n"
                f"   - Monitor role allocations, provider credential verifications, and clinical workflows across the healthcare network."
            )
        else:
            # Patient Role
            body = (
                f"Regarding your question on **\"{query}\"**:\n\n"
                f"1. **Understanding Your Health**:\n"
                f"   - {topic.title()} is an important aspect of your health and wellness that should be evaluated in context with your overall physical state.\n"
                f"   - Common factors influencing this include lifestyle habits, adequate sleep, balanced nutrition, hydration, and adherence to prescribed treatments.\n\n"
                f"2. **Helpful Self-Care Steps**:\n"
                f"   - Keep track of any accompanying symptoms (such as fever, pain, fatigue, or changes in energy levels).\n"
                f"   - Avoid self-medicating with unprescribed medications or altering any current prescriptions without your doctor's guidance.\n\n"
                f"3. **When to Seek Medical Attention**:\n"
                f"   - If your symptoms persist, worsen, or cause significant discomfort, please schedule an appointment with a verified CareAI doctor for personalized evaluation."
            )

        return f"{title}\n\n{body}"

    @staticmethod
    def _get_disclaimer(role: UserRole) -> str:
        """Return clear medical disclaimer appropriate for the user's role."""
        if role in [UserRole.DOCTOR, UserRole.LAB_TECHNICIAN, UserRole.PHARMACY_STAFF]:
            return "*Clinical Decision Support Notice: CareAI provides informational clinical intelligence based on established clinical practice guidelines and does not substitute for independent professional medical judgment or institutional clinical protocols.*"
        elif role == UserRole.ADMIN:
            return "*CareAI Platform Operations Notice: Protected Health Information (PHI) is protected under strict role-based access control policies.*"
        else:
            return "*Important Medical Notice: CareAI provides helpful health education and information. It is not a substitute for professional medical diagnosis, advice, or treatment. Always consult your qualified healthcare provider with any medical questions.*"


clinical_engine = ClinicalEngine()
