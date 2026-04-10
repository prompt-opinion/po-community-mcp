import { fhirR4 } from "@smile-cdr/fhirts";

export interface ReconcileMedicationsInput {
  encounter: fhirR4.Encounter;
  medicationRequests: fhirR4.MedicationRequest[];
  allergyIntolerances: fhirR4.AllergyIntolerance[];
}

export interface MedicationEntry {
  medication: string;
  rxnorm: string;
  startedOn?: string;
  reason?: string;
  dosage?: string;
}

export interface StoppedMedicationEntry {
  medication: string;
  rxnorm: string;
  stoppedOn?: string;
  reason?: string;
}

export interface ChangedMedicationEntry {
  medication: string;
  rxnorm: string;
  previousDosage: string;
  newDosage: string;
  changedOn?: string;
}

export interface BasicMedicationEntry {
  medication: string;
  rxnorm: string;
}

export interface InteractionWarning {
  medications: string[];
  severity: string;
  note: string;
}

export interface AllergyConflict {
  medication: string;
  allergen: string;
  severity: string;
}

export interface ReconcileMedicationsOutput {
  encounterDate: string;
  reconciliation: {
    new: MedicationEntry[];
    stopped: StoppedMedicationEntry[];
    changed: ChangedMedicationEntry[];
    continued: BasicMedicationEntry[];
  };
  interactionWarnings: InteractionWarning[];
  allergyConflicts: AllergyConflict[];
}

export type ReconcileMedicationsResult = ReconcileMedicationsOutput;
