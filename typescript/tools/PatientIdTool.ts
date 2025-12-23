import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";
import { IMcpTool } from "../IMcpTool";
import { z } from "zod";
import { fhirR4 } from "@smile-cdr/fhirts";
import { FhirClientInstance } from "../fhir-client";
import { McpUtilities } from "../mcp-utilities";
import { NullUtilities } from "../null-utilities";

class PatientIdTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "FindPatientId",
      {
        description: "Finds a patient id given a first name and last name",
        inputSchema: {
          firstName: z.string().describe("The patient's first name").nonempty(),
          lastName: z
            .string()
            .describe("The patient's last name. This is optional")
            .optional(),
        },
      },
      async ({ firstName, lastName }) => {
        let patients = await this._patientSearcher(req, firstName, lastName);
        if (!patients?.length) {
          patients = await this._patientSearcher(req, lastName, firstName);
        }

        if (patients && patients.length > 1) {
          return McpUtilities.createTextResponse(
            "More than one patient was found. Provide more details.",
            { isError: true },
          );
        }

        return patients?.[0]
          ? McpUtilities.createTextResponse(
              NullUtilities.getOrThrow(patients[0].id),
            )
          : McpUtilities.createTextResponse(
              "No patient could be found with that name",
              { isError: true },
            );
      },
    );
  }

  private async _patientSearcher(
    req: Request,
    searchFirstName: string | null | undefined,
    searchLastName: string | null | undefined,
  ): Promise<fhirR4.Patient[] | null> {
    const searchParameters: string[] = [];
    if (searchFirstName) {
      searchParameters.push(`given=${searchFirstName}`);
    }

    if (searchLastName) {
      searchParameters.push(`family=${searchLastName}`);
    }

    const response = await FhirClientInstance.search(
      req,
      "Patient",
      searchParameters,
    );
    return response?.entry?.length
      ? response.entry
          .filter((x) => !!x.resource)
          .map((x) => x.resource as fhirR4.Patient)
      : null;
  }
}

export const PatientIdToolInstance = new PatientIdTool();
