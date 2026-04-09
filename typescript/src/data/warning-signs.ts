/**
 * warning-signs.ts
 * SNOMED condition code → plain-language warning signs for discharge instructions.
 * Used by Tool 2 (GenerateDischargeInstructions).
 * 
 * Format: each entry is an array of strings — first item is the header, rest are bullet points.
 */

export const WARNING_SIGNS: Record<string, string[]> = {

  // ── Pneumonia (community acquired) ───────────────────────────────────────
  "233604007": [
    "Return to the ER immediately if you have any of these:",
    "- Fever above 101°F (38.3°C)",
    "- Increasing difficulty breathing or shortness of breath at rest",
    "- Chest pain that worsens with breathing",
    "- Coughing up blood or rust-colored mucus",
    "- Confusion or difficulty staying awake",
    "- Blue tint to lips or fingernails",
  ],

  // ── Congestive heart failure / CHF exacerbation ───────────────────────────
  "84114007": [
    "Return to the ER immediately if you have any of these:",
    "- Sudden weight gain of more than 2 lbs (1 kg) in one day or 5 lbs (2.3 kg) in one week",
    "- Increasing swelling in your legs, ankles, or feet",
    "- Shortness of breath at rest or when lying flat",
    "- New or worsening cough (especially at night)",
    "- Chest pain or pressure",
    "- Feeling faint or dizzy",
  ],

  // ── Type 2 diabetes mellitus ──────────────────────────────────────────────
  "44054006": [
    "Return to the ER immediately if you have any of these:",
    "- Blood sugar above 300 mg/dL or below 70 mg/dL",
    "- Severe nausea, vomiting, or stomach pain",
    "- Fruity-smelling breath",
    "- Extreme thirst or urination",
    "- Confusion, shakiness, or sweating that does not improve with food",
  ],

  // ── Hypertension ──────────────────────────────────────────────────────────
  "38341003": [
    "Return to the ER immediately if you have any of these:",
    "- Severe headache (worst of your life)",
    "- Sudden vision changes or blurred vision",
    "- Chest pain or shortness of breath",
    "- Sudden numbness or weakness on one side of your body",
    "- Difficulty speaking or understanding speech",
    "- Blood pressure above 180/120 mmHg",
  ],

  // ── Acute kidney injury (AKI) ─────────────────────────────────────────────
  // Removed "Confusion or difficulty concentrating" per clinical review (too non-specific).
  "14669001": [
    "Return to the ER immediately if you have any of these:",
    "- Significantly decreased urine output (much less than normal)",
    "- Swelling in your legs, ankles, or face",
    "- Severe nausea or vomiting",
    "- Chest pain or difficulty breathing",
  ],

  // ── COPD ──────────────────────────────────────────────────────────────────
  "13645005": [
    "Return to the ER immediately if you have any of these:",
    "- Shortness of breath that is worse than usual and does not improve with your inhaler",
    "- Coughing up more mucus than usual, especially if it is green, yellow, or blood-tinged",
    "- Fever above 101°F (38.3°C)",
    "- Confusion or difficulty staying awake",
    "- Blue tint to lips or fingernails",
  ],

  // ── Stroke / cerebrovascular disease ─────────────────────────────────────
  "230690007": [
    "Return to the ER immediately — call 911 — if you have any of these:",
    "- Sudden numbness or weakness of face, arm, or leg, especially on one side",
    "- Sudden confusion or trouble speaking or understanding",
    "- Sudden trouble seeing in one or both eyes",
    "- Sudden severe headache with no known cause",
    "- Sudden dizziness, loss of balance, or trouble walking",
  ],

  // ── Myocardial infarction (heart attack) ─────────────────────────────────
  // Added stomach/abdominal pain — common atypical presentation, especially in women.
  "22298006": [
    "Return to the ER immediately — call 911 — if you have any of these:",
    "- Chest pain, pressure, squeezing, or tightness",
    "- Pain spreading to arm, shoulder, neck, jaw, back, or stomach",
    "- Shortness of breath",
    "- Cold sweat, nausea, or lightheadedness",
    "- Palpitations or irregular heartbeat",
  ],

  // ── Fracture ──────────────────────────────────────────────────────────────
  "125605004": [
    "Return to the ER immediately if you have any of these:",
    "- Increased pain, swelling, or bruising at the fracture site",
    "- Numbness, tingling, or weakness in the affected limb",
    "- Fingers or toes that are cold, pale, or blue (near the fracture)",
    "- Signs of infection: fever, warmth, redness, or pus at any wound site",
    "- Cast or splint feels too tight or is causing pain",
  ],

  // ── Sepsis / severe infection ─────────────────────────────────────────────
  "91302008": [
    "Return to the ER immediately if you have any of these:",
    "- Fever above 101°F (38.3°C) or temperature below 96.8°F (36°C)",
    "- Rapid heart rate or rapid breathing",
    "- Confusion or difficulty staying alert",
    "- Feeling very unwell, weak, or extremely tired",
    "- Signs of worsening infection: increased redness, swelling, or warmth",
  ],

  // ── Pulmonary embolism (PE) ───────────────────────────────────────────────
  "59282003": [
    "Return to the ER immediately — call 911 — if you have any of these:",
    "- Sudden shortness of breath",
    "- Chest pain, especially when breathing deeply",
    "- Coughing up blood",
    "- Rapid or irregular heartbeat",
    "- Lightheadedness or fainting",
  ],

  // ── Deep vein thrombosis (DVT) ────────────────────────────────────────────
  "128053003": [
    "Return to the ER immediately if you have any of these:",
    "- Sudden shortness of breath or chest pain (may indicate clot moved to lungs)",
    "- New or worsening leg pain, swelling, or redness",
    "- Leg that feels warm to the touch and looks red or discolored",
  ],

  // ── Urinary tract infection (UTI) ────────────────────────────────────────
  "68566005": [
    "Contact your doctor if you have any of these:",
    "- Fever above 101°F (38.3°C)",
    "- Back or side pain (flank pain) that is new or worsening",
    "- Nausea or vomiting",
    "- Symptoms not improving after 48 hours of antibiotics",
    "Return to the ER immediately if:",
    "- You have confusion or difficulty staying alert",
    "- You are unable to keep fluids or medications down",
  ],

  // ── Atrial fibrillation (AFib) ────────────────────────────────────────────
  "49436004": [
    "Return to the ER immediately if you have any of these:",
    "- Chest pain or pressure",
    "- Shortness of breath at rest",
    "- Fainting or near-fainting",
    "- Rapid, irregular heartbeat that does not resolve",
    "- Sudden weakness, numbness, or trouble speaking (signs of stroke)",
  ],

  // ── Asthma ────────────────────────────────────────────────────────────────
  "195967001": [
    "Return to the ER immediately if you have any of these:",
    "- Shortness of breath that does not improve with your rescue inhaler",
    "- Wheezing that is getting worse",
    "- Inability to speak in full sentences due to shortness of breath",
    "- Blue tint to lips or fingernails",
    "- Using your rescue inhaler more than every 4 hours",
  ],

  // ── Gastrointestinal bleed ────────────────────────────────────────────────
  "74474003": [
    "Return to the ER immediately if you have any of these:",
    "- Vomiting blood or material that looks like coffee grounds",
    "- Black, tarry, or bloody stools",
    "- Severe stomach pain",
    "- Feeling faint, dizzy, or lightheaded",
    "- Rapid or pounding heartbeat",
  ],

  // ── Cellulitis / soft tissue infection ───────────────────────────────────
  "128045006": [
    "Return to the ER immediately if you have any of these:",
    "- Red area spreading beyond the marked border",
    "- Fever above 101°F (38.3°C)",
    "- Pus or discharge from the affected area",
    "- Rapid worsening of pain, swelling, or redness",
    "- Red streaks spreading from the infected area",
  ],

  // ── Surgical wound / post-operative ──────────────────────────────────────
  "387713003": [
    "Contact your surgeon immediately if you have any of these:",
    "- Fever above 101°F (38.3°C)",
    "- Increased redness, warmth, or swelling around your incision",
    "- Drainage that is green, yellow, or has a foul odor",
    "- The wound edges separating or opening",
    "- Severe pain that is not controlled by prescribed medication",
    "Return to the ER immediately if:",
    "- You have signs of severe infection: high fever, confusion, rapid heartbeat",
    "- You have heavy bleeding from your wound",
  ],

  // ── Default (any unrecognized condition) ─────────────────────────────────
  "default": [
    "Contact your doctor right away if:",
    "- Your symptoms return or get worse",
    "- You develop a fever above 101°F (38.3°C)",
    "- You have new pain, swelling, or changes you are worried about",
    "Return to the ER immediately if:",
    "- You feel very unwell or your condition is rapidly getting worse",
    "- You have chest pain, shortness of breath, or confusion",
  ],
};
