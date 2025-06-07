// Import schema-defined types
import type {
  Evidence as SchemaEvidence,
  FactCheckReport as SchemaFactCheckReport,
  Verdict as SchemaVerdict,
} from "../lib/event-schema";

/**
 * Event Types
 */
export type EventType = "metadata" | "updates" | string;

export interface AgentEvent<T extends EventType, D> {
  event: T;
  data: D;
}

export interface MetadataEventData {
  run_id: string;
  attempt?: number;
}

export type AgentMetadataEvent = AgentEvent<"metadata", MetadataEventData>;

// biome-ignore lint/suspicious/noExplicitAny: <explanation>
export type AgentUpdatesDataContent = Record<string, any>;

export type AgentUpdatesEvent = AgentEvent<string, AgentUpdatesDataContent>;

export type AgentSSEStreamEvent = AgentMetadataEvent | AgentUpdatesEvent;

export type Evidence = SchemaEvidence;
export type Verdict = SchemaVerdict;
export type FactCheckReport = SchemaFactCheckReport;

/**
 * Frontend UI Types
 */
export interface UIOriginalSentence {
  id: number;
  text: string;
}

export interface UISelectedSentence {
  id: number;
  processedText: string;
  originalSentenceText: string;
}

export interface UIDisambiguatedSentence {
  id: number;
  disambiguatedText: string;
  originalSentenceText: string;
}

export interface UIClaim {
  claimText: string;
}

export interface UIValidatedClaim {
  claimText: string;
  originalIndex: number;
  isValid: boolean;
  sourceDisambiguatedSentence?: string;
  originalSentence?: string;
}

export type UIEvidence = Evidence;

export type UIVerdict = Verdict;

export interface UIFactCheckReport {
  question: string;
  answer: string;
  claims_verified: number;
  verified_claims: Verdict[];
  summary: string;
  timestamp: Date; // Parsed for easier use
}

/**
 * Processor Event Types
 */
export type ProcessedAgentUpdateData =
  | { type: "AgentRunMetadata"; data: { runId: string } }
  | { type: "ContextualSentenceAdded"; data: UIOriginalSentence }
  | { type: "SelectedContentAdded"; data: UISelectedSentence }
  | { type: "DisambiguatedContentAdded"; data: UIDisambiguatedSentence }
  | {
      type: "PotentialClaimAdded";
      data: {
        originalSentenceId: number;
        originalSentenceText: string;
        claim: UIClaim;
        sourceDisambiguatedSentenceText: string;
      };
    }
  | { type: "ValidatedClaimAdded"; data: UIValidatedClaim }
  | { type: "ExtractedClaimsProvided"; data: { claims: UIValidatedClaim[] } }
  | { type: "SearchQueryGenerated"; data: { query: string } }
  | { type: "EvidenceRetrieved"; data: { evidence: UIEvidence[] } }
  | { type: "ClaimVerificationResult"; data: UIVerdict }
  | { type: "AllVerificationResultsProvided"; data: { verdicts: UIVerdict[] } }
  | { type: "FactCheckReportGenerated"; data: UIFactCheckReport };
