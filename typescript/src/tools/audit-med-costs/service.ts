import { AuditMedCostsInput, AuditMedCostsResult, SavingsOpportunity } from "./types";
import {
  COST_TIERS,
  DISCLAIMER,
  KNOWN_BRAND_TO_GENERIC,
  KNOWN_GENERICS,
  DrugTier,
} from "../../data/cost-tiers";
import { getRelatedGenerics } from "../../external/rxnav/client";

const RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm";

function midpoint(tier: DrugTier): number {
  return (COST_TIERS[tier].min + COST_TIERS[tier].max) / 2;
}

export async function auditMedCosts(input: AuditMedCostsInput): Promise<AuditMedCostsResult> {
  const { medicationRequests, allergyIntolerances } = input;

  // Build a set of RxNorm codes the patient is allergic to
  const allergyRxCuis = new Set<string>();
  for (const allergy of allergyIntolerances) {
    for (const reaction of allergy.reaction ?? []) {
      for (const coding of reaction.substance?.coding ?? []) {
        if (coding.system === RXNORM_SYSTEM && coding.code) {
          allergyRxCuis.add(coding.code);
        }
      }
    }
  }

  const savingsOpportunities: SavingsOpportunity[] = [];
  const noChangeNeeded: string[] = [];
  let rxnavUnreachable = false;

  for (const med of medicationRequests) {
    const concept = med.medicationCodeableConcept;
    const rxnormCoding = concept?.coding?.find((c) => c.system === RXNORM_SYSTEM);
    const name = concept?.text ?? rxnormCoding?.display ?? "Unknown medication";
    const rxcui = rxnormCoding?.code;

    if (!rxcui) {
      noChangeNeeded.push(name);
      continue;
    }

    // Already a known generic — no savings opportunity
    if (KNOWN_GENERICS.has(rxcui)) {
      noChangeNeeded.push(name);
      continue;
    }

    // Fast path: known brand→generic mapping (no network call needed)
    const knownGeneric = KNOWN_BRAND_TO_GENERIC[rxcui];
    if (knownGeneric) {
      if (allergyRxCuis.has(knownGeneric.rxnorm)) {
        noChangeNeeded.push(name);
        continue;
      }
      const savings = Math.round(midpoint("non_preferred_brand") - midpoint(knownGeneric.tier));
      if (savings > 0) {
        savingsOpportunities.push({
          currentMedication: name,
          suggestedAlternative: knownGeneric.name,
          estimatedMonthlySavings: savings,
          reason: "Switch from brand-name to generic equivalent",
        });
      } else {
        noChangeNeeded.push(name);
      }
      continue;
    }

    // RxNav lookup: fetches both SBD (brand) and SCD (generic) related drugs
    const related = await getRelatedGenerics(rxcui);

    if (related.length === 0) {
      // Empty result means RxNav was unreachable (client returns [] on any error)
      rxnavUnreachable = true;
      noChangeNeeded.push(name);
      continue;
    }

    // If this drug itself is listed as SCD, it is already a generic
    if (related.some((r) => r.rxcui === rxcui && r.tty === "SCD")) {
      noChangeNeeded.push(name);
      continue;
    }

    // Extract dose from current med name (e.g. "20 MG") to avoid suggesting a different strength
    const doseStr = name.match(/(\d+(?:\.\d+)?)\s*MG/i)?.[1] ?? null;

    // Find the first safe generic at the same dose
    const genericAlt = related.find(
      (r) =>
        r.tty === "SCD" &&
        !allergyRxCuis.has(r.rxcui) &&
        (doseStr === null || r.name.includes(doseStr)),
    );
    if (genericAlt) {
      const savings = Math.round(midpoint("non_preferred_brand") - midpoint("generic"));
      if (savings > 0) {
        savingsOpportunities.push({
          currentMedication: name,
          suggestedAlternative: genericAlt.name,
          estimatedMonthlySavings: savings,
          reason: "Switch from brand-name to generic equivalent",
        });
      } else {
        noChangeNeeded.push(name);
      }
    } else {
      noChangeNeeded.push(name);
    }
  }

  const totalEstimatedMonthlySavings = savingsOpportunities.reduce(
    (sum, opp) => sum + opp.estimatedMonthlySavings,
    0,
  );

  const disclaimer = rxnavUnreachable
    ? `${DISCLAIMER} Cost analysis unavailable — external drug database unreachable`
    : DISCLAIMER;

  return { savingsOpportunities, totalEstimatedMonthlySavings, noChangeNeeded, disclaimer };
}
