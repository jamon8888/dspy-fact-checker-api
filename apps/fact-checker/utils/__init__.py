"""Utility functions for the fact-checking system.

Common tools shared across all components.
"""

from .llm import call_llm_with_structured_output, process_with_voting
from .text import remove_following_sentences

__all__ = [
    # LLM utilities
    "call_llm_with_structured_output",
    "process_with_voting",
    # Text utilities
    "remove_following_sentences",
]

# This file makes 'utils' a Python package.
