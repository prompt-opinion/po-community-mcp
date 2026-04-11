import axios from "axios";
import { logger } from "../../logger";
import { RxNavRelatedResponse, RxNavRelatedGroup } from "./types";

const RXNAV_BASE_URL = "https://rxnav.nlm.nih.gov/REST";
const RXNAV_TIMEOUT_MS = 5000;

export async function getRelatedGenerics(
  rxcui: string,
): Promise<RxNavRelatedGroup[]> {
  try {
    // tty param uses '+' as separator — must be literal, not URL-encoded (%2B)
    const response = await axios.get<RxNavRelatedResponse>(
      `${RXNAV_BASE_URL}/rxcui/${rxcui}/related.json?tty=SBD+SCD`,
      { timeout: RXNAV_TIMEOUT_MS },
    );

    return (
      response.data.relatedGroup?.conceptGroup?.flatMap(
        (g) =>
          g.conceptProperties?.map((p) => ({
            rxcui: p.rxcui,
            tty: p.tty,
            name: p.name,
          })) ?? [],
      ) ?? []
    );
  } catch (error) {
    logger.warn("RxNav API unavailable", {
      rxcui,
      error: error instanceof Error ? error.message : String(error),
    });
    return [];
  }
}
