/**
 * charlson-mapping.ts
 * SNOMED condition code → Charlson Comorbidity Index category and point value.
 * Used by Tool 3 (AssessReadmissionRisk) for LACE "C" component scoring.
 *
 * Charlson Comorbidity Index (CCI):
 *   - Sum all applicable points
 *   - Cap the total at 5 for LACE scoring purposes
 *   - Score 0 → LACE C = 0 pts, 1 → 1 pt, 2 → 2 pts, 3 → 3 pts, 4+ → 5 pts
 *
 * References:
 *   - Charlson ME et al. J Chronic Dis. 1987;40(5):373-83
 *   - LACE index: van Walraven C et al. CMAJ. 2010;182(6):551-7
 */

export interface CharlsonEntry {
  category: string;
  points: number;
  notes?: string;
}

/**
 * Primary SNOMED mappings for Charlson categories.
 * These are the most common codes used in modern EHR systems.
 *
 * NOTE on SNOMED code 73211009 ("Diabetes mellitus"):
 *   This code maps ONLY to the 2-point "with end-organ damage" category.
 *   Code 44054006 is used for uncomplicated type 2 diabetes (1 point).
 *   If a patient has both 44054006 and any complication code (e.g. 368581000119106),
 *   the scoring logic in AssessReadmissionRisk should take the higher value (2 pts),
 *   not sum them.
 */
