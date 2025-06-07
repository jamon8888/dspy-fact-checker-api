"""LLM model instances and factory functions.

Provides access to configured language model instances.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from claim_verifier.llm.config import DEFAULT_TEMPERATURE, MODEL_NAME

# Default LLM instance with zero temperature
openai_llm = init_chat_model(model=MODEL_NAME, temperature=DEFAULT_TEMPERATURE)


def get_llm() -> BaseChatModel:
    """Get LLM with appropriate temperature based on completions.

    Returns:
        Configured LLM instance
    """
    # Always use default temperature - claim verifier doesn't need diverse outputs
    return init_chat_model(model=MODEL_NAME, temperature=DEFAULT_TEMPERATURE)
