import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { z } from "zod";
import { IMcpTool } from "../../mcp/tool.interface";
import { McpResponse } from "../../mcp/response";
import { resolvePatientId } from "../../utils/patient-context";
import {
  getMedicationRequests,
  getAllergyIntolerances,
} from "../../fhir/queries";
import { auditMedCosts } from "./service";

class AuditMedCostsTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "AuditMedCosts",
      {
        description:
          "Finds brand-to-generic savings opportunities for active medications.",
        inputSchema: {
          patientId: z
            .string()
            .describe(
              "The patient ID. Optional if patient context exists.",
            )
            .optional(),
        },
      },
      async ({ patientId }) => {
        const id = resolvePatientId(patientId, req);

        const [medicationRequests, allergyIntolerances] = await Promise.all([
          getMedicationRequests(req, id),
          getAllergyIntolerances(req, id),
        ]);

        const result = await auditMedCosts({
          medicationRequests,
          allergyIntolerances,
        });

        return McpResponse.json(result);
      },
    );
  }
}

export const auditMedCostsTool = new AuditMedCostsTool();
