"""
Reusable tenacity-based retry wrapper for structured output LLM calls.

Groq models sometimes fail to comply with tool_choice="required" and return
plain text instead of a tool call, causing a BadRequestError. This utility
retries those transient failures with exponential backoff + jitter.
"""
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


def retry_structured_output(max_attempts: int = 5):
    """
    Decorator for async functions that call .with_structured_output().ainvoke().
    Retries on Groq BadRequestError (tool_use_failed) with exponential backoff + jitter.

    Usage:
        @retry_structured_output(max_attempts=3)
        async def extract_data(...):
            return await llm.with_structured_output(Schema).ainvoke(messages)
    """
    # Import here to avoid hard dependency at module level
    try:
        from groq import BadRequestError as GroqBadRequestError
    except ImportError:
        GroqBadRequestError = Exception

    return retry(
        retry=retry_if_exception_type((GroqBadRequestError,)),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=2),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
