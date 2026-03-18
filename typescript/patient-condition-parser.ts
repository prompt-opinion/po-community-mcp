import { fhirR4 } from "@smile-cdr/fhirts";
import {
  format,
  isValid,
  parse,
  parseISO,
  startOfDay,
  subDays,
  subMonths,
  subWeeks,
  subYears,
} from "date-fns";

const NAME_STOP_MARKERS = [
  " that is ",
  " who is ",
  " aged ",
  " age ",
  " with ",
  ".",
  ",",
  ";",
];

const ONSET_FORMATS = [
  "yyyy-MM-dd",
  "MMMM d, yyyy",
  "MMM d, yyyy",
  "MMMM d yyyy",
  "MMM d yyyy",
];

export type ParsedCondition = Readonly<{
  text: string;
  onsetDateTime?: string;
}>;

export type ParsedPatientWithConditions = Readonly<{
  fullName: string;
  firstName: string;
  lastName: string;
  birthDate: string;
  conditions: readonly ParsedCondition[];
}>;

const normalizeWhitespace = (value: string) =>
  value.trim().replace(/\s+/g, " ");

const stripTrailingPunctuation = (value: string) =>
  value.trim().replace(/[.!?,;:]+$/g, "").trim();

const extractNameSegment = (prompt: string) => {
  const normalizedPrompt = normalizeWhitespace(prompt);
  const loweredPrompt = normalizedPrompt.toLowerCase();
  const patientIndex = loweredPrompt.indexOf("patient");
  if (patientIndex === -1) {
    throw new Error(
      "The prompt must identify the patient by name, for example: 'Create the patient John Doe ...'.",
    );
  }

  let remainingPrompt = normalizedPrompt
    .slice(patientIndex + "patient".length)
    .trim()
    .replace(/^(named|called)\s+/i, "");

  let endIndex = remainingPrompt.length;
  const loweredRemainingPrompt = remainingPrompt.toLowerCase();
  for (const marker of NAME_STOP_MARKERS) {
    const markerIndex = loweredRemainingPrompt.indexOf(marker);
    if (markerIndex !== -1 && markerIndex < endIndex) {
      endIndex = markerIndex;
    }
  }

  remainingPrompt = normalizeWhitespace(
    stripTrailingPunctuation(remainingPrompt.slice(0, endIndex)),
  );
  if (!remainingPrompt) {
    throw new Error("The prompt is missing the patient's full name.");
  }

  const nameParts = remainingPrompt.split(" ").filter(Boolean);
  if (nameParts.length < 2) {
    throw new Error(
      "Please provide both a first name and a last name for the patient.",
    );
  }

  const [firstName, ...lastNameParts] = nameParts;
  if (!firstName || !lastNameParts.length) {
    throw new Error(
      "Please provide both a first name and a last name for the patient.",
    );
  }

  return {
    fullName: remainingPrompt,
    firstName,
    lastName: lastNameParts.join(" "),
  };
};

const extractAge = (prompt: string) => {
  const ageMatchers = [
    /\b(\d{1,3})\s*(?:years?\s+old|year-old|yo|y\/o)\b/i,
    /\baged\s+(\d{1,3})\b/i,
    /\bage\s+(\d{1,3})\b/i,
  ];

  for (const matcher of ageMatchers) {
    const match = prompt.match(matcher);
    const age = match?.[1] ? Number.parseInt(match[1], 10) : Number.NaN;
    if (Number.isFinite(age) && age > 0 && age < 130) {
      return age;
    }
  }

  throw new Error(
    "The prompt must include the patient's age, for example: '57 years old'.",
  );
};

