import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { z } from "zod";
import { IMcpTool } from "../../mcp/tool.interface";
import { McpResponse } from "../../mcp/response";
import { resolvePatientId } from "../../utils/patient-context";
import {
  getEncounters,
  getMedicationRequests,
  getAllergyIntolerances,
} from "../../fhir/queries";
import { reconcileMedications } from "./service";
import { logger } from "../../logger";

class ReconcileMedicationsTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "ReconcileMedications",
      {
        description:
          "Compares pre-admission medications with current active medications at discharge. " +
          "Identifies new, stopped, and changed medications, and checks for drug interactions and allergy conflicts.",
        inputSchema: {
          patientId: z
            .string()
            .describe(
              "FHIR Patient ID. If omitted, resolved from SHARP context.",
            )
            .optional(),
        },
      },
      async ({ patientId }) => {
        const id = resolvePatientId(patientId, req);

        const [encounters, medicationRequests, allergyIntolerances] =
          await Promise.all([
            getEncounters(req, id, [
              "class=IMP",
              "_sort=-date",
              "_count=1",
            ]),
            getMedicationRequests(req, id, ["_sort=-date", "_count=100"]),
            getAllergyIntolerances(req, id),
          ]);

        const encounter = encounters[0];
        if (!encounter) {
          return McpResponse.error("No inpatient encounter found.");
        }

        try {
          const result = reconcileMedications({
            encounter,
            medicationRequests,
            allergyIntolerances,
          });
          return McpResponse.json(result);
        } catch (err) {
          const message =
            err instanceof Error ? err.message : "Unexpected error";
          logger.error("ReconcileMedications service error", { error: message });
          return McpResponse.error(message);
        }
      },
    );
  }
}

export const reconcileMedicationsTool = new ReconcileMedicationsTool();
