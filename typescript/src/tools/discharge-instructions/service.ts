import { differenceInDays, differenceInYears, format, isValid, parseISO } from "date-fns";
import { fhirR4 } from "@smile-cdr/fhirts";
import {
  DischargeInstructionsInput,
  DischargeInstructionsResult,
  MedicationInstruction,
  ReadingLevel,
} from "./types";
import {
  ACTIVITY_RESTRICTIONS,
  DIET_GUIDANCE,
  DRUG_CLASS_INSTRUCTIONS,
  MED_INSTRUCTIONS,
  RXNORM_TO_DRUG_CLASS,
  WARNING_SIGNS,
} from "../../data";

// ── Private helpers ───────────────────────────────────────────────────────────

function toDate(value: string | Date): Date | null {
  if (value instanceof Date) return isValid(value) ? value : null;
  const parsed = parseISO(value);
  return isValid(parsed) ? parsed : null;
}

function formatPatientName(patient: fhirR4.Patient): string {
  const name = patient.name?.[0];
  if (!name) return "the patient";
  const given = name.given?.join(" ") ?? "";
  const family = name.family ?? "";
  return [given, family].filter(Boolean).join(" ") || "the patient";
}

function extractSnomedCodes(conditions: fhirR4.Condition[]): string[] {
  return conditions.flatMap(
    (c) =>
      c.code?.coding
        ?.filter((coding) => coding.system === "http://snomed.info/sct" && coding.code)
        .map((coding) => coding.code as string) ?? [],
  );
}

// ── Section builders ──────────────────────────────────────────────────────────

function buildVisitSummary(
  patient: fhirR4.Patient,
  encounter: fhirR4.Encounter,
  conditions: fhirR4.Condition[],
  procedures: fhirR4.Procedure[],
  level: ReadingLevel,
): string {
  const name = formatPatientName(patient);
  const birthDate = patient.birthDate ? toDate(patient.birthDate) : null;
  const age = birthDate ? differenceInYears(new Date(), birthDate) : null;

  const admitDate = encounter.period?.start ? toDate(encounter.period.start) : null;
  const dischargeDate = (encounter.period?.end ? toDate(encounter.period.end) : null) ?? new Date();
  const los = admitDate ? differenceInDays(dischargeDate, admitDate) : null;

  const conditionNames = conditions
    .map((c) => c.code?.text ?? c.code?.coding?.[0]?.display ?? "")
    .filter(Boolean);
  const procedureNames = procedures
    .map((p) => p.code?.text ?? p.code?.coding?.[0]?.display ?? "")
    .filter(Boolean);

  if (level === "simple") {
    const parts = [`${name} was in the hospital`];
    if (los !== null) parts.push(`for ${los} day${los !== 1 ? "s" : ""}`);
    if (conditionNames.length === 1) {
      parts.push(`for ${conditionNames[0]}`);
    } else if (conditionNames.length > 1) {
      const last = conditionNames[conditionNames.length - 1];
      const rest = conditionNames.slice(0, -1);
      parts.push(`for ${rest.join(", ")} and ${last}`);
    }
    return parts.join(" ") + ".";
  }

  if (level === "standard") {
    const agePart = age !== null ? `, ${age} years old,` : "";
    const losPart = admitDate
      ? `admitted on ${format(admitDate, "MMMM d, yyyy")}`
      : "recently admitted";
    const condPart =
      conditionNames.length > 0 ? `Conditions treated: ${conditionNames.join(", ")}.` : "";
    const procPart =
      procedureNames.length > 0 ? ` Procedures performed: ${procedureNames.join(", ")}.` : "";
    return (
      `${name}${agePart} was ${losPart} and is being discharged today. ` +
      condPart +
      procPart +
      " Please follow all instructions in this document carefully."
    );
  }

  // detailed
  const lines = [
    `Patient: ${age !== null ? `${age}-year-old ` : ""}${name}`,
    admitDate ? `Admission date: ${format(admitDate, "MMMM d, yyyy")}` : "",
    `Discharge date: ${format(dischargeDate, "MMMM d, yyyy")}`,
    los !== null ? `Length of stay: ${los} day${los !== 1 ? "s" : ""}` : "",
    conditionNames.length > 0 ? `Active diagnoses: ${conditionNames.join("; ")}.` : "",
    procedureNames.length > 0
      ? `Procedures performed during admission: ${procedureNames.join("; ")}.`
      : "",
  ];
  return lines.filter(Boolean).join("\n");
}

