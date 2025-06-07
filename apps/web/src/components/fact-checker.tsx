"use client";

import type { Verdict } from "@/lib/event-schema";
import type {
  ContextualSentence,
  DisambiguatedContentData,
  PotentialClaimData,
  SelectedContentData,
} from "@/lib/store";
import { cn } from "@/lib/utils";
import type { UIValidatedClaim } from "@/types";
import { motion } from "framer-motion";
import { useMemo, useState } from "react";

import { LoadingState } from "./loading-state";
import { ProcessedAnswer } from "./processed-answer";
import { ProgressBar } from "./progress-bar";
import { SourcePills } from "./source-pills";
import { createDerivativesMap } from "./utils";
import { VerdictProgress } from "./verdict-progress";
import { VerdictSummary } from "./verdict-summary";

interface FactCheckerProps {
  contextualSentences: ContextualSentence[];
  selectedContents: SelectedContentData[];
  disambiguatedContents: DisambiguatedContentData[];
  potentialClaims: PotentialClaimData[];
  validatedClaims: UIValidatedClaim[];
  claimVerdicts: Verdict[];
  isLoading: boolean;
}

export const FactChecker = ({
  contextualSentences,
  selectedContents,
  disambiguatedContents,
  potentialClaims,
  validatedClaims,
  claimVerdicts,
  isLoading,
}: FactCheckerProps) => {
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);

  // Create a map from original sentences to their derivative data
  const derivativesMap = useMemo(
    () =>
      createDerivativesMap(
        contextualSentences,
        selectedContents,
        disambiguatedContents,
        potentialClaims,
        validatedClaims,
        claimVerdicts
      ),
    [
      contextualSentences,
      selectedContents,
      disambiguatedContents,
      potentialClaims,
      validatedClaims,
      claimVerdicts,
    ]
  );

  // Prepare progress stages data
  const progressStages = [
    { name: "Contextual", count: contextualSentences.length },
    { name: "Selected", count: selectedContents.length },
    { name: "Disambiguated", count: disambiguatedContents.length },
    { name: "Claims", count: potentialClaims.length },
    { name: "Validated", count: validatedClaims.length },
    { name: "Verdicts", count: claimVerdicts.length },
  ];

  // Convert the map to an array for rendering
  const sentenceEntries = useMemo(
    () => Array.from(derivativesMap.entries()),
    [derivativesMap]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("w-full bg-white")}
    >
      {contextualSentences.length === 0 ? (
        <>
          <ProgressBar stages={progressStages} isLoading={isLoading} />
          <LoadingState message="Initializing verification..." />
        </>
      ) : (
        <>
          <ProgressBar stages={progressStages} isLoading={isLoading} />
          {claimVerdicts.length > 0 && <SourcePills verdicts={claimVerdicts} />}
          <div>
            {claimVerdicts.length > 0 && (
              <VerdictProgress verdicts={claimVerdicts} isLoading={isLoading} />
            )}
            <h3 className="my-2.5 mt-6 font-medium text-neutral-900 text-sm">
              Processed Answer
            </h3>
            <ProcessedAnswer
              sentenceEntries={sentenceEntries}
              expandedCitation={expandedCitation}
              setExpandedCitation={setExpandedCitation}
            />
          </div>
        </>
      )}
      <VerdictSummary verdicts={claimVerdicts} isLoading={isLoading} />
    </motion.div>
  );
};
