import type {
  AgentUpdatesEvent,
  Evidence,
  ProcessedAgentUpdateData,
  UIValidatedClaim,
  Verdict,
} from "@/types";
import {
  type ContextualSentence,
  type DisambiguatedContent,
  type FactCheckReport,
  type PotentialClaim,
  type SelectedContent,
  type ValidatedClaim,
  parseSSEEventData,
} from "./event-schema";

const toUIValidatedClaim = (claim: ValidatedClaim): UIValidatedClaim => ({
  claimText: claim.claim_text,
  isValid: claim.is_complete_declarative,
  originalSentence: claim.original_sentence,
  originalIndex: claim.original_index,
  sourceDisambiguatedSentence: claim.disambiguated_sentence,
});

const toUIFactCheckReport = (report: FactCheckReport) => ({
  question: report.question,
  answer: report.answer,
  claims_verified: report.claims_verified,
  summary: report.summary,
  verified_claims: report.verified_claims,
  timestamp: new Date(report.timestamp),
});

/**
 * Process a contextual sentence event from the sentence splitter
 */
const processContextualSentence = (
  item: ContextualSentence
): ProcessedAgentUpdateData => ({
  type: "ContextualSentenceAdded",
  data: {
    id: item.original_index,
    text: item.original_sentence,
  },
});

/**
 * Process a selected content event
 */
const processSelectedContent = (
  item: SelectedContent
): ProcessedAgentUpdateData => ({
  type: "SelectedContentAdded",
  data: {
    id: item.original_context_item.original_index,
    processedText: item.processed_sentence,
    originalSentenceText: item.original_context_item.original_sentence,
  },
});

/**
 * Process a disambiguated content event
 */
const processDisambiguatedContent = (
  item: DisambiguatedContent
): ProcessedAgentUpdateData => ({
  type: "DisambiguatedContentAdded",
  data: {
    id: item.original_selected_item.original_context_item.original_index,
    disambiguatedText: item.disambiguated_sentence,
    originalSentenceText:
      item.original_selected_item.original_context_item.original_sentence,
  },
});

/**
 * Process a potential claim event
 */
const processPotentialClaim = (
  item: PotentialClaim
): ProcessedAgentUpdateData => ({
  type: "PotentialClaimAdded",
  data: {
    originalSentenceId: item.original_index,
    originalSentenceText: item.original_sentence,
    claim: { claimText: item.claim_text },
    sourceDisambiguatedSentenceText: item.disambiguated_sentence,
  },
});

/**
 * Process a validated claim event
 */
const processValidatedClaim = (
  item: ValidatedClaim
): ProcessedAgentUpdateData => ({
  type: "ValidatedClaimAdded",
  data: toUIValidatedClaim(item),
});

type NodeStateItem =
  | ContextualSentence
  | SelectedContent
  | DisambiguatedContent
  | PotentialClaim
  | ValidatedClaim;

const processExtractClaimsNodeEvents = (
  topLevelNodeKey: string,
  stateKey: string,
  items: NodeStateItem[]
): ProcessedAgentUpdateData[] => {
  const output: ProcessedAgentUpdateData[] = [];

  for (const rawItem of items) {
    const nodeStateKey = `${topLevelNodeKey}:${stateKey}`;

    switch (nodeStateKey) {
      case "sentence_splitter:contextual_sentences":
        output.push(processContextualSentence(rawItem as ContextualSentence));
        break;

      case "selection:selected_contents":
        output.push(processSelectedContent(rawItem as SelectedContent));
        break;

      case "disambiguation:disambiguated_contents":
        output.push(
          processDisambiguatedContent(rawItem as DisambiguatedContent)
        );
        break;

      case "decomposition:potential_claims":
        output.push(processPotentialClaim(rawItem as PotentialClaim));
        break;

      case "validation:validated_claims":
        output.push(processValidatedClaim(rawItem as ValidatedClaim));
        break;

      default:
        break;
    }
  }

  return output;
};

interface ClaimVerifierNodeData {
  queries?: string[];
  evidence?: Evidence[];
  verdict?: {
    claim_text: string;
    source_text: string;
    result:
      | "Supported"
      | "Refuted"
      | "Insufficient Information"
      | "Conflicting Evidence";
    reasoning: string;
    sources: Array<{ url: string; text: string; title?: string | null }>;
  };
}

