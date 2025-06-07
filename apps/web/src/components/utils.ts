import type { Verdict } from "@/lib/event-schema";
import type {
  ContextualSentence,
  DisambiguatedContentData,
  PotentialClaimData,
  SelectedContentData,
} from "@/lib/store";
import type { UIValidatedClaim } from "@/types";

// Define type for the map value to avoid 'any'
type SentenceData = {
  original: ContextualSentence;
  selected: SelectedContentData[];
  disambiguated: DisambiguatedContentData[];
  potentialClaims: PotentialClaimData[];
  validatedClaims: UIValidatedClaim[];
  verdicts: Verdict[];
};

// Helper function to create a map from original sentence ID to its derivatives
export const createDerivativesMap = (
  contextualSentences: ContextualSentence[],
  selectedContents: SelectedContentData[],
  disambiguatedContents: DisambiguatedContentData[],
  potentialClaims: PotentialClaimData[],
  validatedClaims: UIValidatedClaim[],
  claimVerdicts: Verdict[]
) => {
  const map = new Map<number, SentenceData>();

  // Initialize map with contextual sentences
  for (const sentence of contextualSentences) {
    map.set(sentence.id, {
      original: sentence,
      selected: [],
      disambiguated: [],
      potentialClaims: [],
      validatedClaims: [],
      verdicts: [],
    });
  }

  // Associate selected contents with original sentences
  for (const content of selectedContents) {
    const originalSentence = contextualSentences.find(
      (s) => s.text === content.originalSentenceText
    );
    if (originalSentence && map.has(originalSentence.id)) {
      const data = map.get(originalSentence.id);
      if (data) {
        data.selected.push(content);
      }
    }
  }

  // Associate disambiguated contents
  for (const content of disambiguatedContents) {
    const originalSentence = contextualSentences.find(
      (s) => s.text === content.originalSentenceText
    );
    if (originalSentence && map.has(originalSentence.id)) {
      const data = map.get(originalSentence.id);
      if (data) {
        data.disambiguated.push(content);
      }
    }
  }

  // Associate potential claims
  for (const claim of potentialClaims) {
    const originalSentence = contextualSentences.find(
      (s) => s.text === claim.originalSentenceText
    );
    if (originalSentence && map.has(originalSentence.id)) {
      const data = map.get(originalSentence.id);
      if (data) {
        data.potentialClaims.push(claim);
      }
    }
  }

  // Associate validated claims
  for (const claim of validatedClaims) {
    const originalSentenceId = claim.originalIndex;
    if (map.has(originalSentenceId)) {
      const data = map.get(originalSentenceId);
      if (data) {
        data.validatedClaims.push(claim);
      }
    }
  }

  // Associate verdicts
  for (const verdict of claimVerdicts) {
    const matchingValidatedClaim = validatedClaims.find(
      (vc) => vc.claimText === verdict.claim_text
    );

    if (matchingValidatedClaim) {
      const originalSentenceId = matchingValidatedClaim.originalIndex;
      if (map.has(originalSentenceId)) {
        const data = map.get(originalSentenceId);
        if (data) {
          data.verdicts.push(verdict);
        }
      }
    }
  }

  return map;
};

export const getCurrentStageMessage = (
  claimVerdicts: Verdict[],
  validatedClaims: UIValidatedClaim[],
  potentialClaims: PotentialClaimData[],
  disambiguatedContents: DisambiguatedContentData[],
  selectedContents: SelectedContentData[]
): string => {
  if (claimVerdicts.length > 0) {
    return "Finalizing fact check report...";
  }

  if (validatedClaims.length > 0) {
    return "Verifying claims against reliable sources...";
  }

  if (potentialClaims.length > 0) {
    return "Validating potential claims...";
  }

  if (disambiguatedContents.length > 0) {
    return "Extracting factual claims from content...";
  }

  if (selectedContents.length > 0) {
    return "Disambiguating selected content...";
  }

  return "Analyzing answer sentences...";
};
