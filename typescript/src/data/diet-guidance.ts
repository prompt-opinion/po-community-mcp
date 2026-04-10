/**
 * diet-guidance.ts
 * SNOMED condition code → plain-language dietary guidance for discharge instructions.
 * Used by GenerateDischargeInstructions to populate the diet section.
 *
 * Format: each entry is a single string of dietary guidance.
 * When a patient has multiple conditions, the first matching entry is used
 * (most clinically specific condition wins).
 */

export const DIET_GUIDANCE: Record<string, string> = {

  // ── Pneumonia (community acquired) ───────────────────────────────────────
  "233604007": "Eat small, nutritious meals to support recovery. Stay well hydrated — aim for 8 glasses of water per day. Protein-rich foods (chicken, eggs, legumes) help your immune system fight infection.",

  // ── Congestive heart failure / CHF exacerbation ───────────────────────────
  "84114007": "Limit sodium (salt) to less than 2,000 mg per day. Weigh yourself every morning — call your doctor if you gain more than 2 lbs in one day. Avoid canned soups, processed meats, and fast food.",

  // ── Type 2 diabetes mellitus ──────────────────────────────────────────────
  "44054006": "Follow a consistent diabetic diet — low sugar, low refined carbohydrates, and consistent meal times. Avoid sugary drinks. Work with a dietitian if available.",

  // ── Hypertension ──────────────────────────────────────────────────────────
  "38341003": "Follow a low-sodium, heart-healthy diet (DASH diet). Limit salt, processed foods, and alcohol. Eat plenty of fruits, vegetables, and whole grains.",

  // ── Acute kidney injury (AKI) ─────────────────────────────────────────────
  "14669001": "Limit salt and fluid intake as directed by your doctor. Avoid high-potassium foods (bananas, oranges, potatoes) unless your doctor says otherwise. Stay hydrated but do not overdrink.",

  // ── COPD ──────────────────────────────────────────────────────────────────
  "13645005": "Eat small, frequent meals — large meals can make breathing harder. Maintain a healthy weight; excess weight makes breathing more difficult. Choose easy-to-chew, nutrient-dense foods.",

  // ── Stroke / cerebrovascular disease ─────────────────────────────────────
  "230690007": "Follow a heart-healthy, low-sodium diet to reduce stroke recurrence risk. If you have swallowing difficulties, follow the swallowing precautions provided by your speech therapist.",

  // ── Myocardial infarction (heart attack) ─────────────────────────────────
  "22298006": "Follow a heart-healthy diet: limit saturated fat, trans fat, and sodium. Eat plenty of fruits, vegetables, whole grains, and lean proteins. Limit alcohol to no more than 1 drink per day.",

  // ── Fracture ──────────────────────────────────────────────────────────────
  "125605004": "Eat calcium-rich foods (dairy, leafy greens, fortified foods) and ensure adequate vitamin D to support bone healing. Maintain good overall nutrition.",

  // ── Sepsis / severe infection ─────────────────────────────────────────────
  "91302008": "Eat a high-protein diet to support immune function and recovery. Small, frequent meals are easier to manage if your appetite is poor. Stay hydrated.",

  // ── Pulmonary embolism (PE) ───────────────────────────────────────────────
  "59282003": "Maintain consistent vitamin K intake if you are on warfarin (avoid large changes in green vegetables). Stay well hydrated. Limit alcohol.",

  // ── Deep vein thrombosis (DVT) ────────────────────────────────────────────
  "128053003": "Stay well hydrated throughout the day. If on warfarin, keep your vitamin K intake consistent. Avoid alcohol.",

  // ── Urinary tract infection (UTI) ────────────────────────────────────────
  "68566005": "Drink at least 8 glasses of water per day. Avoid caffeine and alcohol during treatment, as they can irritate the bladder. Unsweetened cranberry juice may help.",

  // ── Atrial fibrillation (AFib) ────────────────────────────────────────────
  "49436004": "Follow a heart-healthy diet. If on warfarin, maintain consistent vitamin K intake — eat similar amounts of green leafy vegetables each day. Limit alcohol and caffeine.",

  // ── Asthma ────────────────────────────────────────────────────────────────
  "195967001": "No specific dietary restrictions. Some people find that sulfite-containing foods (wine, dried fruit, shrimp) can trigger asthma — monitor for triggers and avoid them.",

  // ── Gastrointestinal bleed ────────────────────────────────────────────────
  "74474003": "Avoid alcohol and NSAIDs (ibuprofen, naproxen). Eat soft, easily digestible foods initially. Avoid spicy, acidic, or fatty foods until follow-up confirms healing.",

  // ── Cellulitis / soft tissue infection ───────────────────────────────────
  "128045006": "Eat a balanced diet with adequate protein to support skin healing. Stay hydrated. No specific dietary restrictions beyond general healthy eating.",

  // ── Surgical wound / post-operative ──────────────────────────────────────
  "387713003": "Eat a high-protein diet to support wound healing (eggs, chicken, fish, legumes). Vitamin C-rich foods (citrus, berries, broccoli) promote collagen formation. Avoid alcohol during recovery.",

  // ── Default (any unrecognized condition) ─────────────────────────────────
  "default": "Eat a balanced diet. Stay hydrated. Avoid alcohol during recovery.",
};
