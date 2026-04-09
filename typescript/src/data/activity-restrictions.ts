/**
 * activity-restrictions.ts
 * SNOMED condition code → plain-language activity restrictions for discharge instructions.
 * Used by GenerateDischargeInstructions to populate the activity section.
 *
 * Format: each entry is an array of instruction strings.
 * Reading level does not affect these entries — activity safety guidance is constant.
 */

export const ACTIVITY_RESTRICTIONS: Record<string, string[]> = {

  // ── Pneumonia (community acquired) ───────────────────────────────────────
  "233604007": [
    "Rest as much as you need — fatigue is normal during recovery",
    "Short walks are encouraged; increase distance gradually each day",
    "Avoid strenuous activity until your doctor clears you",
  ],

  // ── Congestive heart failure / CHF exacerbation ───────────────────────────
  "84114007": [
    "Limit activity to what you can do without shortness of breath",
    "Avoid lifting anything heavier than 10 lbs",
    "Rest between activities; plan for rest periods throughout your day",
  ],

  // ── Type 2 diabetes mellitus ──────────────────────────────────────────────
  "44054006": [
    "Regular light activity such as walking is encouraged and helps control blood sugar",
    "Avoid exercising when blood sugar is below 100 mg/dL or above 250 mg/dL",
    "Carry a fast-acting sugar source when exercising",
  ],

  // ── Hypertension ──────────────────────────────────────────────────────────
  "38341003": [
    "Light to moderate exercise is beneficial — walking, swimming, or cycling",
    "Avoid heavy lifting or straining",
    "Monitor your blood pressure before and after activity",
  ],

  // ── Acute kidney injury (AKI) ─────────────────────────────────────────────
  "14669001": [
    "Rest and avoid strenuous physical activity until your kidney function is confirmed improved",
    "Gentle walking is fine; do not push through fatigue",
  ],

  // ── COPD ──────────────────────────────────────────────────────────────────
  "13645005": [
    "Pace your activities — stop to rest if you become short of breath",
    "Avoid outdoor exercise on high-pollution or cold days",
    "Pursed-lip breathing can help during activity",
  ],

  // ── Stroke / cerebrovascular disease ─────────────────────────────────────
  "230690007": [
    "Follow your physical therapist's instructions exactly",
    "Do not drive until your doctor clears you",
    "Use assistive devices as recommended to prevent falls",
  ],

  // ── Myocardial infarction (heart attack) ─────────────────────────────────
  "22298006": [
    "Gradually increase activity as tolerated — start with short walks",
    "Avoid lifting more than 10 lbs for the first 4–6 weeks",
    "Do not drive for at least 1 week or until cleared by your cardiologist",
    "Cardiac rehabilitation is strongly recommended — ask your doctor for a referral",
  ],

  // ── Fracture ──────────────────────────────────────────────────────────────
  "125605004": [
    "Follow all weight-bearing restrictions given to you at discharge",
    "Keep the injured area elevated when possible to reduce swelling",
    "Do not remove or adjust your cast or splint without your doctor's guidance",
  ],

  // ── Sepsis / severe infection ─────────────────────────────────────────────
  "91302008": [
    "Rest completely during early recovery — your body needs energy to heal",
    "Light activity such as walking around the house is fine when you feel able",
    "Avoid returning to work or strenuous activity until your doctor approves",
  ],

  // ── Pulmonary embolism (PE) ───────────────────────────────────────────────
  "59282003": [
    "Light activity such as short walks is encouraged to improve circulation",
    "Avoid prolonged sitting or bed rest — move around every hour",
    "Do not engage in strenuous exercise until your doctor clears you",
  ],

  // ── Deep vein thrombosis (DVT) ────────────────────────────────────────────
  "128053003": [
    "Keep your affected leg elevated above heart level when sitting or lying down",
    "Walk regularly — short, frequent walks help prevent new clots",
    "Avoid long periods of sitting, especially with legs dangling",
  ],

  // ── Urinary tract infection (UTI) ────────────────────────────────────────
  "68566005": [
    "No specific activity restrictions — rest if you feel unwell",
    "Drink plenty of fluids throughout the day",
  ],

  // ── Atrial fibrillation (AFib) ────────────────────────────────────────────
  "49436004": [
    "Avoid strenuous exercise until your heart rate is well controlled",
    "Light activity such as walking is generally safe and encouraged",
    "Do not drive if you feel lightheaded or have recently fainted",
  ],

  // ── Asthma ────────────────────────────────────────────────────────────────
  "195967001": [
    "Carry your rescue inhaler whenever you exercise",
    "Warm up gradually before exercise and cool down slowly",
    "Avoid exercise in cold, dry air or when pollen counts are high",
  ],

  // ── Gastrointestinal bleed ────────────────────────────────────────────────
  "74474003": [
    "Rest and avoid strenuous activity until bleeding is confirmed resolved",
    "No heavy lifting for at least 2 weeks",
  ],

  // ── Cellulitis / soft tissue infection ───────────────────────────────────
  "128045006": [
    "Elevate the affected limb as much as possible to reduce swelling",
    "Avoid activities that cause trauma to the affected area",
    "Light activity is fine — do not stay in bed if you feel well enough to walk",
  ],

  // ── Surgical wound / post-operative ──────────────────────────────────────
  "387713003": [
    "Follow your surgeon's specific activity restrictions",
    "Avoid lifting anything heavier than your surgeon specified (often 10–15 lbs)",
    "No swimming, hot tubs, or submerging your wound until cleared by your surgeon",
  ],

  // ── Default (any unrecognized condition) ─────────────────────────────────
  "default": [
    "Resume normal activities gradually as you feel better",
  ],
};
