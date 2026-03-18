import assert from "node:assert/strict";
import { createServer } from "node:http";
import { format } from "date-fns";
import type { Request } from "express";
import {
  buildConditionResource,
  buildPatientResource,
  parsePatientWithConditionsPrompt,
} from "./patient-condition-parser";
import { createPatientWithConditionsFromPrompt } from "./tools/CreatePatientWithConditionsTool";

const fixedNow = new Date("2026-03-19T00:00:00.000Z");

const examplePrompt = parsePatientWithConditionsPrompt(
  "Create the patient John Doe that is 57 years old with high cholesterol that started last week.",
  fixedNow,
);

assert.equal(examplePrompt.firstName, "John");
assert.equal(examplePrompt.lastName, "Doe");
assert.equal(examplePrompt.birthDate, "1969-03-19");
assert.equal(examplePrompt.conditions.length, 1);
assert.equal(examplePrompt.conditions[0]?.text, "high cholesterol");
assert.equal(
  examplePrompt.conditions[0]?.onsetDateTime
    ? format(new Date(examplePrompt.conditions[0].onsetDateTime), "yyyy-MM-dd")
    : undefined,
  "2026-03-12",
);

const multiConditionPrompt = parsePatientWithConditionsPrompt(
  "Create patient Jane Smith aged 40 with asthma and seasonal allergies started 2 months ago.",
  fixedNow,
);

assert.equal(multiConditionPrompt.firstName, "Jane");
assert.equal(multiConditionPrompt.lastName, "Smith");
assert.equal(multiConditionPrompt.birthDate, "1986-03-19");
assert.deepEqual(
  multiConditionPrompt.conditions.map((condition) => condition.text),
  ["asthma", "seasonal allergies"],
);
assert.ok(
  multiConditionPrompt.conditions.every(
    (condition) =>
      condition.onsetDateTime &&
      format(new Date(condition.onsetDateTime), "yyyy-MM-dd") === "2026-01-19",
  ),
);

const patientResource = buildPatientResource(examplePrompt);
assert.equal(patientResource.resourceType, "Patient");
assert.equal(patientResource.name?.[0]?.family, "Doe");
assert.deepEqual(patientResource.name?.[0]?.given, ["John"]);

const conditionResource = buildConditionResource(
  "patient-123",
  examplePrompt.fullName,
  examplePrompt.conditions[0],
);
assert.equal(conditionResource.resourceType, "Condition");
assert.equal(conditionResource.subject?.reference, "Patient/patient-123");
assert.equal(conditionResource.code?.text, "high cholesterol");
assert.equal(
  conditionResource.onsetDateTime
    ? format(new Date(conditionResource.onsetDateTime), "yyyy-MM-dd")
    : undefined,
  "2026-03-12",
);

const patientCreations: unknown[] = [];
const conditionCreations: unknown[] = [];

const main = async () => {
  const server = createServer((req, res) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      const body = JSON.parse(
        Buffer.concat(chunks).toString("utf8"),
      ) as Record<string, unknown>;

      res.setHeader("content-type", "application/json");
      if (req.method === "POST" && req.url === "/Patient") {
        patientCreations.push(body);
        res.statusCode = 201;
        res.end(JSON.stringify({ ...body, id: "patient-123" }));
        return;
      }

      if (req.method === "POST" && req.url === "/Condition") {
        conditionCreations.push(body);
        res.statusCode = 201;
        res.end(
          JSON.stringify({
            ...body,
            id: `condition-${conditionCreations.length}`,
          }),
        );
        return;
      }

      res.statusCode = 404;
      res.end(JSON.stringify({ message: "Not found" }));
    });
  });

  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve());
  });

  try {
    const address = server.address();
    if (!address || typeof address === "string") {
      throw new Error("Could not determine the mock FHIR server port.");
    }

    const result = await createPatientWithConditionsFromPrompt(
      {
        headers: {
          "x-fhir-server-url": `http://127.0.0.1:${address.port}`,
        },
      } as unknown as Request,
      "Create the patient John Doe that is 57 years old with high cholesterol that started last week.",
    );

    assert.equal(result.isError, false);
    assert.equal(patientCreations.length, 1);
    assert.equal(conditionCreations.length, 1);
    assert.equal(
      (patientCreations[0] as { resourceType?: string }).resourceType,
      "Patient",
    );
    assert.equal(
      (conditionCreations[0] as {
        subject?: { reference?: string };
        code?: { text?: string };
      }).subject?.reference,
      "Patient/patient-123",
    );
    assert.equal(
      (conditionCreations[0] as {
        subject?: { reference?: string };
        code?: { text?: string };
      }).code?.text,
      "high cholesterol",
    );
    assert.equal(result.content[0]?.type, "text");
    assert.match(
      result.content[0]?.type === "text" ? result.content[0].text : "",
      /Patient id: patient-123/,
    );
    assert.match(
      result.content[0]?.type === "text" ? result.content[0].text : "",
      /Condition ids: high cholesterol: condition-1/,
    );
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((error) => {
        if (error) {
          reject(error);
          return;
        }

        resolve();
      });
    });
  }
};

main()
  .then(() => {
    console.log("Natural-language patient creation verification passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
