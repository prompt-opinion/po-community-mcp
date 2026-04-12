import { fhirR4 } from "@smile-cdr/fhirts";

export interface LaceBreakdown {
  L: number;
  A: number;
  C: number;
  E: number;
}

export type RiskCategory = "low" | "moderate" | "high";

export interface ReadmissionRiskResult {
  laceScore: number;
  category: RiskCategory;
  breakdown: LaceBreakdown;
  recommendation: string;
}

export interface ReadmissionRiskInput {
  encounter: fhirR4.Encounter;
  erEncounters: fhirR4.Encounter[];
  conditions: fhirR4.Condition[];
}
