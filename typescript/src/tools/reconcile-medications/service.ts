import { fhirR4 } from "@smile-cdr/fhirts";
import { DRUG_INTERACTIONS } from "../../data/drug-interactions";
import { MEDICAL_ABBREVIATIONS } from "../../data/medical-abbreviations";
import {
  ReconcileMedicationsInput,
  ReconcileMedicationsOutput,
  MedicationEntry,
  StoppedMedicationEntry,
  ChangedMedicationEntry,
  BasicMedicationEntry,
  InteractionWarning,
  AllergyConflict,
} from "./types";

const RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm";

const ABBREVIATION_REGEX = new RegExp(
  `\\b(${Object.keys(MEDICAL_ABBREVIATIONS)
    .map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|")})\\b`,
  "g",
);

function expandText(text: string): string {
  ABBREVIATION_REGEX.lastIndex = 0;
  return text.replace(
    ABBREVIATION_REGEX,
    (match) => MEDICAL_ABBREVIATIONS[match] ?? match,
  );
}

function toDateString(value: string | Date | undefined): string | undefined {
  if (value === undefined) return undefined;
  if (value instanceof Date) return value.toISOString();
  return value;
}

function toDateOnly(value: string | Date | undefined): string | undefined {
  const str = toDateString(value);
  return str?.slice(0, 10);
}

function extractRxNorm(
  med: fhirR4.MedicationRequest,
): string | undefined {
  return med.medicationCodeableConcept?.coding?.find(
    (c) => c.system === RXNORM_SYSTEM,
  )?.code;
}

function extractDisplayName(med: fhirR4.MedicationRequest): string {
  return (
    med.medicationCodeableConcept?.text ??
    med.medicationCodeableConcept?.coding?.[0]?.display ??
    "Unknown medication"
  );
}

function extractDosage(med: fhirR4.MedicationRequest): string | undefined {
  return med.dosageInstruction?.[0]?.text ?? undefined;
}

function isActive(med: fhirR4.MedicationRequest): boolean {
  return med.status === "active";
}

function isStopped(med: fhirR4.MedicationRequest): boolean {
  return med.status === "stopped" || med.status === "cancelled";
}

