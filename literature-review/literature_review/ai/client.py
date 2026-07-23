"""Unified AI client — wraps litellm for all model interactions.

Absorbed from:
- ReviewAgent ai_chat_response.py (chat interface)
- AeroWdgLiteratureReview ai_model.py (model registry)
- ReviewAgent config.py (model builder)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelSpec:
    """Descriptor for an AI model usable via litellm."""
    provider: str                     # e.g. "ollama", "gemini", "openai"
    model_name: str                   # e.g. "gpt-oss:20b", "gemini-2.5-flash"
    temperature: float = 0.1
    context_length: int = 64000
    think: str | None = None          # "low" | "medium" | "high" — model-dependent
    extra_options: dict[str, Any] = field(default_factory=dict)

    def to_litellm_model(self) -> str:
        """Return litellm-compatible model string like 'ollama/gpt-oss:20b'."""
        if "/" in self.model_name:
            return self.model_name
        return f"{self.provider}/{self.model_name}"

    def to_dict(self) -> dict:
        """Return the dict format used by legacy ReviewAgent chat_response."""
        result: dict[str, Any] = {
            "provider": self.provider,
            "model_name": self.model_name,
            "options": {"temperature": self.temperature, **self.extra_options},
            "context_length": self.context_length,
        }
        if self.think is not None:
            result["think"] = self.think
        return result


# ---------------------------------------------------------------------------
# Built-in model registry
# ---------------------------------------------------------------------------

MODELS: dict[str, ModelSpec] = {
    # Ollama (local)
    "gpt-oss:20b": ModelSpec(provider="ollama", model_name="gpt-oss:20b", think="medium"),
    "gemma3:27b": ModelSpec(provider="ollama", model_name="gemma3:27b", think="medium"),
    # Gemini
    "gemini-2.5-flash-lite": ModelSpec(provider="gemini", model_name="gemini-2.5-flash-lite",
                                        context_length=128000, think="medium"),
    "gemini-2.5-flash": ModelSpec(provider="gemini", model_name="gemini-2.5-flash",
                                   context_length=128000, think="medium"),
    "gemini-2.5-pro": ModelSpec(provider="gemini", model_name="gemini-2.5-pro",
                                 context_length=128000, think="medium"),
}


def get_model(key: str) -> ModelSpec:
    """Look up a model by registry key."""
    if key in MODELS:
        return MODELS[key]
    raise KeyError(f"Unknown model: {key}. Available: {list(MODELS)}")


# ---------------------------------------------------------------------------
# Chat interface (from ReviewAgent ai_chat_response.py)
# ---------------------------------------------------------------------------

def chat(model: ModelSpec | str, messages: list[dict[str, str]]) -> str | None:
    """Send messages to an LLM via litellm and return assistant text.

    Args:
        model: ModelSpec or registry key string.
        messages: List of {"role": "...", "content": "..."} dicts.

    Returns:
        Assistant response text, or None on failure.
    """
    from litellm import completion

    if isinstance(model, str):
        model = get_model(model)

    model_str = model.to_litellm_model()
    options = {"temperature": model.temperature, **model.extra_options}

    try:
        response = completion(model=model_str, messages=messages, stream=False, **options)
        content = response["choices"][0]["message"]["content"]
        return str(content).strip() if content else None
    except Exception:
        return None


def chat_structured(
    model: ModelSpec | str,
    system: str,
    prompt: str,
) -> str | None:
    """Convenience wrapper: system + user message → chat."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    return chat(model, messages)
