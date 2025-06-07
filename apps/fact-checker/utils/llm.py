"""LLM interaction utilities.

Helper functions for working with language models.
"""

import asyncio
import logging
from typing import Any, Callable, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel

T = TypeVar("T")
R = TypeVar("R")
M = TypeVar("M", bound=BaseModel)

logger = logging.getLogger(__name__)


async def call_llm_with_structured_output(
    llm: BaseChatModel,
    output_class: Type[M],
    messages: List[Tuple[str, str]],
    context_desc: str = "",
) -> Optional[M]:
    """Call LLM with structured output and consistent error handling.

    Args:
        llm: LLM instance
        output_class: Pydantic model for structured output
        messages: Messages to send to the LLM
        context_desc: Description for error logs

    Returns:
        Structured output or None if error
    """
    try:
        return await llm.with_structured_output(output_class).ainvoke(messages)
    except Exception as e:
        logger.error(f"Error in LLM call for {context_desc}: {e}")
        return None


async def process_with_voting(
    items: List[T],
    processor: Callable[[T, Any], Tuple[bool, Optional[R]]],
    llm: Any,
    completions: int,
    min_successes: int,
    result_factory: Callable[[R, T], Any],
    description: str = "item",
) -> List[Any]:
    """Process items with multiple LLM attempts and consensus voting.

    Args:
        items: Items to process
        processor: Function that processes each item
        llm: LLM instance
        completions: How many attempts per item
        min_successes: How many must succeed
        result_factory: Function to create final result
        description: Item type for logs

    Returns:
        List of successfully processed results
    """
    results = []

    for item in items:
        # Make multiple attempts
        attempts = await asyncio.gather(
            *[processor(item, llm) for _ in range(completions)]
        )

        # Count successes
        success_count = sum(1 for success, _ in attempts if success)

        # Only proceed if we have enough successes
        if success_count < min_successes:
            logger.info(
                f"Not enough successes ({success_count}/{min_successes}) for {description}"
            )
            continue

        # Use the first successful result
        for success, result in attempts:
            if success and result is not None:
                processed_result = result_factory(result, item)
                if processed_result:
                    results.append(processed_result)
                    break

    return results
