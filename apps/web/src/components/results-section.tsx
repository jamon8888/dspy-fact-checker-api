"use client";

import { useFactCheckerResults } from "@/lib/store";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircle } from "lucide-react";
import { FactChecker } from "./fact-checker";

const EmptyState = () => (
  <div className="px-6 py-12 text-center" aria-live="polite">
    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-neutral-100 border">
      <MessageCircle
        className="text-neutral-400"
        size={24}
        aria-hidden="true"
      />
    </div>
    <h2 className="mb-1 font-medium text-neutral-900">
      No answer submitted yet
    </h2>
    <p className="text-neutral-500 text-sm">
      Enter a question and answer, then click "Verify"
    </p>
  </div>
);

interface AnimatedPanelProps {
  children: React.ReactNode;
  keyName: string;
  className?: string;
}

const AnimatedPanel = ({
  children,
  keyName,
  className,
}: AnimatedPanelProps) => (
  <motion.div
    key={keyName}
    initial={{ opacity: 0, scale: 0.98 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.98 }}
    transition={{ duration: 0.3 }}
    className={className}
  >
    {children}
  </motion.div>
);

export const ResultsSection = () => {
  const {
    submittedAnswer,
    contextualSentences,
    selectedContents,
    disambiguatedContents,
    potentialClaims,
    validatedClaims,
    claimVerdicts,
    isLoading,
  } = useFactCheckerResults();

  return (
    <motion.section
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      aria-label="Fact check results"
      className="lg:row-span-2 flex-grow flex flex-col"
      aria-live="polite"
      aria-busy={isLoading}
    >
      <AnimatePresence mode="wait">
        {submittedAnswer ? (
          <AnimatedPanel
            keyName="results"
            className="flex flex-col w-full flex-grow"
          >
            <article className="w-full flex-grow">
              <h2 className="sr-only">Fact Check Results</h2>
              <FactChecker
                contextualSentences={contextualSentences}
                selectedContents={selectedContents}
                disambiguatedContents={disambiguatedContents}
                potentialClaims={potentialClaims}
                validatedClaims={validatedClaims}
                claimVerdicts={claimVerdicts}
                isLoading={isLoading}
              />
            </article>
          </AnimatedPanel>
        ) : (
          <AnimatedPanel
            keyName="empty-state"
            className="flex w-full flex-grow items-center justify-center rounded-lg border border-neutral-200 border-dashed bg-neutral-50/50 shadow-sm"
          >
            <EmptyState />
          </AnimatedPanel>
        )}
      </AnimatePresence>
    </motion.section>
  );
};
