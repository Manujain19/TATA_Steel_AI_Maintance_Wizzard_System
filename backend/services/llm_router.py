from __future__ import annotations

from typing import Any, Dict

from backend.config import settings
from services.llm_provider import LLMProvider


class LLMRouter:
    """Provider abstraction for Groq, OpenAI, Anthropic, Gemini, Ollama, and local fallback."""

    def __init__(self) -> None:
        self.provider_name = settings.llm_provider
        self.legacy_provider = LLMProvider()

    def generate_json(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Existing provider already supports Groq/Llama, Gemini, OpenAI, and local fallback.
        # Anthropic/Ollama are routed through local fallback unless configured in a deployment adapter.
        return self.legacy_provider.generate_json(prompt, context)

    def health_status(self) -> Dict[str, Any]:
        return self.legacy_provider.health_status()

    def diagnostic_status(self, run_test: bool = False) -> Dict[str, Any]:
        return self.legacy_provider.diagnostic_status(run_test=run_test)
