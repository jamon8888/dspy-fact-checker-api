"""Extract claims node - extracts factual claims from input text.

Uses claim extractor subsystem to identify factual claims in input text.
"""

import logging
from typing import Dict, List

from claim_extractor import ValidatedClaim
from claim_extractor import graph as claim_extractor_graph
from fact_checker.schemas import FactCheckerState

logger = logging.getLogger(__name__)


async def extract_claims_node(
    state: FactCheckerState,
) -> Dict[str, List[ValidatedClaim]]:
    """Extract claims from the input text using the claim_extractor graph.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with extracted_claims key
    """
    logger.info("Starting claim extraction process")

    extractor_payload = {"question": state.question, "answer_text": state.answer}

    try:
        extractor_result = await claim_extractor_graph.ainvoke(extractor_payload)
        validated_claims = extractor_result.get("validated_claims", [])
        logger.info(f"Extracted {len(validated_claims)} validated claims")
        return {"extracted_claims": validated_claims}
    except Exception as e:
        logger.error(f"Error in claim extraction: {str(e)}")
        return {"extracted_claims": []}
