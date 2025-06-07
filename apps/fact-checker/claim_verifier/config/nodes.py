"""Node configuration settings.

Contains settings for the claim verification pipeline nodes.
"""

# Node settings
QUERY_GENERATION_CONFIG = {
    "temperature": 0.0,  # Zero temp for consistent results
    "max_queries": 3,  # Maximum number of queries to generate
}

EVIDENCE_RETRIEVAL_CONFIG = {
    "results_per_query": 5,  # Number of search results to fetch per query
    "max_snippets": 20,  # Maximum total snippets to process
}

EVIDENCE_EVALUATION_CONFIG = {
    "temperature": 0.0,  # Zero temp for consistent results
}

RETRY_CONFIG = {
    "max_retries": 3,  # Maximum number of retry attempts if information is insufficient
}
