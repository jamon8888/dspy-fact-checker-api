"use client";

import type {
  AgentSSEStreamEvent,
  ProcessedAgentUpdateData,
  UIValidatedClaim,
} from "@/types";
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { processAgentSSEEvent } from "./agent-processor";
import {
  type Evidence,
  type SSEEvent,
  type Verdict,
  parseSSEEventData,
} from "./event-schema";

// ContextualSentence as processed for the store
export interface ContextualSentence {
  id: number;
  text: string;
}

// For SelectedContentAdded events
export interface SelectedContentData {
  id: number;
  processedText: string;
  originalSentenceText: string;
}

// For DisambiguatedContentAdded events
export interface DisambiguatedContentData {
  id: number;
  disambiguatedText: string;
  originalSentenceText: string;
}

// For PotentialClaimAdded events
export interface UIClaim {
  claimText: string;
}
export interface PotentialClaimData {
  originalSentenceId: number;
  originalSentenceText: string;
  claim: UIClaim;
  sourceDisambiguatedSentenceText: string;
}

// UI version of FactCheckReport with parsed date
export interface UIFactCheckReport {
  question: string;
  answer: string;
  claims_verified: number;
  verified_claims: Verdict[];
  summary: string;
  timestamp: Date;
}

interface FactCheckerState {
  // User inputs
  question: string;
  answer: string;
  submittedAnswer: string | null;

  // UI State
  isLoading: boolean;

  // Processing results - raw events and specific data types
  rawServerEvents: SSEEvent[];
  contextualSentences: ContextualSentence[];
  selectedContents: SelectedContentData[];
  disambiguatedContents: DisambiguatedContentData[];
  potentialClaims: PotentialClaimData[];
  validatedClaims: UIValidatedClaim[];
  searchQueriesLog: string[];
  evidenceBatchesLog: Evidence[][];
  claimVerdicts: Verdict[];
  factCheckReport: UIFactCheckReport | null;
}

interface FactCheckerActions {
  // Input actions
  setQuestion: (question: string) => void;
  setAnswer: (answer: string) => void;

  // Process actions
  startVerification: () => Promise<void>;
  resetState: () => void;

  // Update actions
  setIsLoading: (isLoading: boolean) => void;
  addRawServerEvent: (event: AgentSSEStreamEvent) => void;
  addContextualSentence: (sentence: ContextualSentence) => void;
  addSelectedContent: (content: SelectedContentData) => void;
  addDisambiguatedContent: (content: DisambiguatedContentData) => void;
  addPotentialClaim: (claim: PotentialClaimData) => void;
  addValidatedClaim: (claim: UIValidatedClaim) => void;
  addSearchQuery: (query: string) => void;
  addEvidenceBatch: (evidence: Evidence[]) => void;
  addClaimVerdict: (verdict: Verdict) => void;
  setFactCheckReport: (report: UIFactCheckReport) => void;

  // Process SSE events
  processEventData: (eventData: string) => void;
  handleProcessedItem: (item: ProcessedAgentUpdateData) => void;
}

type FactCheckerStore = FactCheckerState & FactCheckerActions;

/**
 * Helper function to process SSE buffer chunks
 * Extracts and processes complete SSE messages from the buffer
 */
const processBufferChunk = (
  buffer: string,
  processEventData: (data: string) => void
): void => {
  const messages = buffer.split("\n\n");
  // Process all complete messages (excluding the last one if it's incomplete)
  for (let i = 0; i < messages.length - 1; i++) {
    const message = messages[i].trim();
    if (!message) continue;

    // Extract data field from SSE format
    let jsonData = "";
    const lines = message.split("\n");
    for (const line of lines) {
      if (line.startsWith("data:")) {
        jsonData += line.substring(5).trim();
      }
    }

    if (jsonData) {
      try {
        processEventData(jsonData);
      } catch (e) {
        console.error("Error processing message:", e, `Message: '${jsonData}'`);
      }
    }
  }
};

