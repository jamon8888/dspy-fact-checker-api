import { z } from "zod";

// Basic data schemas - direct mapping to backend models
export const contextualSentenceSchema = z.object({
  original_sentence: z.string(),
  context_for_llm: z.string().optional(),
  question: z.string().optional(),
  metadata: z.string().optional(),
  original_index: z.number(),
});

export const selectedContentSchema = z.object({
  original_context_item: contextualSentenceSchema,
  processed_sentence: z.string(),
});

export const disambiguatedContentSchema = z.object({
  original_selected_item: selectedContentSchema,
  disambiguated_sentence: z.string(),
});

export const potentialClaimSchema = z.object({
  claim_text: z.string(),
  disambiguated_sentence: z.string(),
  original_sentence: z.string(),
  original_index: z.number(),
});

export const validatedClaimSchema = z.object({
  claim_text: z.string(),
  is_complete_declarative: z.boolean(),
  disambiguated_sentence: z.string(),
  original_sentence: z.string(),
  original_index: z.number(),
});

export const evidenceSchema = z.object({
  url: z.string(),
  text: z.string(),
  title: z.string().nullable().optional(),
});

export const verificationResultEnum = z.enum([
  "Supported",
  "Refuted",
  "Insufficient Information",
  "Conflicting Evidence",
]);

export type VerificationResult =
  | "Supported"
  | "Refuted"
  | "Insufficient Information"
  | "Conflicting Evidence";

export const verdictSchema = z.object({
  claim_text: z.string(),
  disambiguated_sentence: z.string(),
  result: verificationResultEnum,
  reasoning: z.string(),
  sources: z.array(evidenceSchema).default([]),
});

export const factCheckReportSchema = z.object({
  question: z.string(),
  answer: z.string(),
  claims_verified: z.number(),
  verified_claims: z.array(verdictSchema),
  summary: z.string(),
  timestamp: z.string(), // ISO date string
});

export const metadataEventSchema = z.object({
  event: z.literal("metadata"),
  data: z.object({
    run_id: z.string(),
  }),
});

export const errorEventSchema = z.object({
  event: z.literal("error"),
  data: z.object({
    message: z.string(),
    run_id: z.string(),
  }),
});

export const updatesEventSchema = z.object({
  event: z.string(),
  data: z.record(z.any()),
});

export const sseEventSchema = z.union([
  metadataEventSchema,
  errorEventSchema,
  updatesEventSchema,
]);

export type ContextualSentence = z.infer<typeof contextualSentenceSchema>;
export type SelectedContent = z.infer<typeof selectedContentSchema>;
export type DisambiguatedContent = z.infer<typeof disambiguatedContentSchema>;
export type PotentialClaim = z.infer<typeof potentialClaimSchema>;
export type ValidatedClaim = z.infer<typeof validatedClaimSchema>;
export type Evidence = z.infer<typeof evidenceSchema>;
export type Verdict = z.infer<typeof verdictSchema>;
export type FactCheckReport = z.infer<typeof factCheckReportSchema>;
export type SSEEvent = z.infer<typeof sseEventSchema>;

export const parseSSEEventData = (eventData: string): SSEEvent => {
  try {
    const parsed = JSON.parse(eventData);

    // Basic validation before attempting to parse with Zod
    if (!parsed || typeof parsed !== "object") {
      throw new Error("Invalid event data: not an object");
    }

    if (!parsed.event || typeof parsed.event !== "string") {
      throw new Error(
        "Invalid event data: missing or invalid 'event' property"
      );
    }

    if (parsed.data === undefined) {
      throw new Error("Invalid event data: missing 'data' property");
    }

    return sseEventSchema.parse(parsed);
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Failed to parse SSE event data: ${error.message}`, error);
      console.error("Problematic event data:", eventData);
    } else {
      console.error("Unknown error parsing SSE event data");
    }
    throw error;
  }
};
