from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterator, List

logger = logging.getLogger(__name__)


class LLMProvider:
    """Pluggable decision-engine adapter with Llama Versatile and local fallback."""

    def __init__(self) -> None:
        load_env_file()
        self.llama_api_key = (
            os.getenv("GROQ_API_KEY", "").strip()
            or os.getenv("LLAMA_API_KEY", "").strip()
        )
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.preferred_provider = (
            os.getenv("LLM_PROVIDER", "").strip().lower()
            or os.getenv("STEELMIND_PROVIDER", "").strip().lower()
        )
        self.provider = self._select_provider()
        self.llama_model = os.getenv("LLAMA_MODEL", "llama-3.3-70b-versatile")
        self.gemini_model = os.getenv("GEMINI_MODEL", "").strip()
        self.llama_base_url = normalize_openai_base_url(
            os.getenv("LLAMA_BASE_URL", "https://api.groq.com/openai/v1")
        )
        self.last_status: Dict[str, Any] = {
            "provider": self.provider,
            "model": self.llama_model,
            "base_url": self.llama_base_url,
            "api_key_loaded": bool(self.llama_api_key or self.gemini_api_key or self.openai_api_key),
            "status": "not_called",
            "latency_ms": None,
            "token_count": None,
        }

    def _select_provider(self) -> str:
        if self.preferred_provider in {"groq", "llama", "llama_versatile"}:
            return "llama_versatile" if self.llama_api_key else "local_fallback"
        if self.llama_api_key:
            return "llama_versatile"
        if self.preferred_provider == "gemini":
            return "gemini" if self.gemini_api_key else "local_fallback"
        if self.preferred_provider == "openai":
            return "openai" if self.openai_api_key else "local_fallback"
        if self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        return "local_fallback"

    def generate_json(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("LLM generation requested provider=%s", self.provider)
        context = self._compress_context(context)
        if self.provider == "llama_versatile":
            return self._call_llama_versatile(prompt, context)
        if self.provider == "gemini":
            return self._call_gemini(prompt, context)
        if self.provider == "openai":
            return self._call_openai(prompt, context)
        return self._local_reasoning(context)

    def _call_llama_versatile(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        url = self._chat_completions_url()
        context_text = json.dumps(context, separators=(",", ":"))
        body = {
            "model": self.llama_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return strict JSON for an industrial maintenance diagnosis.",
                },
                {
                    "role": "user",
                    "content": prompt + "\n\nContext:\n" + context_text,
                },
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        estimated_prompt_tokens = estimate_tokens(prompt) + estimate_tokens(context_text) + 32
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llama_api_key}",
                "User-Agent": "Maintenance-Wizard-Tata-Steel-AI/1.0",
            },
            method="POST",
        )
        started = time.perf_counter()
        last_error = None
        try:
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(request, timeout=20) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                    break
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                    last_error = exc
                    if attempt == 1:
                        raise
                    time.sleep(0.35)
            content = payload["choices"][0]["message"]["content"]
            usage = payload.get("usage", {})
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            self.last_status = {
                "provider": "groq",
                "model": body["model"],
                "base_url": self.llama_base_url,
                "api_key_loaded": bool(self.llama_api_key),
                "status": "completed",
                "latency_ms": latency_ms,
                "prompt_tokens": usage.get("prompt_tokens", estimated_prompt_tokens),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens", usage.get("prompt_tokens", estimated_prompt_tokens)),
                "token_count": usage.get("total_tokens", usage.get("prompt_tokens", estimated_prompt_tokens)),
            }
            logger.info(
                "Groq Llama response generated request_time_ms=%s token_count=%s completion_status=completed",
                latency_ms,
                usage.get("total_tokens"),
            )
            parsed = self._parse_or_fallback(content, context, "llama_versatile")
            parsed["llm_status"] = self.last_status
            return parsed
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            error_detail = self._format_http_error(last_error or exc)
            self.last_status = {
                "provider": "groq",
                "model": body["model"],
                "base_url": self.llama_base_url,
                "api_key_loaded": bool(self.llama_api_key),
                "status": "fallback",
                "latency_ms": latency_ms,
                "prompt_tokens": estimated_prompt_tokens,
                "completion_tokens": None,
                "total_tokens": estimated_prompt_tokens,
                "token_count": estimated_prompt_tokens,
                "error": error_detail,
            }
            logger.warning("Groq API unavailable, using deterministic fallback: %s", error_detail)
            if self.gemini_api_key:
                logger.info("Switching provider from Groq to Gemini reason=%s", error_detail)
                gemini_result = self._call_gemini(prompt, context)
                gemini_result["provider_switch_reason"] = error_detail
                gemini_result["fallback_provider"] = "gemini"
                return gemini_result
            return self._local_reasoning(context, degraded_provider="llama_versatile_error")

    def _call_gemini(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                prompt
                                + "\n\nReturn strict JSON only.\n\nContext:\n"
                                + json.dumps(context, separators=(",", ":"))
                            )
                        }
                    ]
                }
            ]
        }
        last_error = None
        for model in self._gemini_model_candidates(validate=True):
            url = self._gemini_generate_url(model)
            result = self._post_json(url, body, provider="gemini", context=context, model=model)
            if result.get("llm_provider") == "gemini" and self.last_status.get("status") == "completed":
                return result
            last_error = self.last_status.get("error")
        fallback = self._local_reasoning(context, degraded_provider="gemini_error")
        fallback["fallback_reason"] = last_error or "No Gemini model produced a valid response."
        return fallback

    def _call_openai(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        body = {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "Return strict JSON for an industrial maintenance diagnosis.",
                },
                {
                    "role": "user",
                    "content": prompt + "\n\nContext:\n" + json.dumps(context, indent=2),
                },
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            return self._parse_or_fallback(content, context, "openai")
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
            return self._local_reasoning(context, degraded_provider="openai_error")

    def _post_json(
        self,
        url: str,
        body: Dict[str, Any],
        provider: str,
        context: Dict[str, Any] | None = None,
        model: str | None = None,
    ) -> Dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["candidates"][0]["content"]["parts"][0]["text"]
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            self.last_status = {
                **self.last_status,
                "provider": provider,
                "model": model or self.last_status.get("model"),
                "status": "completed",
                "latency_ms": latency_ms,
                "error": None,
            }
            parsed = self._parse_or_fallback(content, context or body, provider)
            parsed["llm_status"] = self.last_status
            return parsed
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            self.last_status = {
                **self.last_status,
                "provider": provider,
                "model": model or self.last_status.get("model"),
                "status": "fallback",
                "latency_ms": latency_ms,
                "error": self._format_http_error(exc),
            }
            return self._local_reasoning(context or body, degraded_provider=f"{provider}_error")

    def _parse_or_fallback(self, content: str, context: Dict[str, Any], provider: str) -> Dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        try:
            parsed = json.loads(cleaned)
            parsed["llm_provider"] = provider
            return parsed
        except json.JSONDecodeError:
            fallback = self._local_reasoning(context, degraded_provider=f"{provider}_parse_error")
            fallback["raw_llm_text"] = content[:1200]
            return fallback

    def _local_reasoning(
        self, context: Dict[str, Any], degraded_provider: str = "local_fallback"
    ) -> Dict[str, Any]:
        self.last_status = {
            **self.last_status,
            "provider": degraded_provider,
            "status": "fallback" if degraded_provider != "local_fallback" else "completed",
            "api_key_loaded": bool(self.llama_api_key or self.gemini_api_key or self.openai_api_key),
            "prompt_tokens": self.last_status.get("prompt_tokens"),
            "completion_tokens": self.last_status.get("completion_tokens"),
            "total_tokens": self.last_status.get("total_tokens"),
        }
        report = context.get("base_report", context)
        equipment = report.get("equipment", {})
        diagnosis = report.get("diagnosis", {})
        risk = report.get("risk", {})
        if "fault" in diagnosis and "probable_fault" not in diagnosis:
            diagnosis = {
                "probable_fault": diagnosis.get("fault"),
                "probable_root_causes": diagnosis.get("root_causes", []),
                "condition_breaches": diagnosis.get("condition_breaches", []),
            }
        recommendations = report.get("recommendations", [])
        breaches = diagnosis.get("condition_breaches", [])
        causes = diagnosis.get("probable_root_causes", [])
        first_action = recommendations[0] if recommendations else "Escalate to maintenance review and collect more evidence."
        equipment_name = equipment.get("equipment_name") or equipment.get("name") or equipment.get("id") or "Selected asset"

        summary = (
            f"{equipment_name} shows "
            f"{risk.get('level', 'unknown')} maintenance risk from "
            f"{diagnosis.get('probable_fault', 'the active alert')}. "
            f"Detected {len(breaches)} condition breach(es). "
            f"Likely root cause candidates: {', '.join(causes) if causes else 'not enough evidence'}. "
            f"Recommended first action: {first_action}"
        )
        return {
            "llm_provider": degraded_provider,
            "fault_diagnosis": diagnosis.get("probable_fault", "Unknown fault"),
            "root_cause_candidates": causes,
            "risk_explanation": (
                f"Risk is {risk.get('level')} with score {risk.get('score')} because condition, "
                "history severity, and spare constraints all contribute to intervention urgency."
            ),
            "maintenance_recommendations": recommendations,
            "executive_summary": summary,
            "llm_confidence_estimate": 0.82,
            "llm_status": self.last_status,
        }

    def _compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        report = context.get("report") or context.get("base_report") or context
        equipment = report.get("equipment", {})
        diagnosis = report.get("diagnosis", {})
        risk = report.get("risk", {})
        prediction = report.get("prediction", {})
        recommendations = report.get("recommendations", [])
        retrieval = context.get("retrieval", {})
        documents = retrieval.get("documents", []) if isinstance(retrieval, dict) else []
        evidence = []
        for item in documents[:3]:
            metadata = item.get("metadata", {})
            text = str(item.get("text", "")).replace("\n", " ").strip()
            evidence.append(
                {
                    "source": metadata.get("source"),
                    "id": metadata.get("parent_id") or item.get("id"),
                    "score": item.get("score") or item.get("hybrid_score"),
                    "snippet": text[:500],
                }
            )
        return {
            "query": str(context.get("query", ""))[:500],
            "equipment": {
                "id": equipment.get("equipment_id"),
                "name": equipment.get("equipment_name"),
                "alert": equipment.get("active_alert"),
                "criticality": equipment.get("criticality"),
            },
            "diagnosis": {
                "fault": diagnosis.get("probable_fault"),
                "root_causes": (diagnosis.get("probable_root_causes") or [])[:3],
                "condition_breaches": (diagnosis.get("condition_breaches") or [])[:5],
            },
            "risk": {
                "level": risk.get("level"),
                "score": risk.get("score"),
                "drivers": risk.get("drivers"),
            },
            "prediction": {
                "rul_hours": prediction.get("estimated_remaining_useful_life_hours"),
                "health_index": prediction.get("health_index"),
            },
            "recommendations": recommendations[:5],
            "evidence": evidence,
        }

    def health_status(self) -> Dict[str, Any]:
        return {
            **self.last_status,
            "groq_api_key_loaded": bool(self.llama_api_key),
            "configured_model": self.llama_model,
            "base_url": self.llama_base_url,
            "healthy": self.last_status.get("status") in {"completed", "fallback"},
            "streaming_supported": self.provider == "llama_versatile",
        }

    def stream_tokens(self, prompt: str, context: Dict[str, Any]) -> Iterator[str]:
        """Streaming facade. Groq streaming can be enabled here; fallback streams local text chunks."""
        output = self.generate_json(prompt, context)
        text = output.get("executive_summary") or output.get("risk_explanation") or "Recommendation generated."
        for token in text.split():
            yield token + " "

    def diagnostic_status(self, run_test: bool = False) -> Dict[str, Any]:
        status = {
            "provider": "groq" if self.provider == "llama_versatile" else self.provider,
            "model": self.llama_model,
            "base_url": self.llama_base_url,
            "api_key_loaded": bool(self.llama_api_key),
            "connection_status": "not_tested",
            "error": None,
            "last_status": self.health_status(),
        }
        if run_test and self.provider == "llama_versatile" and self.llama_api_key:
            result = self._call_llama_versatile(
                "Return JSON: {\"executive_summary\":\"ok\",\"llm_confidence_estimate\":0.9}",
                {"equipment": {"equipment_name": "health check"}, "diagnosis": {}, "risk": {}, "recommendations": []},
            )
            status["connection_status"] = "healthy" if result.get("llm_provider") == "llama_versatile" else "fallback"
            status["error"] = self.last_status.get("error")
            status["last_status"] = self.health_status()
        elif run_test:
            status["connection_status"] = "missing_api_key" if not self.llama_api_key else "provider_not_groq"
        return status

    def groq_test(self) -> Dict[str, Any]:
        started = time.perf_counter()
        status = self.diagnostic_status(run_test=True)
        last = status.get("last_status", {})
        return {
            "success": status.get("connection_status") == "healthy",
            "latency_ms": last.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2),
            "model": status.get("model"),
            "provider": "groq",
            "status": status.get("connection_status"),
            "error": status.get("error") or last.get("error"),
            "base_url": status.get("base_url"),
            "api_key_loaded": status.get("api_key_loaded"),
        }

    def gemini_test(self) -> Dict[str, Any]:
        started = time.perf_counter()
        if not self.gemini_api_key:
            return {
                "status": "missing_api_key",
                "model": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "api_key_loaded": False,
            }
        for model in self._gemini_model_candidates(validate=True):
            body = {"contents": [{"parts": [{"text": "Return JSON only: {\"executive_summary\":\"ok\"}"}]}]}
            result = self._post_json(self._gemini_generate_url(model), body, "gemini", context={}, model=model)
            if result.get("llm_provider") == "gemini" and self.last_status.get("status") == "completed":
                return {
                    "status": "healthy",
                    "model": model,
                    "latency_ms": self.last_status.get("latency_ms"),
                    "api_key_loaded": True,
                }
        return {
            "status": "fallback",
            "model": self.last_status.get("model"),
            "latency_ms": self.last_status.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2),
            "api_key_loaded": True,
            "error": self.last_status.get("error"),
        }

    def _gemini_model_candidates(self, validate: bool = False) -> List[str]:
        preferred = [self.gemini_model, "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"]
        ordered = []
        for model in preferred:
            if model and model not in ordered:
                ordered.append(model)
        if not validate or not self.gemini_api_key:
            return ordered
        available = self._available_gemini_models()
        if not available:
            return ordered
        filtered = [model for model in ordered if model in available or f"models/{model}" in available]
        return filtered or ordered

    def _available_gemini_models(self) -> set[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.gemini_api_key}"
        request = urllib.request.Request(url, headers={"Content-Type": "application/json"}, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {str(item.get("name", "")).replace("models/", "") for item in payload.get("models", [])}
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            logger.warning("Gemini model discovery unavailable: %s", self._format_http_error(exc))
            return set()

    def _gemini_generate_url(self, model: str) -> str:
        clean_model = str(model or "gemini-2.5-flash").replace("models/", "")
        return f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.gemini_api_key}"

    def _chat_completions_url(self) -> str:
        if self.llama_base_url.endswith("/chat/completions"):
            return self.llama_base_url
        return f"{self.llama_base_url}/chat/completions"

    def _format_http_error(self, exc: Exception) -> str:
        if isinstance(exc, urllib.error.HTTPError):
            try:
                body = exc.read().decode("utf-8", errors="replace")[:1200]
            except Exception:
                body = ""
            return f"HTTP {exc.code} {exc.reason}: {body}".strip()
        return str(exc)


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
            continue
        key, value = cleaned.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def normalize_openai_base_url(value: str) -> str:
    cleaned = str(value or "https://api.groq.com/openai/v1").strip().rstrip("/")
    suffix = "/chat/completions"
    if cleaned.endswith(suffix):
        cleaned = cleaned[: -len(suffix)]
    return cleaned


def estimate_tokens(text: str) -> int:
    return max(1, int(len(str(text)) / 4))
