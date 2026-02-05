from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from config import LLMConfig

load_dotenv()

# Setup LLM using init_chat_model with config
model = init_chat_model(f"openai:{LLMConfig.DEFAULT_MODEL}")


def get_structured_output_model(schema):
    """
    Get model configured for structured output with given schema.

    Args:
        schema: Pydantic model or schema for structured output.

    Returns:
        Model configured for structured output.
    """
    return model.with_structured_output(schema)
