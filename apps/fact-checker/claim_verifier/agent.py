import logging
from typing import Literal

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph, Send

from claim_verifier.nodes import (
    evaluate_evidence_node,
    generate_search_queries_node,
    retrieve_evidence_node,
)
from claim_verifier.schemas import ClaimVerifierState

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def query_distributor(
    state: ClaimVerifierState,
) -> Literal["__end__"] | list[Send]:
    """Distribute queries to retrieve evidence.

    Args:
        state: Current workflow state

    Returns:
        Either END or a list of Send objects to retrieve evidence
    """
    queries = state.queries

    if not queries:
        logger.info("No queries generated, ending.")
        return END

    logger.info(f"Distributing {len(queries)} queries for evidence retrieval.")
    return [Send("retrieve_evidence", {"query": query}) for query in queries]


def create_graph() -> CompiledStateGraph:
    """Set up the claim verification workflow graph.

    The pipeline follows these steps:
    1. Generate search queries for a claim
    2. Distribute queries for evidence retrieval
    3. Retrieve evidence from web searches
    4. Evaluate evidence to determine a verdict
    """
    workflow = StateGraph(ClaimVerifierState)

    # Add nodes
    workflow.add_node("generate_search_queries", generate_search_queries_node)
    workflow.add_node("retrieve_evidence", retrieve_evidence_node)
    workflow.add_node("evaluate_evidence", evaluate_evidence_node)

    # Set entry point
    workflow.set_entry_point("generate_search_queries")

    # Connect the nodes in sequence
    workflow.add_conditional_edges(
        "generate_search_queries", query_distributor, ["retrieve_evidence", END]
    )
    workflow.add_edge("retrieve_evidence", "evaluate_evidence")

    # Set finish point
    workflow.set_finish_point("evaluate_evidence")

    return workflow.compile()


graph = create_graph()
