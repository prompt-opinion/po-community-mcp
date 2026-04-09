/**
 * med-instructions.ts
 * RxNorm code → plain-language medication purpose and special instructions.
 * Used by Tool 2 (GenerateDischargeInstructions) to populate the medications section.
 *
 * 
 * Keyed by RxNorm concept unique identifier (RXCUI).
 * When a med is not in this table, fall back to the drug class lookup or generic description.
 */

export interface MedInstruction {
  purpose: string;          // Plain-language explanation of why the patient takes this
  notes?: string;           // Special instructions (timing, food, storage, warnings)
  simpleNotes?: string;     // 5th-grade alternative for readingLevel="simple"
}

// ── Primary RxNorm-keyed lookup ───────────────────────────────────────────────
// Keys are RxNorm CUIs as strings. Drug name in comment for readability.

export const MED_INSTRUCTIONS: Record<string, MedInstruction> = {

  // ── Antibiotics ──────────────────────────────────────────────────────────

  // Azithromycin 250mg
  "308460": {
    purpose: "To treat your lung infection (pneumonia)",
    notes: "Take with food to avoid stomach upset. Complete the full course even if you feel better.",
    simpleNotes: "Take with food. Keep taking all your pills even if you feel better.",
  },
  // Amoxicillin 500mg
  "723": {
    purpose: "To treat bacterial infection",
    notes: "Take with or without food. Complete the full course. Avoid if allergic to penicillin.",
    simpleNotes: "Take all your pills. Stop and call your doctor if you get a rash.",
  },
  // Ciprofloxacin 500mg
  "141962": {
    purpose: "To treat bacterial infection",
    notes: "Take on an empty stomach if possible. Avoid antacids within 2 hours of dose. Drink plenty of water.",
    simpleNotes: "Try to take on an empty stomach. Drink lots of water.",
  },
  // Doxycycline 100mg
  "310026": {
    purpose: "To treat bacterial infection",
    notes: "Take with a full glass of water. Do not lie down for 30 minutes after taking. Avoid sun exposure.",
    simpleNotes: "Take with lots of water. Stay upright for 30 minutes. Wear sunscreen outside.",
  },
  // Trimethoprim-sulfamethoxazole (TMP-SMX) 800/160mg
  "198333": {
    purpose: "To treat bacterial infection (urinary or other)",
    notes: "Drink plenty of fluids. Avoid direct sunlight. Complete the full course.",
    simpleNotes: "Drink lots of water. Complete all your pills.",
  },

  // ── Diabetes medications ──────────────────────────────────────────────────

  // Metformin 500mg
  "860975": {
    purpose: "To control your blood sugar (diabetes)",
    notes: "Take with meals to reduce stomach upset. Do not crush or chew extended-release tablets.",
    simpleNotes: "Take with food to avoid stomach upset.",
  },
  // Metformin 1000mg
  "861007": {
    purpose: "To control your blood sugar (diabetes)",
    notes: "Take with meals. Do not skip doses — blood sugar control requires consistent dosing.",
    simpleNotes: "Take with meals every day.",
  },
  // Glipizide 5mg
  "310489": {
    purpose: "To lower your blood sugar (diabetes)",
    notes: "Take 30 minutes before meals. Monitor for low blood sugar (shakiness, sweating, confusion).",
    simpleNotes: "Take before eating. Watch for signs of low blood sugar: shaking, sweating, feeling confused.",
  },
  // Insulin glargine (Lantus)
  "285018": {
    purpose: "Long-acting insulin to control your blood sugar",
    notes: "Inject at the same time each day. Rotate injection sites. Store unopened vials in the refrigerator; opened vials at room temperature up to 28 days.",
    simpleNotes: "Inject at the same time each day. Keep unopened insulin in the fridge.",
  },
  // Insulin lispro (Humalog) — rapid-acting
  "86009": {
    purpose: "Fast-acting insulin to control blood sugar at meals",
    notes: "Inject within 15 minutes before eating or immediately after starting a meal. Monitor blood sugar before and after meals.",
    simpleNotes: "Inject just before you eat.",
  },

  // ── Blood pressure medications ────────────────────────────────────────────

  // Lisinopril 10mg
  "314076": {
    purpose: "To lower your blood pressure",
    notes: "Take at the same time each day. You may develop a dry cough — contact your doctor if bothersome. Avoid potassium supplements unless directed.",
    simpleNotes: "Take at the same time every day. Call your doctor if you develop a dry cough.",
  },
  // Lisinopril 20mg (same RXCUI family — handled same way)
  "314077": {
    purpose: "To lower your blood pressure",
    notes: "Take at the same time each day. A dry cough is a common side effect. Avoid potassium supplements unless directed.",
    simpleNotes: "Take at the same time every day. Call your doctor if you develop a dry cough.",
  },
  // Amlodipine 5mg
  "197361": {
    purpose: "To lower your blood pressure and improve blood flow to your heart",
    notes: "Take at the same time each day. Swelling in the ankles is a common side effect.",
    simpleNotes: "Take at the same time every day.",
  },
  // Metoprolol succinate 50mg (extended release)
  "866514": {
    purpose: "To lower your blood pressure and heart rate, and protect your heart",
    notes: "Do not stop taking suddenly — gradual tapering is required. Take with food.",
    simpleNotes: "Take with food. Do not stop taking without talking to your doctor first.",
  },
  // Carvedilol 6.25mg
  "200031": {
    purpose: "To lower your blood pressure and heart rate, and support heart function",
    notes: "Take with food to reduce dizziness. Do not stop suddenly.",
    simpleNotes: "Take with food. Do not stop taking without your doctor's approval.",
  },
  // Losartan 50mg
  "203160": {
    purpose: "To lower your blood pressure",
    notes: "Take at the same time each day. Avoid potassium supplements and salt substitutes.",
    simpleNotes: "Take at the same time every day.",
  },
  // Furosemide 40mg (loop diuretic)
  "202991": {
    purpose: "Water pill to remove extra fluid from your body",
    notes: "Best taken in the morning to avoid nighttime urination. Eat bananas, oranges, or potatoes to replace lost potassium.",
    simpleNotes: "Take in the morning. Eat bananas or oranges to keep your potassium up.",
  },
  // Spironolactone 25mg
  "202672": {
    purpose: "Water pill that also helps your heart and prevents potassium loss",
    notes: "Avoid potassium supplements and high-potassium salt substitutes. Check with your doctor before taking NSAIDs (ibuprofen, etc.).",
    simpleNotes: "Do not take extra potassium supplements. Ask your doctor before taking ibuprofen.",
  },

  // ── Cholesterol medications ───────────────────────────────────────────────

  // Atorvastatin 20mg (generic)
  "259255": {
    purpose: "To lower your cholesterol and protect your heart and blood vessels",
    notes: "Take in the evening or at bedtime for best effect. Report any muscle pain or weakness to your doctor.",
    simpleNotes: "Take at night. Call your doctor if your muscles hurt or feel weak.",
  },
  // Lipitor 20mg (brand — same as atorvastatin 20mg)
  "617312": {
    purpose: "To lower your cholesterol and protect your heart and blood vessels",
    notes: "Take in the evening or at bedtime for best effect. Report any muscle pain or weakness to your doctor.",
    simpleNotes: "Take at night. Call your doctor if your muscles hurt or feel weak.",
  },
  // Simvastatin 20mg
  "312961": {
    purpose: "To lower your cholesterol",
    notes: "Take in the evening. Avoid large amounts of grapefruit juice. Report muscle pain to your doctor.",
    simpleNotes: "Take at night. Avoid grapefruit juice. Call your doctor if your muscles hurt.",
  },
  // Rosuvastatin 10mg
  "301542": {
    purpose: "To lower your cholesterol and reduce heart disease risk",
    notes: "Can be taken at any time of day. Report muscle pain to your doctor.",
    simpleNotes: "Take once a day. Call your doctor if your muscles hurt.",
  },

  // ── Pain / fever medications ──────────────────────────────────────────────

  // Acetaminophen 500mg
  "198440": {
    purpose: "To relieve pain and reduce fever",
    notes: "Do not exceed 4,000 mg (4g) in 24 hours. Avoid alcohol. Check other medications for hidden acetaminophen (Tylenol).",
    simpleNotes: "Do not take more than 8 tablets in one day. Check other medicines for Tylenol.",
  },
  // Ibuprofen 400mg
  "197806": {
    purpose: "To relieve pain and reduce inflammation",
    notes: "Take with food or milk to protect your stomach. Avoid if you have kidney disease or heart failure. Limit alcohol.",
    simpleNotes: "Take with food. Do not take if you have kidney problems.",
  },
  // Naproxen 500mg
  "849727": {
    purpose: "To relieve pain and reduce inflammation",
    notes: "Take with food. Avoid in kidney disease, heart failure, or peptic ulcer disease.",
    simpleNotes: "Take with food.",
  },
  // Oxycodone 5mg (opioid)
  "1049502": {
    purpose: "To control moderate to severe pain",
    notes: "Take only as prescribed. Do not drive or operate machinery. May cause constipation — drink water and eat fiber. Do not drink alcohol.",
    simpleNotes: "Only take as your doctor ordered. Do not drive. Do not drink alcohol.",
  },
  // Hydrocodone/acetaminophen 5/325mg (Norco, Vicodin)
  "856900": {
    purpose: "To control moderate to severe pain",
    notes: "Contains acetaminophen — do not take additional Tylenol. Do not drive or drink alcohol. Can cause constipation.",
    simpleNotes: "Do not take extra Tylenol. Do not drive or drink alcohol.",
  },

  // ── Anticoagulants ────────────────────────────────────────────────────────

  // Warfarin 5mg (Coumadin)
  "855332": {
    purpose: "Blood thinner to prevent dangerous blood clots",
    notes: "Keep your INR appointments — this medication requires regular monitoring. Eat consistent amounts of green vegetables (vitamin K). Watch for unusual bleeding or bruising.",
    simpleNotes: "Keep all blood test appointments. Watch for unusual bruising or bleeding.",
  },
  // Apixaban 5mg (Eliquis)
  "1364435": {
    purpose: "Blood thinner to prevent dangerous blood clots",
    notes: "Take twice daily at the same times. Do not stop without talking to your doctor — stopping suddenly increases clot risk. Watch for unusual bleeding.",
    simpleNotes: "Take twice a day. Do not stop taking without your doctor's approval.",
  },
  // Rivaroxaban 20mg (Xarelto)
  "1114195": {
    purpose: "Blood thinner to prevent dangerous blood clots",
    notes: "Take with the evening meal for best absorption. Do not miss doses. Watch for unusual bleeding.",
    simpleNotes: "Take with dinner. Watch for unusual bruising or bleeding.",
  },

  // ── Respiratory medications ────────────────────────────────────────────────

  // Albuterol inhaler (rescue)
  "745679": {
    purpose: "Quick-relief inhaler to open your airways during breathing difficulty",
    notes: "Use only when having difficulty breathing. Shake well before use. Rinse mouth after use. If you need it more than 2 times per week, contact your doctor.",
    simpleNotes: "Use when you have trouble breathing. If you need it more than twice a week, call your doctor.",
  },
  // Tiotropium (Spiriva) — COPD maintenance
  "896458": {
    purpose: "Long-acting inhaler to keep your airways open (for COPD)",
    notes: "Use once daily at the same time. Rinse mouth after use. Do not use for sudden breathing problems — use rescue inhaler instead.",
    simpleNotes: "Use once a day at the same time. This is not for sudden breathing problems.",
  },
  // Fluticasone/salmeterol (Advair) inhaler
  "896766": {
    purpose: "Combination inhaler to reduce airway inflammation and keep airways open",
    notes: "Use twice daily. Rinse mouth after use to prevent thrush. Do not use for sudden breathing emergencies.",
    simpleNotes: "Use twice a day. Rinse your mouth after each use.",
  },
  // Prednisone 10mg (oral steroid)
  "312615": {
    purpose: "To reduce inflammation and help your body recover",
    notes: "Take with food. Do not stop suddenly — always taper as directed. May cause increased blood sugar, mood changes, or insomnia.",
    simpleNotes: "Take with food. Do not stop suddenly — follow your doctor's tapering plan.",
  },

  // ── Heart / cardiac medications ────────────────────────────────────────────

  // Aspirin 81mg
  "243670": {
    purpose: "Low-dose aspirin to prevent blood clots and reduce heart attack risk",
    notes: "Take at the same time each day. Take with food to reduce stomach irritation.",
    simpleNotes: "Take with food each day.",
  },
  // Nitroglycerin 0.4mg sublingual
  "315971": {
    purpose: "Emergency medication to relieve chest pain (angina)",
    notes: "Place 1 tablet under your tongue at onset of chest pain. May repeat every 5 minutes up to 3 times. If pain persists after 3 doses, call 911 immediately. Store in original dark bottle away from heat and light.",
    simpleNotes: "Put 1 tablet under your tongue when you have chest pain. If pain continues after 3 tablets, call 911.",
  },
  // Digoxin 0.125mg
  "197604": {
    purpose: "To help your heart beat more regularly and with better strength",
    notes: "Take at the same time each day. Report nausea, loss of appetite, vision changes (yellow/green tint), or irregular heartbeat to your doctor immediately.",
    simpleNotes: "Take at the same time every day. Call your doctor right away if you feel sick, have vision changes, or your heartbeat feels off.",
  },

  // ── Gastrointestinal medications ──────────────────────────────────────────

  // Omeprazole 20mg (PPI)
  "40790": {
    purpose: "To reduce stomach acid and protect your stomach lining",
    notes: "Take 30 minutes before your first meal of the day for best effect.",
    simpleNotes: "Take 30 minutes before breakfast.",
  },
  // Pantoprazole 40mg
  "114979": {
    purpose: "To reduce stomach acid",
    notes: "Take before meals. Swallow whole — do not crush or chew.",
    simpleNotes: "Take before eating. Swallow whole.",
  },
  // Ondansetron 4mg (anti-nausea)
  "312086": {
    purpose: "To prevent and treat nausea and vomiting",
    notes: "Let dissolve under tongue for orally disintegrating tablets. May cause headache or constipation.",
    simpleNotes: "Let melt under your tongue if using the dissolving tablet.",
  },

  // ── Other commonly discharged medications ─────────────────────────────────

  // Levothyroxine 50mcg (thyroid)
  "196429": {
    purpose: "To replace thyroid hormone your body needs",
    notes: "Take on an empty stomach 30–60 minutes before breakfast for best absorption. Do not take with calcium, iron, or antacids within 4 hours.",
    simpleNotes: "Take on an empty stomach in the morning, before eating.",
  },
  // Gabapentin 300mg
  "196961": {
    purpose: "To reduce nerve pain or help prevent seizures",
    notes: "May cause dizziness or drowsiness — do not drive until you know how it affects you. Do not stop suddenly.",
    simpleNotes: "May make you dizzy or sleepy. Do not drive until you know how it affects you.",
  },
  // Sertraline 50mg (Zoloft)
  "312938": {
    purpose: "To treat depression or anxiety",
    notes: "May take 2–4 weeks to feel full effects. Do not stop suddenly. Avoid alcohol.",
    simpleNotes: "Takes a few weeks to work. Do not stop suddenly without talking to your doctor.",
  },
};

