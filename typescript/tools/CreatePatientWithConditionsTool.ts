import { fhirR4 } from "@smile-cdr/fhirts";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { CallToolResult } from "@modelcontextprotocol/sdk/types";
import { Request } from "express";
import { z } from "zod";
import { IMcpTool } from "../IMcpTool";
import { FhirClientInstance } from "../fhir-client";
import { McpUtilities } from "../mcp-utilities";
import {
  buildConditionResource,
  buildPatientResource,
  parsePatientWithConditionsPrompt,
} from "../patient-condition-parser";

export const createPatientWithConditionsFromPrompt = async (
  req: Request,
  prompt: string,
): Promise<CallToolResult> => {
  try {
    const parsedPrompt = parsePatientWithConditionsPrompt(prompt);
    const createdPatient = await FhirClientInstance.create<fhirR4.Patient>(
      req,
      buildPatientResource(parsedPrompt),
    );
    const patientId = createdPatient?.id;
    if (!patientId) {
      return McpUtilities.createTextResponse(
        "The patient was created, but the FHIR server did not return a patient id.",
        { isError: true },
      );
    }

    const createdConditionSummaries: string[] = [];
    for (const condition of parsedPrompt.conditions) {
      const createdCondition = await FhirClientInstance.create<fhirR4.Condition>(
        req,
        buildConditionResource(patientId, parsedPrompt.fullName, condition),
      );

      if (!createdCondition?.id) {
        return McpUtilities.createTextResponse(
          [
            `Patient created with id: ${patientId}`,
            "A condition was created without an id in the FHIR response.",
          ].join("\n"),
          { isError: true },
        );
      }

      createdConditionSummaries.push(`${condition.text}: ${createdCondition.id}`);
    }

    return McpUtilities.createTextResponse(
      [
        `Patient id: ${patientId}`,
        `Condition ids: ${createdConditionSummaries.join(", ")}`,
      ].join("\n"),
    );
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Failed to create the patient and conditions from the supplied prompt.";

    return McpUtilities.createTextResponse(message, { isError: true });
  }
};

class CreatePatientWithConditionsTool implements IMcpTool {
  registerTool(server: McpServer, req: Request) {
    server.registerTool(
      "CreatePatientWithConditionsFromPrompt",
      {
        description:
          "Creates a Patient and linked Condition resources from a natural-language prompt such as 'Create the patient John Doe that is 57 years old with high cholesterol that started last week.'",
        inputSchema: {
          prompt: z
            .string()
            .describe(
              "A natural-language description of the patient and one or more conditions to create.",
            )
            .nonempty(),
        },
      },
      async ({ prompt }) => createPatientWithConditionsFromPrompt(req, prompt),
    );
  }
}

export const CreatePatientWithConditionsToolInstance =
  new CreatePatientWithConditionsTool();
