import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { CallToolResultSchema } from "@modelcontextprotocol/sdk/types.js";

const mcpBaseUrl =
  process.env["MCP_BASE_URL"]?.trim() || "http://localhost:5000/mcp";
const fhirServerUrl = process.env["REAL_FHIR_SERVER_URL"]?.trim();
const fhirAccessToken = process.env["REAL_FHIR_ACCESS_TOKEN"]?.trim();

if (!fhirServerUrl) {
  throw new Error(
    "REAL_FHIR_SERVER_URL is required for the real MCP/FHIR verification.",
  );
}

const transport = new StreamableHTTPClientTransport(new URL(mcpBaseUrl), {
  requestInit: {
    headers: {
      "x-fhir-server-url": fhirServerUrl,
      ...(fhirAccessToken
        ? {
            "x-fhir-access-token": fhirAccessToken,
          }
        : {}),
    },
  },
});

const fetchFhirResource = async (path: string) => {
  const response = await fetch(
    `${fhirServerUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`,
    {
      headers: {
        Accept: "application/fhir+json",
        ...(fhirAccessToken
          ? {
              Authorization: `Bearer ${fhirAccessToken}`,
            }
          : {}),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      `FHIR fetch failed for ${path}: ${response.status} ${response.statusText}`,
    );
  }

  return (await response.json()) as Record<string, unknown>;
};

const extractIds = (resultText: string) => {
  const patientMatch = resultText.match(/^Patient id:\s*(\S+)$/m);
  const conditionMatch = resultText.match(
    /^Condition ids:\s*[^:]+:\s*(\S+)$/m,
  );

  if (!patientMatch?.[1] || !conditionMatch?.[1]) {
    throw new Error(`Could not extract resource ids from tool output:\n${resultText}`);
  }

  return {
    patientId: patientMatch[1],
    conditionId: conditionMatch[1],
  };
};

const main = async () => {
  const client = new Client({
    name: "po-community-mcp-real-verifier",
    version: "1.0.0",
  });

  try {
    await client.connect(transport);

    const toolsResult = await client.listTools();
    assert.ok(
      toolsResult.tools.some(
        (tool) => tool.name === "CreatePatientWithConditionsFromPrompt",
      ),
      "CreatePatientWithConditionsFromPrompt should be exposed over MCP.",
    );

    const uniqueSuffix = Date.now().toString();
    const lastName = `Verifier${uniqueSuffix}`;
    const prompt = `Create the patient Jane ${lastName} that is 40 years old with high cholesterol that started last week.`;

    const toolResult = await client.callTool({
      name: "CreatePatientWithConditionsFromPrompt",
      arguments: { prompt },
    }, CallToolResultSchema);

    assert.equal(toolResult.isError, false);
    const resultContent = toolResult.content as Array<{
      type: string;
      text?: string;
    }>;
    assert.equal(resultContent[0]?.type, "text");

    const resultText =
      resultContent[0]?.type === "text" ? resultContent[0].text ?? "" : "";
    const { patientId, conditionId } = extractIds(resultText);

    const patient = await fetchFhirResource(`Patient/${patientId}`);
    const condition = await fetchFhirResource(`Condition/${conditionId}`);

    assert.equal(patient["resourceType"], "Patient");
    assert.equal(condition["resourceType"], "Condition");
    assert.equal(
      (patient["name"] as Array<{ family?: string }> | undefined)?.[0]?.family,
      lastName,
    );
    assert.equal(
      (condition["subject"] as { reference?: string } | undefined)?.reference,
      `Patient/${patientId}`,
    );
    assert.equal(
      (condition["code"] as { text?: string } | undefined)?.text,
      "high cholesterol",
    );

    console.log(
      [
        `MCP tool created Patient/${patientId}`,
        `MCP tool created Condition/${conditionId}`,
        `Verified both resources exist on ${fhirServerUrl}`,
      ].join("\n"),
    );
  } finally {
    await transport.close();
  }
};

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