const parseOnsetPhrase = (phrase: string, now: Date) => {
  const normalizedPhrase = stripTrailingPunctuation(
    phrase.replace(/^on\s+/i, ""),
  ).toLowerCase();

  const relativeValueMatchers: ReadonlyArray<
    readonly [RegExp, (amount: number) => Date]
  > = [
    [/^(\d+)\s+days?\s+ago$/, (amount) => subDays(now, amount)],
    [/^(\d+)\s+weeks?\s+ago$/, (amount) => subWeeks(now, amount)],
    [/^(\d+)\s+months?\s+ago$/, (amount) => subMonths(now, amount)],
    [/^(\d+)\s+years?\s+ago$/, (amount) => subYears(now, amount)],
  ];

  if (normalizedPhrase === "today") {
    return startOfDay(now).toISOString();
  }

  if (normalizedPhrase === "yesterday") {
    return startOfDay(subDays(now, 1)).toISOString();
  }

  if (normalizedPhrase === "last week") {
    return startOfDay(subWeeks(now, 1)).toISOString();
  }

  if (normalizedPhrase === "last month") {
    return startOfDay(subMonths(now, 1)).toISOString();
  }

  if (normalizedPhrase === "last year") {
    return startOfDay(subYears(now, 1)).toISOString();
  }

  for (const [matcher, dateFactory] of relativeValueMatchers) {
    const match = normalizedPhrase.match(matcher);
    if (match?.[1]) {
      return startOfDay(dateFactory(Number.parseInt(match[1], 10))).toISOString();
    }
  }

  const isoDate = parseISO(normalizedPhrase);
  if (isValid(isoDate)) {
    return startOfDay(isoDate).toISOString();
  }

  for (const formatString of ONSET_FORMATS) {
    const parsedDate = parse(normalizedPhrase, formatString, now);
    if (isValid(parsedDate)) {
      return startOfDay(parsedDate).toISOString();
    }
  }

  throw new Error(
    `Could not understand the condition start date '${phrase}'. Try phrases like 'last week', '2 months ago', or '2026-03-01'.`,
  );
};

const extractConditions = (prompt: string, now: Date): ParsedCondition[] => {
  const normalizedPrompt = normalizeWhitespace(prompt);
  const loweredPrompt = normalizedPrompt.toLowerCase();
  const withIndex = loweredPrompt.indexOf(" with ");
  if (withIndex === -1) {
    throw new Error(
      "The prompt must describe at least one condition using a phrase like 'with high cholesterol'.",
    );
  }

  const tail = normalizedPrompt.slice(withIndex + " with ".length).trim();
  const onsetMatch = tail.match(/\b(?:that\s+)?started\s+(.+?)(?=$|[.!?;])/i);
  const onsetDateTime =
    onsetMatch?.[1] !== undefined ? parseOnsetPhrase(onsetMatch[1], now) : undefined;

  const conditionsSegment = stripTrailingPunctuation(
    onsetMatch?.index !== undefined ? tail.slice(0, onsetMatch.index) : tail,
  );
  if (!conditionsSegment) {
    throw new Error("The prompt is missing the condition description.");
  }

  const conditions = conditionsSegment
    .replace(/\s+(?:and|&)\s+/gi, ",")
    .split(",")
    .map((condition) =>
      stripTrailingPunctuation(
        condition.replace(/^(?:a|an|the)\s+/i, "").trim(),
      ),
    )
    .filter(Boolean)
    .map<ParsedCondition>((text) => ({ text, onsetDateTime }));

  if (!conditions.length) {
    throw new Error("The prompt is missing the condition description.");
  }

  return conditions;
};

export const parsePatientWithConditionsPrompt = (
  prompt: string,
  now: Date = new Date(),
): ParsedPatientWithConditions => {
  const name = extractNameSegment(prompt);
  const age = extractAge(prompt);
  const birthDate = format(startOfDay(subYears(now, age)), "yyyy-MM-dd");
  const conditions = extractConditions(prompt, now);

  return {
    ...name,
    birthDate,
    conditions,
  };
};

export const buildPatientResource = (
  patient: ParsedPatientWithConditions,
): fhirR4.Patient => ({
  resourceType: "Patient",
  name: [
    {
      use: "official",
      family: patient.lastName,
      given: [patient.firstName],
      text: patient.fullName,
    },
  ],
  birthDate: patient.birthDate,
});

export const buildConditionResource = (
  patientId: string,
  patientName: string,
  condition: ParsedCondition,
): fhirR4.Condition => ({
  resourceType: "Condition",
  clinicalStatus: {
    coding: [
      {
        system: "http://terminology.hl7.org/CodeSystem/condition-clinical",
        code: "active",
        display: "Active",
      },
    ],
    text: "Active",
  },
  verificationStatus: {
    coding: [
      {
        system: "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        code: "confirmed",
        display: "Confirmed",
      },
    ],
    text: "Confirmed",
  },
  code: {
    text: condition.text,
  },
  subject: {
    reference: `Patient/${patientId}`,
    display: patientName,
  },
  onsetDateTime: condition.onsetDateTime,
});
