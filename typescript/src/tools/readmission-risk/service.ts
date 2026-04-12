import { CHARLSON_MAP, charlsonSumToLaceC, getSnomedCode } from "../../data/charlson-mapping";
import { ReadmissionRiskInput, ReadmissionRiskResult, RiskCategory } from "./types";

function scoreL(encounter: ReadmissionRiskInput["encounter"]): number {
  const { start, end } = encounter.period ?? {};
  if (!start || !end) return 0;
  const days = Math.ceil((new Date(end).getTime() - new Date(start).getTime()) / 86_400_000);
  if (days <= 1) return 0;
  if (days === 2) return 1;
  if (days === 3) return 2;
  if (days <= 6) return 3;
  if (days <= 13) return 4;
  return 5;
}

function scoreA(encounter: ReadmissionRiskInput["encounter"]): number {
  const admitCodes = encounter.hospitalization?.admitSource?.coding ?? [];
  if (admitCodes.some((c) => c.code === "emd")) return 3;
  const classHistory = encounter.classHistory ?? [];
  if (classHistory.some((h) => h.class?.code === "EMER")) return 3;
  return 0;
}

function scoreC(conditions: ReadmissionRiskInput["conditions"]): number {
  const best: Record<string, number> = {};
  for (const condition of conditions) {
    const code = getSnomedCode(condition.code?.coding);
    if (!code) continue;
    const entry = CHARLSON_MAP[code];
    if (!entry) continue;
    best[entry.category] = Math.max(best[entry.category] ?? 0, entry.points);
  }
  const sum = Object.values(best).reduce((a, b) => a + b, 0);
  return charlsonSumToLaceC(sum);
}

function scoreE(erEncounters: ReadmissionRiskInput["erEncounters"]): number {
  return Math.min(erEncounters.length, 4);
}

const RECOMMENDATIONS: Record<RiskCategory, string> = {
  low: "Routine follow-up. Schedule PCP visit within 30 days.",
  moderate: "Elevated risk. Ensure follow-up within 7 days and medication reconciliation.",
  high: "High readmission risk. Initiate transitional care management and 48-hour post-discharge contact.",
};

export function assessReadmissionRisk(input: ReadmissionRiskInput): ReadmissionRiskResult {
  const L = scoreL(input.encounter);
  const A = scoreA(input.encounter);
  const C = scoreC(input.conditions);
  const E = scoreE(input.erEncounters);
  const laceScore = L + A + C + E;
  const category: RiskCategory = laceScore <= 4 ? "low" : laceScore <= 9 ? "moderate" : "high";
  return { laceScore, category, breakdown: { L, A, C, E }, recommendation: RECOMMENDATIONS[category] };
}
