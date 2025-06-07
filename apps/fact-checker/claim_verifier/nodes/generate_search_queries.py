"""Generate search queries node - creates effective search queries for claims.

Generates optimized queries to find evidence related to a claim.
"""

import logging
from typing import Dict, List

from pydantic import BaseModel, Field

from claim_verifier.config import QUERY_GENERATION_CONFIG
from claim_verifier.llm import get_llm
from claim_verifier.prompts import (
    QUERY_GENERATION_HUMAN_PROMPT,
    QUERY_GENERATION_SYSTEM_PROMPT,
    RETRY_QUERY_GENERATION_SYSTEM_PROMPT,
)
from claim_verifier.schemas import ClaimVerifierState
from utils.llm import call_llm_with_structured_output

logger = logging.getLogger(__name__)


class QueryGenerationOutput(BaseModel):
    """Response schema for query generation LLM calls."""

    queries: List[str] = Field(
        description="List of search queries generated for the claim"
    )


async def generate_search_queries_node(
    state: ClaimVerifierState,
) -> Dict[str, List[str]]:
    """Generate effective search queries for a claim.

    Args:
        state: Current workflow state with claim to check

    Returns:
        Dictionary with queries key
    """
    claim = state.claim
    retry_count = state.retry_count
    max_queries = QUERY_GENERATION_CONFIG["max_queries"]

    logger.info(
        f"Generating search queries for claim: '{claim.claim_text}' (Attempt: {retry_count + 1})"
    )

    # Get LLM with the right temperature
    llm = get_llm()

    system_prompt = QUERY_GENERATION_SYSTEM_PROMPT.format(max_queries=max_queries)
    
    if retry_count > 0:
        # Get previous queries and verdict for context
        previous_queries = state.queries
        verdict = state.verdict

        logger.info(
            "Using retry query generation prompt with context from previous attempt."
        )

        # Format previous queries as a numbered list
        formatted_queries = "\n".join(
            [f"{i + 1}. {query}" for i, query in enumerate(previous_queries)]
        )

        # Get reasoning from previous verdict
        verdict_reasoning = (
            verdict.reasoning
            if verdict and verdict.reasoning
            else "No specific reasoning provided."
        )

        # Use the template with the previous context
        system_prompt = RETRY_QUERY_GENERATION_SYSTEM_PROMPT.format(
            previous_queries=formatted_queries, 
            verdict_reasoning=verdict_reasoning,
            max_queries=max_queries
        )

    messages = [
        ("system", system_prompt),
        (
            "human",
            QUERY_GENERATION_HUMAN_PROMPT.format(
                claim_text=claim.claim_text,
                max_queries=max_queries,
            ),
        ),
    ]

    # Call the LLM with structured output schema
    response = await call_llm_with_structured_output(
        llm=llm,
        output_class=QueryGenerationOutput,
        messages=messages,
        context_desc=f"query generation for claim '{claim.claim_text}'",
    )

    if not response or not response.queries:
        logger.warning(f"Failed to generate queries for claim: '{claim.claim_text}'")
        return {"queries": [claim.claim_text]}

    # Limit to max_queries
    queries = response.queries[:max_queries]

    logger.info(
        f"Generated {len(queries)} search queries for claim: '{claim.claim_text}'"
    )
    for idx, query in enumerate(queries):
        logger.debug(f"Query {idx + 1}: {query}")

    return {"queries": queries}
