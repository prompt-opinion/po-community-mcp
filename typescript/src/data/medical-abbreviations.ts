/**
 * Patient-facing expansions for medical abbreviations.
 * The map value is the exact replacement string used in output.
 *
 * Lab tests  → "Full Name (ABBR)"  so patients can match it to their paperwork.
 * Clinical   → "full name (ABBR)"  so patients recognise the term they were given.
 * Shorthands → plain full word (no parenthetical needed).
 */
export const MEDICAL_ABBREVIATIONS: Record<string, string> = {
  // ── Lab tests ──────────────────────────────────────────────────────────────
  CBC: "Complete Blood Count (CBC)",
  BMP: "Basic Metabolic Panel (BMP)",
  BNP: "B-type Natriuretic Peptide (BNP)",
  HbA1c: "Hemoglobin A1c (HbA1c)",
  BUN: "Blood Urea Nitrogen (BUN)",
  INR: "Blood Clotting Level (INR)",

  // ── Clinical condition shorthands ─────────────────────────────────────────
  CHF: "heart failure (CHF)",
  AKI: "acute kidney injury (AKI)",
  MI: "heart attack (MI)",
  UTI: "urinary tract infection (UTI)",
  DVT: "deep vein thrombosis (DVT)",

  // ── Procedure shorthands ──────────────────────────────────────────────────
  cath: "catheterization",

  // ── Dosing frequency ──────────────────────────────────────────────────────
  BID: "twice daily (BID)",
  TID: "three times daily (TID)",
  QID: "four times daily (QID)",
  QD: "once daily",
  QDay: "once daily",
  PRN: "as needed (PRN)",
  HS: "at bedtime (HS)",
  AC: "before meals (AC)",
  PC: "after meals (PC)",
  STAT: "immediately",
  NPO: "nothing by mouth (NPO)",

  // ── Route of administration ───────────────────────────────────────────────
  PO: "by mouth (PO)",
  IV: "intravenously (IV)",
  SQ: "under the skin (subcutaneous)",
  SC: "under the skin (subcutaneous)",
  IM: "into the muscle (intramuscular)",
};