export const CHARLSON_MAP: Record<string, CharlsonEntry> = {

  // ── 1-point conditions ─────────────────────────────────────────────────

  // Myocardial infarction
  "22298006":  { category: "Myocardial infarction", points: 1 },
  "1755008":   { category: "Myocardial infarction", points: 1, notes: "Old MI" },

  // Congestive heart failure
  "84114007":  { category: "Congestive heart failure", points: 1 },
  "88805009":  { category: "Congestive heart failure", points: 1, notes: "Chronic CHF" },
  "42343007":  { category: "Congestive heart failure", points: 1, notes: "Congestive heart disease" },

  // Peripheral vascular disease
  "399957001": { category: "Peripheral vascular disease", points: 1 },
  "400047006": { category: "Peripheral vascular disease", points: 1, notes: "Peripheral arterial occlusive disease" },
  "233985008": { category: "Peripheral vascular disease", points: 1, notes: "Ischemic peripheral vascular disease" },

  // Cerebrovascular disease
  "230690007": { category: "Cerebrovascular disease", points: 1 },
  "422504002": { category: "Cerebrovascular disease", points: 1, notes: "Ischemic stroke" },
  "266257000": { category: "Cerebrovascular disease", points: 1, notes: "TIA" },
  "230614007": { category: "Cerebrovascular disease", points: 1, notes: "Cerebral infarction" },

  // Dementia
  "52448006":  { category: "Dementia", points: 1 },
  "26929004":  { category: "Dementia", points: 1, notes: "Alzheimer's disease" },
  "230258005": { category: "Dementia", points: 1, notes: "Vascular dementia" },

  // Chronic pulmonary disease (COPD, asthma if severe/chronic)
  "13645005":  { category: "Chronic pulmonary disease", points: 1, notes: "COPD" },
  "195967001": { category: "Chronic pulmonary disease", points: 1, notes: "Asthma (chronic)" },
  "68505006":  { category: "Chronic pulmonary disease", points: 1, notes: "Chronic pulmonary disease" },

  // Rheumatic disease (rheumatoid arthritis, lupus, etc.)
  "69896004":  { category: "Rheumatic disease", points: 1, notes: "Rheumatoid arthritis" },
  "55464009":  { category: "Rheumatic disease", points: 1, notes: "Systemic lupus erythematosus" },
  "24693007":  { category: "Rheumatic disease", points: 1, notes: "Polymyalgia rheumatica" },

  // Peptic ulcer disease
  "13200003":  { category: "Peptic ulcer disease", points: 1 },
  "40845000":  { category: "Peptic ulcer disease", points: 1, notes: "Gastric ulcer" },
  "51868009":  { category: "Peptic ulcer disease", points: 1, notes: "Duodenal ulcer" },

  // Mild liver disease
  "197480006": { category: "Mild liver disease", points: 1, notes: "Chronic hepatitis" },
  "235878007": { category: "Mild liver disease", points: 1, notes: "Chronic viral hepatitis" },
  "61977001":  { category: "Mild liver disease", points: 1, notes: "Chronic liver disease" },

  // Diabetes mellitus (uncomplicated) — code 44054006 only
  // 73211009 is intentionally excluded here; it maps to the 2-point complications entry below.
  "44054006":  { category: "Diabetes mellitus (uncomplicated)", points: 1 },

  // Hemiplegia / paraplegia
  "50582007":  { category: "Hemiplegia or hemiparesis", points: 2 },
  "60454009":  { category: "Hemiplegia or hemiparesis", points: 2, notes: "Paraplegia" },

  // ── 2-point conditions ─────────────────────────────────────────────────

  // Diabetes with end-organ damage (complications)
  // 73211009 maps here (2 pts). Do NOT add it to the uncomplicated section above.
  "73211009":          { category: "Diabetes mellitus with end-organ damage", points: 2, notes: "Diabetes with complications" },
  "368581000119106":   { category: "Diabetes mellitus with end-organ damage", points: 2, notes: "Diabetic nephropathy" },
  "127013003":         { category: "Diabetes mellitus with end-organ damage", points: 2, notes: "Diabetic retinopathy" },
  "230572002":         { category: "Diabetes mellitus with end-organ damage", points: 2, notes: "Diabetic neuropathy" },

  // Moderate or severe renal disease
  "431855005":         { category: "Moderate or severe renal disease", points: 2 },
  "709044004":         { category: "Moderate or severe renal disease", points: 2, notes: "Chronic kidney disease stage 3+" },
  "285811000119108":   { category: "Moderate or severe renal disease", points: 2, notes: "CKD stage 4" },
  "433146000":         { category: "Moderate or severe renal disease", points: 2, notes: "CKD stage 5 / ESRD" },

  // Any malignancy (non-metastatic)
  "363346000": { category: "Any malignancy", points: 2 },
  "372087000": { category: "Any malignancy", points: 2, notes: "Malignant neoplasm" },
  "363418001": { category: "Any malignancy", points: 2, notes: "Malignant tumor of lung" },
  "363443007": { category: "Any malignancy", points: 2, notes: "Malignant tumor of colon" },
  "254837009": { category: "Any malignancy", points: 2, notes: "Malignant tumor of breast" },
  "399068003": { category: "Any malignancy", points: 2, notes: "Malignant tumor of prostate" },

  // Moderate or severe liver disease
  "19943007":  { category: "Moderate or severe liver disease", points: 3, notes: "Cirrhosis" },
  "57773001":  { category: "Moderate or severe liver disease", points: 3, notes: "Portal hypertension" },
  "32916005":  { category: "Moderate or severe liver disease", points: 3, notes: "Hepatic encephalopathy" },

  // ── 6-point conditions ─────────────────────────────────────────────────

  // Metastatic solid tumor
  "94222008":  { category: "Metastatic solid tumor", points: 6 },
  "128462008": { category: "Metastatic solid tumor", points: 6, notes: "Secondary malignant neoplasm" },
  "315004001": { category: "Metastatic solid tumor", points: 6, notes: "Metastatic malignant neoplasm" },

  // AIDS / HIV disease
  "62479008":  { category: "AIDS", points: 6 },
  "86406008":  { category: "AIDS", points: 6, notes: "HIV infection (symptomatic)" },
};

/**
 * Maps a LACE C raw Charlson sum to the points used in the LACE score.
 * LACE C is capped at 5.
 */
export function charlsonSumToLaceC(charlsonSum: number): number {
  if (charlsonSum === 0) return 0;
  if (charlsonSum === 1) return 1;
  if (charlsonSum === 2) return 2;
  if (charlsonSum === 3) return 3;
  return 5; // 4 or more → 5 points
}

/**
 * Extracts the primary SNOMED code from a FHIR CodeableConcept.
 * Returns undefined if no SNOMED code is found.
 */
export function getSnomedCode(coding?: Array<{ system?: string; code: string }>): string | undefined {
  return coding?.find(c => c.system?.includes("snomed"))?.code;
}
