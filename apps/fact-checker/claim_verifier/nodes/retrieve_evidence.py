"""Retrieve evidence node - fetches evidence for claims using Tavily Search.

Uses search queries to retrieve relevant evidence snippets from the web.
"""

import logging
from typing import Dict, List

from langchain_tavily import TavilySearch

from claim_verifier.config import EVIDENCE_RETRIEVAL_CONFIG
from claim_verifier.schemas import Evidence, RetrieveEvidenceInput

logger = logging.getLogger(__name__)

# Retrieval settings
RESULTS_PER_QUERY = EVIDENCE_RETRIEVAL_CONFIG["results_per_query"]
MAX_SNIPPETS = EVIDENCE_RETRIEVAL_CONFIG["max_snippets"]


async def _search_query(query: str) -> List[Evidence]:
    """Execute a search query using Tavily Search and format the results.

    Args:
        query: Search query to execute

    Returns:
        List of evidence snippets from search results
    """
    logger.info(f"Searching with Tavily for: '{query}'")

    try:
        # Initialize Tavily Search
        tavily_search = TavilySearch(
            max_results=RESULTS_PER_QUERY,
            search_depth="basic",
            topic="general",
        )

        # Execute the search
        search_result = await tavily_search.ainvoke(query)

        # Extract evidence from the results
        evidence_list: List[Evidence] = []

        # Parse Tavily search results
        if isinstance(search_result, dict) and "results" in search_result:
            for item in search_result["results"]:
                evidence_list.append(
                    Evidence(
                        url=item.get("url", ""),
                        text=item.get("content", ""),
                        title=item.get("title"),
                    )
                )

        logger.info(
            f"Retrieved {len(evidence_list)} evidence items for query: '{query}'"
        )
        return evidence_list

    except Exception as e:
        logger.error(f"Error searching with Tavily for '{query}': {str(e)}")
        return []


async def retrieve_evidence_node(
    state: RetrieveEvidenceInput,
) -> Dict[str, List[Evidence]]:
    """Retrieve evidence snippets for each search query using Tavily Search.

    Args:
        state: Current workflow state with search queries

    Returns:
        Dictionary with evidence key containing evidence snippets
    """
    if not state["query"]:
        logger.warning("No search queries to process")
        return {"evidence": []}

    # Execute search
    all_evidence = await _search_query(state["query"])

    # Flatten and deduplicate evidence
    seen_urls = set()
    unique_evidence: List[Evidence] = []

    for evidence in all_evidence:
        if evidence.url not in seen_urls:
            seen_urls.add(evidence.url)
            unique_evidence.append(evidence)

    # Respect the maximum number of snippets
    if len(unique_evidence) > MAX_SNIPPETS:
        logger.info(
            f"Limiting from {len(unique_evidence)} to {MAX_SNIPPETS} evidence snippets"
        )
        unique_evidence = unique_evidence[:MAX_SNIPPETS]

    logger.info(f"Retrieved a total of {len(unique_evidence)} unique evidence snippets")
    return {"evidence": [evidence.model_dump() for evidence in unique_evidence]}
