import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { IMcpTool } from "../IMcpTool";
import { z } from "zod";
import { FhirUtilities } from "../fhir-utilities";
import { McpUtilities } from "../mcp-utilities";
import { differenceInYears, parseISO } from "date-fns";
import { NullUtilities } from "../null-utilities";
import { FhirClientInstance } from "../fhir-client";
import { fhirR4 } from "@smile-cdr/fhirts";

class PatientAgeTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "GetPatientAge",
      {
        description: "Gets the age of a patient.",
        inputSchema: {
          patientId: z
            .string()
            .describe(
              "The id of the patient. This is optional if patient context already exists",
            )
            .optional(),
        },
      },
      async ({ patientId }) => {
        if (!patientId) {
          patientId = NullUtilities.getOrThrow(
            FhirUtilities.getPatientIdIfContextExists(req),
          );
        }

        const patient = await FhirClientInstance.read<fhirR4.Patient>(
          req,
          `Patient/${patientId}`,
        );
        if (!patient) {
          return McpUtilities.createTextResponse(
            "The patinet could not be found.",
            { isError: true },
          );
        }

        if (!patient.birthDate) {
          return McpUtilities.createTextResponse(
            "A birth date could not be found for the patient.",
            { isError: true },
          );
        }

        try {
          const date = parseISO(patient.birthDate);
          const age = differenceInYears(new Date(), date);

          return McpUtilities.createTextResponse(
            `The patient's age is: ${age}`,
          );
        } catch {
          return McpUtilities.createTextResponse(
            "Could not parse the patient's birth date.",
            { isError: true },
          );
        }
      },
    );
  }
}

export const PatientAgeToolInstance = new PatientAgeTool();
