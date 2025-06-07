"""LLM model instances and factory functions.

Provides access to configured language model instances.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from claim_extractor.llm.config import (
    DEFAULT_TEMPERATURE,
    MODEL_NAME,
    MULTI_COMPLETION_TEMPERATURE,
)

# Default LLM instance with zero temperature
openai_llm = init_chat_model(model=MODEL_NAME, temperature=DEFAULT_TEMPERATURE)


def get_llm(completions: int = 1) -> BaseChatModel:
    """Get LLM with appropriate temperature based on completions.

    Args:
        completions: How many completions we need

    Returns:
        Configured LLM instance
    """
    # Use higher temp when doing multiple completions for diversity
    temperature = (
        MULTI_COMPLETION_TEMPERATURE if completions > 1 else DEFAULT_TEMPERATURE
    )

    return init_chat_model(model=MODEL_NAME, temperature=temperature)
