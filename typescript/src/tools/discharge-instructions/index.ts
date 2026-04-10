import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { z } from "zod";
import { IMcpTool } from "../../mcp/tool.interface";
import { McpResponse } from "../../mcp/response";
import { resolvePatientId } from "../../utils/patient-context";
import {
  getPatient,
  getEncounters,
  getConditions,
  getProcedures,
  getMedicationRequests,
} from "../../fhir/queries";
import { generateDischargeInstructions } from "./service";

class DischargeInstructionsTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "GenerateDischargeInstructions",
      {
        description:
          "Produces plain-language discharge instructions from templates. Supports simple, standard, and detailed reading levels.",
        inputSchema: {
          patientId: z
            .string()
            .describe(
              "The patient ID. Optional if patient context exists.",
            )
            .optional(),
          readingLevel: z
            .enum(["simple", "standard", "detailed"])
            .describe("The reading level for instructions.")
            .default("standard"),
        },
      },
      async ({ patientId, readingLevel }) => {
        const id = resolvePatientId(patientId, req);

        const [patient, encounters, conditions, procedures, medicationRequests] =
          await Promise.all([
            getPatient(req, id),
            getEncounters(req, id, [
              "class=IMP",
              "_sort=-date",
              "_count=1",
            ]),

            getConditions(req, id, ["clinical-status=active"]),
            getProcedures(req, id),
            getMedicationRequests(req, id, ["status=active"]),
          ]);

        if (!patient) {
          return McpResponse.error("Patient not found.");
        }

        const encounter = encounters[0];
        if (!encounter) {
          return McpResponse.error("No inpatient encounter found.");
        }

        const result = generateDischargeInstructions({
          readingLevel,
          patient,
          encounter,
          conditions,
          procedures,
          medicationRequests,
        });

        return McpResponse.json(result);
      },
    );
  }
}

export const dischargeInstructionsTool = new DischargeInstructionsTool();