export function reconcileMedications(
  input: ReconcileMedicationsInput,
): ReconcileMedicationsOutput {
  const { encounter, medicationRequests, allergyIntolerances } = input;

  const periodStart = encounter.period?.start;
  if (!periodStart) {
    throw new Error("FHIR_RESOURCE_NOT_FOUND");
  }

  const admissionDate = new Date(toDateString(periodStart) ?? periodStart);
  const encounterDate = toDateOnly(periodStart) ?? "";

  const interactionWarnings: InteractionWarning[] = [];
  const allergyConflicts: AllergyConflict[] = [];

  const preAdmission: fhirR4.MedicationRequest[] = [];
  const duringAdmission: fhirR4.MedicationRequest[] = [];
  const skippedIds = new Set<string>();

  for (const med of medicationRequests) {
    const rxnorm = extractRxNorm(med);
    if (!rxnorm) {
      interactionWarnings.push({
        medications: [extractDisplayName(med)],
        severity: "unknown",
        note: "Unknown medication — manual review required",
      });
      skippedIds.add(med.id ?? "");
      continue;
    }

    const authoredOnStr = toDateString(med.authoredOn);
    const authoredOn = authoredOnStr ? new Date(authoredOnStr) : null;
    if (authoredOn && authoredOn < admissionDate) {
      preAdmission.push(med);
    } else {
      duringAdmission.push(med);
    }
  }

  const preAdmissionByRxNorm = new Map<string, fhirR4.MedicationRequest>();
  for (const med of preAdmission) {
    const code = extractRxNorm(med);
    if (code) preAdmissionByRxNorm.set(code, med);
  }

  const changedRxNorms = new Set<string>();
  const newMeds: MedicationEntry[] = [];
  const stoppedMeds: StoppedMedicationEntry[] = [];
  const changedMeds: ChangedMedicationEntry[] = [];
  const continuedMeds: BasicMedicationEntry[] = [];

  for (const med of duringAdmission) {
    const rxnorm = extractRxNorm(med);
    if (!rxnorm) continue;

    const preMed = preAdmissionByRxNorm.get(rxnorm);

    if (isStopped(med)) {
      if (preMed) {
        stoppedMeds.push({
          medication: extractDisplayName(med),
          rxnorm,
          stoppedOn: toDateOnly(med.authoredOn),
        });
      }
      continue;
    }

    if (!isActive(med)) continue;

    if (!preMed) {
      const dosage = extractDosage(med);
      newMeds.push({
        medication: extractDisplayName(med),
        rxnorm,
        startedOn: toDateOnly(med.authoredOn),
        dosage: dosage ? expandText(dosage) : undefined,
      });
    } else {
      const prevDosage = extractDosage(preMed);
      const newDosage = extractDosage(med);
      if (prevDosage !== newDosage) {
        changedMeds.push({
          medication: extractDisplayName(med),
          rxnorm,
          previousDosage: prevDosage ? expandText(prevDosage) : "",
          newDosage: newDosage ? expandText(newDosage) : "",
          changedOn: toDateOnly(med.authoredOn),
        });
        changedRxNorms.add(rxnorm);
      } else {
        continuedMeds.push({
          medication: extractDisplayName(med),
          rxnorm,
        });
      }
    }
  }

  for (const med of preAdmission) {
    const rxnorm = extractRxNorm(med);
    if (!rxnorm || changedRxNorms.has(rxnorm)) continue;
    if (!isActive(med)) continue;

    const alreadyContinued = continuedMeds.some((c) => c.rxnorm === rxnorm);
    const alreadyNew = newMeds.some((n) => n.rxnorm === rxnorm);
    const alreadyStopped = stoppedMeds.some((s) => s.rxnorm === rxnorm);
    const updatedDuringAdmission = duringAdmission.some(
      (d) => extractRxNorm(d) === rxnorm,
    );

    if (
      !alreadyContinued &&
      !alreadyNew &&
      !alreadyStopped &&
      !updatedDuringAdmission
    ) {
      continuedMeds.push({
        medication: extractDisplayName(med),
        rxnorm,
      });
    }
  }

  const activeDischargeMeds = [
    ...medicationRequests.filter((med) => {
      const rxnorm = extractRxNorm(med);
      return (
        isActive(med) &&
        rxnorm !== undefined &&
        !skippedIds.has(med.id ?? "")
      );
    }),
  ];

  for (let i = 0; i < activeDischargeMeds.length; i++) {
    for (let j = i + 1; j < activeDischargeMeds.length; j++) {
      const medA = activeDischargeMeds[i];
      const medB = activeDischargeMeds[j];
      if (!medA || !medB) continue;

      const rxA = extractRxNorm(medA);
      const rxB = extractRxNorm(medB);
      if (!rxA || !rxB) continue;

      const interaction = DRUG_INTERACTIONS.find(
        (d) =>
          (d.pair[0] === rxA && d.pair[1] === rxB) ||
          (d.pair[0] === rxB && d.pair[1] === rxA),
      );

      if (interaction) {
        interactionWarnings.push({
          medications: [extractDisplayName(medA), extractDisplayName(medB)],
          severity: interaction.severity,
          note: interaction.note,
        });
      }
    }
  }

  for (const med of activeDischargeMeds) {
    const rxnorm = extractRxNorm(med);
    const displayName = extractDisplayName(med).toLowerCase();

    for (const allergy of allergyIntolerances) {
      const allergenDisplay =
        allergy.code?.text ??
        allergy.code?.coding?.[0]?.display ??
        "Unknown allergen";

      const codeMatch = allergy.code?.coding?.some((c) => c.code === rxnorm);
      const nameMatch = allergenDisplay.toLowerCase().includes(displayName) ||
        displayName.includes(allergenDisplay.toLowerCase());

      if (codeMatch || nameMatch) {
        const severity =
          allergy.reaction?.[0]?.severity ?? allergy.criticality ?? "unknown";

        allergyConflicts.push({
          medication: extractDisplayName(med),
          allergen: allergenDisplay,
          severity: String(severity),
        });
      }
    }
  }

  return {
    encounterDate,
    reconciliation: {
      new: newMeds,
      stopped: stoppedMeds,
      changed: changedMeds,
      continued: continuedMeds,
    },
    interactionWarnings,
    allergyConflicts,
  };
}
