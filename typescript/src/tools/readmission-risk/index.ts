import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { z } from "zod";
import { IMcpTool } from "../../mcp/tool.interface";
import { McpResponse } from "../../mcp/response";
import { resolvePatientId } from "../../utils/patient-context";
import { getEncounters, getConditions } from "../../fhir/queries";
import { assessReadmissionRisk } from "./service";

class ReadmissionRiskTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "AssessReadmissionRisk",
      {
        description:
          "Computes LACE readmission risk index (0-19). Pure deterministic math based on encounter and comorbidity data.",
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

        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        const sixMonthsAgoStr = sixMonthsAgo.toISOString().split("T")[0];

        const [inpatientEncounters, erEncounters, conditions] = await Promise.all([
          getEncounters(req, id, ["class=IMP", "_sort=-date", "_count=1"]),
          getEncounters(req, id, ["class=EMER", `date=ge${sixMonthsAgoStr}`]),
          getConditions(req, id, ["clinical-status=active"]),
        ]);

        const encounter = inpatientEncounters[0];
        if (!encounter) {
          return McpResponse.error("No inpatient encounter found.");
        }

        const result = assessReadmissionRisk({ encounter, erEncounters, conditions });

        return McpResponse.json(result);
      },
    );
  }
}

export const readmissionRiskTool = new ReadmissionRiskTool();