const processClaimVerifierEvents = (
  topLevelNodeKey: string,
  nodeOrStateData: ClaimVerifierNodeData
): ProcessedAgentUpdateData[] => {
  const output: ProcessedAgentUpdateData[] = [];

  switch (topLevelNodeKey) {
    case "generate_search_queries":
      if (nodeOrStateData.queries?.length) {
        for (const query of nodeOrStateData.queries) {
          output.push({ type: "SearchQueryGenerated", data: { query } });
        }
      }
      break;

    case "retrieve_evidence":
      if (nodeOrStateData.evidence?.length) {
        output.push({
          type: "EvidenceRetrieved",
          data: { evidence: nodeOrStateData.evidence },
        });
      }
      break;

    case "evaluate_evidence":
      if (nodeOrStateData.verdict) {
        const receivedVerdict = nodeOrStateData.verdict;

        const verdict: Verdict = {
          claim_text: receivedVerdict.claim_text,
          disambiguated_sentence: receivedVerdict.source_text,
          result: receivedVerdict.result,
          reasoning: receivedVerdict.reasoning,
          sources: receivedVerdict.sources,
        };

        output.push({ type: "ClaimVerificationResult", data: verdict });
      }
      break;

    default:
      break;
  }

  return output;
};

interface FactCheckerNodeData {
  extracted_claims?: ValidatedClaim[];
  verification_results?: Verdict[];
  final_report?: FactCheckReport;
}

const processFactCheckerEvents = (
  topLevelNodeKey: string,
  nodeOrStateData: FactCheckerNodeData
): ProcessedAgentUpdateData[] => {
  const output: ProcessedAgentUpdateData[] = [];

  switch (topLevelNodeKey) {
    case "extract_claims_node":
      if (nodeOrStateData.extracted_claims?.length) {
        const claims = nodeOrStateData.extracted_claims.map(toUIValidatedClaim);
        output.push({ type: "ExtractedClaimsProvided", data: { claims } });
      }
      break;

    case "claim_verifier":
      if (nodeOrStateData.verification_results?.length) {
        for (const verdict of nodeOrStateData.verification_results) {
          output.push({ type: "ClaimVerificationResult", data: verdict });
        }
      }
      break;

    case "generate_report_node":
      if (nodeOrStateData.final_report) {
        output.push({
          type: "FactCheckReportGenerated",
          data: toUIFactCheckReport(nodeOrStateData.final_report),
        });
      }
      break;

    default:
      break;
  }

  return output;
};

interface NodeDataMap {
  [key: string]: Record<string, unknown>;
}

const processUpdatesEvent = (
  updatesEvent: AgentUpdatesEvent,
  sourceNodeInfo: string | null
): ProcessedAgentUpdateData[] => {
  const output: ProcessedAgentUpdateData[] = [];
  const nodeDataMap = updatesEvent.data as NodeDataMap;

  for (const topLevelNodeKey in nodeDataMap) {
    if (Object.hasOwn(nodeDataMap, topLevelNodeKey)) {
      const nodeOrStateData = nodeDataMap[topLevelNodeKey];

      if (sourceNodeInfo?.startsWith("extract_claims_node")) {
        if (
          typeof nodeOrStateData === "object" &&
          nodeOrStateData !== null &&
          !Array.isArray(nodeOrStateData)
        ) {
          for (const stateKey in nodeOrStateData) {
            if (Object.hasOwn(nodeOrStateData, stateKey)) {
              const items = nodeOrStateData[stateKey] as NodeStateItem[];
              if (Array.isArray(items)) {
                output.push(
                  ...processExtractClaimsNodeEvents(
                    topLevelNodeKey,
                    stateKey,
                    items
                  )
                );
              }
            }
          }
        }
      } else if (sourceNodeInfo?.startsWith("claim_verifier")) {
        output.push(
          ...processClaimVerifierEvents(
            topLevelNodeKey,
            nodeOrStateData as ClaimVerifierNodeData
          )
        );
      } else if (!sourceNodeInfo || sourceNodeInfo.startsWith("fact_checker")) {
        output.push(
          ...processFactCheckerEvents(
            topLevelNodeKey,
            nodeOrStateData as FactCheckerNodeData
          )
        );
      }
    }
  }

  return output;
};

/**
 * Process an SSE event from the agent and convert it to UI-friendly data
 */
export const processAgentSSEEvent = (
  eventData: string
): ProcessedAgentUpdateData[] => {
  const output: ProcessedAgentUpdateData[] = [];

  try {
    const streamEvent = parseSSEEventData(eventData);

    if (streamEvent.event === "metadata" && "run_id" in streamEvent.data) {
      output.push({
        type: "AgentRunMetadata",
        data: { runId: streamEvent.data.run_id },
      });
    } else if (streamEvent.event === "error" && "message" in streamEvent.data) {
      console.error("Error event received:", streamEvent.data.message);
    } else if (streamEvent.event.startsWith("updates")) {
      const updatesEvent = streamEvent as unknown as AgentUpdatesEvent;
      const eventParts = streamEvent.event.split("|");
      const sourceNodeInfo = eventParts.length > 1 ? eventParts[1] : null;
      output.push(...processUpdatesEvent(updatesEvent, sourceNodeInfo));
    }
  } catch (e) {
    console.error("Failed to process SSE event:", e);
  }

  return output;
};