export const useFactCheckerStore = create<FactCheckerStore>()(
  devtools(
    (set, get) => ({
      question: "",
      answer: "",
      submittedAnswer: null,
      isLoading: false,
      rawServerEvents: [],
      contextualSentences: [],
      selectedContents: [],
      disambiguatedContents: [],
      potentialClaims: [],
      validatedClaims: [],
      searchQueriesLog: [],
      evidenceBatchesLog: [],
      claimVerdicts: [],
      factCheckReport: null,

      setQuestion: (question) => set({ question }),
      setAnswer: (answer) => set({ answer }),

      resetState: () =>
        set({
          rawServerEvents: [],
          submittedAnswer: null,
          contextualSentences: [],
          selectedContents: [],
          disambiguatedContents: [],
          potentialClaims: [],
          validatedClaims: [],
          searchQueriesLog: [],
          evidenceBatchesLog: [],
          claimVerdicts: [],
          factCheckReport: null,
        }),

      setIsLoading: (isLoading) => set({ isLoading }),

      addRawServerEvent: (event) =>
        set((state) => ({
          rawServerEvents: [...state.rawServerEvents, event],
        })),

      addContextualSentence: (sentence) =>
        set((state) => {
          // Ensure no duplicates based on id
          if (!state.contextualSentences.find((s) => s.id === sentence.id)) {
            return {
              contextualSentences: [
                ...state.contextualSentences,
                sentence,
              ].sort((a, b) => a.id - b.id),
            };
          }
          return {}; // No change
        }),

      addSelectedContent: (content) =>
        set((state) => ({
          selectedContents: [...state.selectedContents, content],
        })),

      addDisambiguatedContent: (content) =>
        set((state) => ({
          disambiguatedContents: [...state.disambiguatedContents, content],
        })),

      addPotentialClaim: (claim) =>
        set((state) => ({
          potentialClaims: [...state.potentialClaims, claim],
        })),

      addValidatedClaim: (claim) =>
        set((state) => {
          const isDuplicate = state.validatedClaims.some(
            (existingClaim) =>
              existingClaim.claimText === claim.claimText &&
              existingClaim.originalIndex === claim.originalIndex
          );

          if (!isDuplicate) {
            return {
              validatedClaims: [...state.validatedClaims, claim],
            };
          }
          return {};
        }),

      addSearchQuery: (query) =>
        set((state) => ({
          searchQueriesLog: [...state.searchQueriesLog, query],
        })),

      addEvidenceBatch: (evidence) =>
        set((state) => ({
          evidenceBatchesLog: [...state.evidenceBatchesLog, evidence],
        })),

      addClaimVerdict: (verdict) =>
        set((state) => {
          const isDuplicate = state.claimVerdicts.some(
            (existingVerdict) =>
              existingVerdict.claim_text === verdict.claim_text
          );

          if (!isDuplicate) {
            return {
              claimVerdicts: [...state.claimVerdicts, verdict],
            };
          }
          return {};
        }),

      setFactCheckReport: (report) => set({ factCheckReport: report }),

      startVerification: async () => {
        const { question, answer, resetState, processEventData } = get();

        if (!question || !answer) {
          return;
        }

        resetState();
        set({ submittedAnswer: answer, isLoading: true });

        try {
          const response = await fetch("/api/agent/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, answer }),
          });

          if (!response.ok || !response.body) {
            throw new Error("Network error");
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              set({ isLoading: false });

              // Process any remaining data
              if (buffer.trim()) {
                processBufferChunk(buffer, processEventData);
              }

              break;
            }

            buffer += decoder.decode(value, { stream: true });
            processBufferChunk(buffer, processEventData);

            // Reset buffer to whatever remains after processing
            const lastDelimiterPos = buffer.lastIndexOf("\n\n");
            if (lastDelimiterPos !== -1) {
              buffer = buffer.substring(lastDelimiterPos + 2);
            }
          }
        } catch (error) {
          console.error("Failed to connect to SSE or process stream:", error);
          set((state) => ({
            rawServerEvents: [
              ...state.rawServerEvents,
              {
                event: "error",
                data: {
                  message: (error as Error).message,
                  run_id: "local-error",
                },
              },
            ],
            isLoading: false,
          }));
        }
      },

      processEventData: (eventData) => {
        // Log the raw eventData before parsing
        try {
          // Parse and validate with Zod schema
          const parsedServerEvent = parseSSEEventData(eventData);
          get().addRawServerEvent(parsedServerEvent);

          const processedItems = processAgentSSEEvent(eventData);
          for (const item of processedItems) {
            get().handleProcessedItem(item);
          }
        } catch (error) {
          // Log the problematic eventData here as well
          console.error(
            "Failed to process event data in processEventData:",
            error,
            `Problematic eventData: '${eventData}'`
          );
        }
      },

      handleProcessedItem: (item) => {
        const state = get();

        // Remove this block that adds the entire submitted answer as a single contextual sentence
        // This is causing collision with actual contextual sentences from the backend

        switch (item.type) {
          case "AgentRunMetadata":
            break;

          case "ContextualSentenceAdded":
            state.addContextualSentence(item.data);
            break;

          case "SelectedContentAdded":
            state.addSelectedContent(item.data);
            break;

          case "DisambiguatedContentAdded":
            state.addDisambiguatedContent(item.data);
            break;

          case "PotentialClaimAdded":
            state.addPotentialClaim(item.data);
            break;

          case "ValidatedClaimAdded":
            state.addValidatedClaim(item.data);
            break;

          case "SearchQueryGenerated":
            state.addSearchQuery(item.data.query);
            break;

          case "EvidenceRetrieved":
            state.addEvidenceBatch(item.data.evidence);
            break;

          case "ClaimVerificationResult": {
            state.addClaimVerdict(item.data);
            break;
          }

          case "ExtractedClaimsProvided":
            for (const claim of item.data.claims) {
              state.addValidatedClaim(claim);
            }
            break;

          case "FactCheckReportGenerated":
            state.setFactCheckReport(item.data);
            break;

          default:
            console.warn(
              "Unhandled processed item type:",
              (item as ProcessedAgentUpdateData).type
            );
            break;
        }
      },
    }),
    { name: "fact-checker-store" }
  )
);

export const useFactCheckerInput = () => {
  const store = useFactCheckerStore();

  const clearInputs = () => {
    store.setQuestion("");
    store.setAnswer("");
  };

  return {
    question: store.question,
    setQuestion: store.setQuestion,
    answer: store.answer,
    setAnswer: store.setAnswer,
    isLoading: store.isLoading,
    startVerification: store.startVerification,
    resetState: store.resetState,
    clearInputs,
  };
};

export const useFactCheckerResults = () => {
  const store = useFactCheckerStore();

  return {
    submittedAnswer: store.submittedAnswer,
    isLoading: store.isLoading,
    rawServerEvents: store.rawServerEvents,
    contextualSentences: store.contextualSentences,
    selectedContents: store.selectedContents,
    disambiguatedContents: store.disambiguatedContents,
    potentialClaims: store.potentialClaims,
    validatedClaims: store.validatedClaims,
    searchQueriesLog: store.searchQueriesLog,
    evidenceBatchesLog: store.evidenceBatchesLog,
    claimVerdicts: store.claimVerdicts,
    factCheckReport: store.factCheckReport,
  };
};
