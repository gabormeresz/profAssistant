from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from typing import Optional

from config import LLMConfig

load_dotenv()


def get_model(api_key: Optional[str] = None, **kwargs):
    """
    Create an LLM model instance.

    Args:
        api_key: Optional OpenAI API key. If None, falls back to the
                 OPENAI_API_KEY environment variable.
        **kwargs: Additional keyword arguments passed to init_chat_model
                  (e.g. temperature, max_tokens).

    Returns:
        A configured chat model instance.
    """
    if api_key:
        kwargs["api_key"] = api_key
    return init_chat_model(f"openai:{LLMConfig.DEFAULT_MODEL}", **kwargs)


def get_structured_output_model(schema, api_key: Optional[str] = None):
    """
    Get model configured for structured output with given schema.

    Args:
        schema: Pydantic model or schema for structured output.
        api_key: Optional OpenAI API key. If None, falls back to the
                 OPENAI_API_KEY environment variable.

    Returns:
        Model configured for structured output.
    """
    return get_model(api_key).with_structured_output(schema)
