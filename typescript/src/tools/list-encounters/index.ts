import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { z } from "zod";
import { fhirR4 } from "@smile-cdr/fhirts";
import { IMcpTool } from "../../mcp/tool.interface";
import { McpResponse } from "../../mcp/response";
import { resolvePatientId } from "../../utils/patient-context";
import { getEncounters } from "../../fhir/queries";

const CLASS_LABELS: Record<string, string> = {
  IMP: "Inpatient",
  AMB: "Ambulatory",
  EMER: "Emergency",
  SS: "Short Stay",
  HH: "Home Health",
  VR: "Virtual",
  OBSENC: "Observation",
};

function formatEncounter(enc: fhirR4.Encounter) {
  const classCode =
    (enc.class as unknown as { code?: string })?.code ?? "unknown";
  const label = CLASS_LABELS[classCode] ?? classCode;
  const period = enc.period as { start?: string; end?: string } | undefined;

  return {
    id: enc.id,
    status: enc.status,
    class: classCode,
    classLabel: label,
    start: period?.start ?? null,
    end: period?.end ?? null,
  };
}

class ListEncountersTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "ListEncounters",
      {
        description:
          "Lists all encounters for a patient, grouped by class (Inpatient, Ambulatory, Emergency, etc).",
        inputSchema: {
          patientId: z
            .string()
            .describe(
              "The patient ID. Optional if patient context exists.",
            )
            .optional(),
          classFilter: z
            .string()
            .describe(
              "Optional encounter class code to filter by (e.g. IMP, AMB, EMER). Returns all classes if omitted.",
            )
            .optional(),
        },
      },
      async ({ patientId, classFilter }) => {
        const id = resolvePatientId(patientId, req);

        const VALID_CLASS_CODES = new Set(Object.keys(CLASS_LABELS));
        const params: string[] = [];
        if (classFilter) {
          if (!VALID_CLASS_CODES.has(classFilter)) {
            return McpResponse.error(
              `Invalid class code "${classFilter}". Valid codes: ${[...VALID_CLASS_CODES].join(", ")}`,
            );
          }
          params.push(`class=${encodeURIComponent(classFilter)}`);
        }
        params.push("_sort=-date");

        const encounters = await getEncounters(req, id, params);

        if (!encounters.length) {
          const msg = classFilter
            ? `No encounters with class "${classFilter}" found for this patient.`
            : "No encounters found for this patient.";
          return McpResponse.error(msg);
        }

        const formatted = encounters.map(formatEncounter);

        const grouped: Record<string, typeof formatted> = {};
        for (const enc of formatted) {
          const key = enc.classLabel;
          if (!grouped[key]) grouped[key] = [];
          grouped[key].push(enc);
        }

        return McpResponse.json({
          patientId: id,
          totalEncounters: formatted.length,
          byClass: grouped,
        });
      },
    );
  }
}

export const listEncountersTool = new ListEncountersTool();
