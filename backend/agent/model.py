from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from typing import Literal, Optional

from config import LLMConfig

load_dotenv()

# ── public type alias ────────────────────────────────────────────────
ModelPurpose = Literal["enhancer", "generator", "evaluator"]


# ── internal helpers ─────────────────────────────────────────────────
def _get_preset_kwargs(purpose: ModelPurpose) -> dict:
    """Return a copy of the preset kwargs for *purpose*."""
    preset = LLMConfig.MODEL_PRESETS.get(purpose)
    if preset is None:
        raise ValueError(
            f"Unknown model purpose {purpose!r}. "
            f"Choose from: {', '.join(LLMConfig.MODEL_PRESETS)}"
        )
    return dict(preset)


def _filter_kwargs_for_model(model_id: str, kwargs: dict) -> dict:
    """
    Strip parameters that are incompatible with the resolved model.

    - Reasoning models (gpt-5*): ``temperature`` and ``max_tokens`` are
      removed (temperature is fixed at 1; max_tokens would starve the
      visible output because reasoning tokens count against it).
    - Non-reasoning models: ``reasoning_effort`` is removed (the API
      rejects unrecognised arguments).
    """
    filtered = dict(kwargs)
    if model_id in LLMConfig.REASONING_MODELS:
        filtered.pop("temperature", None)
        filtered.pop("max_tokens", None)
    else:
        filtered.pop("reasoning_effort", None)
    return filtered


# ── public factory functions ─────────────────────────────────────────
def get_model(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    *,
    purpose: ModelPurpose = "generator",
):
    """
    Create an LLM model instance with purpose-based presets.

    Loads tuning parameters (temperature, max_tokens, reasoning_effort)
    from ``LLMConfig.MODEL_PRESETS[purpose]`` and automatically strips
    any that are incompatible with the resolved model.

    Args:
        api_key: Optional OpenAI API key. If None, falls back to the
                 OPENAI_API_KEY environment variable.
        model_name: Optional OpenAI model identifier (e.g. "gpt-4o-mini").
                    Falls back to ``LLMConfig.DEFAULT_MODEL`` when not given.
        purpose: The intended usage — ``"enhancer"``, ``"generator"``,
                 or ``"evaluator"``.  Determines temperature,
                 max_tokens, and reasoning_effort.

    Returns:
        A configured chat model instance.
    """
    kwargs = _get_preset_kwargs(purpose)
    if api_key:
        kwargs["api_key"] = api_key
    model_id = model_name or LLMConfig.DEFAULT_MODEL
    kwargs = _filter_kwargs_for_model(model_id, kwargs)
    return init_chat_model(f"openai:{model_id}", **kwargs)


def get_structured_output_model(
    schema,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    *,
    purpose: ModelPurpose = "generator",
):
    """
    Get model configured for structured output with given schema.

    Args:
        schema: Pydantic model or schema for structured output.
        api_key: Optional OpenAI API key. If None, falls back to the
                 OPENAI_API_KEY environment variable.
        model_name: Optional OpenAI model identifier.
        purpose: The intended usage (see :func:`get_model`).

    Returns:
        Model configured for structured output.
    """
    return get_model(
        api_key, model_name=model_name, purpose=purpose
    ).with_structured_output(schema)