// ── Drug class → generic purpose (fallback when specific RxNorm not found) ───

export interface DrugClassInstruction {
  purposeTemplate: string;  // Use {drugName} as placeholder
  notes?: string;
}

export const DRUG_CLASS_INSTRUCTIONS: Record<string, DrugClassInstruction> = {
  "antibiotic":          { purposeTemplate: "To treat your infection", notes: "Complete the full course even if you feel better." },
  "antihypertensive":    { purposeTemplate: "To lower your blood pressure", notes: "Take at the same time each day." },
  "statin":              { purposeTemplate: "To lower your cholesterol", notes: "Report muscle pain or weakness to your doctor." },
  "diuretic":            { purposeTemplate: "To help remove extra fluid from your body", notes: "Best taken in the morning." },
  "anticoagulant":       { purposeTemplate: "Blood thinner to prevent dangerous blood clots", notes: "Do not stop taking without your doctor's approval." },
  "antidiabetic":        { purposeTemplate: "To help control your blood sugar", notes: "Monitor blood sugar as directed." },
  "bronchodilator":      { purposeTemplate: "To help open your airways and make breathing easier" },
  "corticosteroid":      { purposeTemplate: "To reduce inflammation", notes: "Take with food. Follow the tapering schedule if provided." },
  "analgesic":           { purposeTemplate: "To relieve pain", notes: "Take only as directed." },
  "default":             { purposeTemplate: "As directed by your doctor", notes: "Ask your pharmacist if you have questions about this medication." },
};