function buildMedicationInstructions(
  medicationRequests: fhirR4.MedicationRequest[],
  level: ReadingLevel,
): MedicationInstruction[] {
  return medicationRequests.map((req) => {
    const coding = req.medicationCodeableConcept?.coding ?? [];
    const rxNormCoding = coding.find(
      (c) => c.system === "http://www.nlm.nih.gov/research/umls/rxnorm",
    );
    const rxNormCode = rxNormCoding?.code ?? "";
    const medName =
      req.medicationCodeableConcept?.text ??
      rxNormCoding?.display ??
      coding[0]?.display ??
      "Unknown medication";

    const instruction = rxNormCode ? MED_INSTRUCTIONS[rxNormCode] : undefined;
    const drugClass = !instruction && rxNormCode ? RXNORM_TO_DRUG_CLASS[rxNormCode] : undefined;
    const classInstruction = drugClass ? DRUG_CLASS_INSTRUCTIONS[drugClass] : undefined;

    const purpose = instruction?.purpose
      ?? classInstruction?.purposeTemplate
      ?? "As directed by your doctor";
    const defaultNotes = "Ask your pharmacist if you have questions about this medication.";
    const notes = instruction
      ? (level === "simple"
          ? (instruction.simpleNotes ?? instruction.notes ?? defaultNotes)
          : (instruction.notes ?? defaultNotes))
      : (classInstruction?.notes ?? defaultNotes);

    const dosageInstruction = req.dosageInstruction?.[0];
    const doseQuantity = dosageInstruction?.doseAndRate?.[0]?.doseQuantity;
    const dosage = doseQuantity
      ? `${doseQuantity.value ?? ""} ${doseQuantity.unit ?? ""}`.trim()
      : (dosageInstruction?.text ?? "As directed");

    const repeat = dosageInstruction?.timing?.repeat;
    const frequency =
      repeat?.frequency && repeat?.period && repeat?.periodUnit
        ? `${repeat.frequency} time(s) per ${repeat.period} ${repeat.periodUnit}`
        : (dosageInstruction?.timing?.code?.text ?? "As directed");

    return {
      name: medName,
      dosage,
      frequency,
      instructions: [purpose, notes].filter(Boolean).join(". "),
    };
  });
}

function buildWarningSigns(conditions: fhirR4.Condition[]): string[] {
  const codes = extractSnomedCodes(conditions);
  const defaultSigns = WARNING_SIGNS["default"] ?? [];
  const seen = new Set<string>();
  const lines: string[] = [];

  const addLines = (entries: string[]) => {
    for (const line of entries) {
      if (!seen.has(line)) {
        seen.add(line);
        lines.push(line);
      }
    }
  };

  if (codes.length === 0) {
    addLines(defaultSigns);
    return lines;
  }

  for (const code of codes) {
    addLines(WARNING_SIGNS[code] ?? defaultSigns);
  }
  return lines;
}

function buildActivityRestrictions(conditions: fhirR4.Condition[]): string[] {
  const codes = extractSnomedCodes(conditions);
  const defaultActivity = ACTIVITY_RESTRICTIONS["default"] ?? [];
  const seen = new Set<string>();
  const lines: string[] = [];

  if (codes.length === 0) return defaultActivity;

  for (const code of codes) {
    for (const line of ACTIVITY_RESTRICTIONS[code] ?? defaultActivity) {
      if (!seen.has(line)) {
        seen.add(line);
        lines.push(line);
      }
    }
  }
  return lines;
}

function buildDietGuidance(conditions: fhirR4.Condition[]): string {
  const codes = extractSnomedCodes(conditions);
  const defaultDiet = DIET_GUIDANCE["default"] ?? "Eat a balanced diet. Stay hydrated.";

  for (const code of codes) {
    const guidance = DIET_GUIDANCE[code];
    if (guidance) return guidance;
  }
  return defaultDiet;
}

// ── Main export ───────────────────────────────────────────────────────────────

export function generateDischargeInstructions(
  input: DischargeInstructionsInput,
): DischargeInstructionsResult {
  const { readingLevel, patient, encounter, procedures } = input;

  const conditions = input.conditions.filter((c) =>
    c.clinicalStatus?.coding?.some((coding) => coding.code === "active"),
  );
  const medicationRequests = input.medicationRequests.filter(
    (m) => m.status === "active",
  );

  return {
    visitSummary: buildVisitSummary(patient, encounter, conditions, procedures, readingLevel),
    medications: buildMedicationInstructions(medicationRequests, readingLevel),
    warningSigns: buildWarningSigns(conditions),
    activityRestrictions: buildActivityRestrictions(conditions),
    dietGuidance: buildDietGuidance(conditions),
  };
}
