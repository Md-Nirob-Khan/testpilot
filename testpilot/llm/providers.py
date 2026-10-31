"""Anthropic and Ollama clients with a shared, small provider interface."""

import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol, cast

from dotenv import load_dotenv


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot return a valid completion."""


OLLAMA_TEMPERATURE = 0.0
OLLAMA_SEED = 42


@dataclass(frozen=True)
class LLMResponse:
    """Hold generated text and provider usage information."""

    content: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float

    @property
    def total_tokens(self) -> int:
        """Return the number of input and output tokens."""
        return self.input_tokens + self.output_tokens


class LLMProvider(Protocol):
    """Common interface implemented by configured language model providers."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Request one completion from the provider."""


@dataclass(frozen=True)
class AnthropicProvider:
    """Call the Anthropic Messages API."""

    api_key: str
    model: str = "claude-haiku-5-5"
    timeout_seconds: float = 120.0
    input_cost_per_million: float = 0.10
    output_cost_per_million: float = 0.50
    input_cost_over_100k_per_million: float = 0.50
    output_cost_over_100k_per_million: float = 2.50

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("Anthropic API key cannot be empty")
        _validate_timeout(self.timeout_seconds)
        _validate_rate(self.input_cost_per_million, "input")
        _validate_rate(self.output_cost_per_million, "output")
        _validate_rate(self.input_cost_over_100k_per_million, "over-100K input")
        _validate_rate(self.output_cost_over_100k_per_million, "over-100K output")

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Request one non-streaming message and estimate its API cost."""
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(
                {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                }
            ).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        payload = _post_json(request, self.timeout_seconds, "Anthropic")
        content_items = payload.get("content")
        usage = payload.get("usage")
        if not isinstance(content_items, list) or not isinstance(usage, dict):
            raise LLMProviderError("Anthropic response is missing content or usage")

        text = "".join(
            item["text"]
            for item in content_items
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        )
        if not text:
            raise LLMProviderError("Anthropic response contained no text")

        input_tokens = _token_count(usage, "input_tokens", "Anthropic")
        output_tokens = _token_count(usage, "output_tokens", "Anthropic")
        if input_tokens > 100_000:
            input_rate = self.input_cost_over_100k_per_million
            output_rate = self.output_cost_over_100k_per_million
        else:
            input_rate = self.input_cost_per_million
            output_rate = self.output_cost_per_million
        cost = (
            input_tokens * input_rate
            + output_tokens * output_rate
        ) / 1_000_000
        return LLMResponse(text, input_tokens, output_tokens, cost)


@dataclass(frozen=True)
class OllamaProvider:
    """Call a local Ollama chat endpoint."""

    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    timeout_seconds: float = 120.0
    temperature: float = OLLAMA_TEMPERATURE
    seed: int = OLLAMA_SEED

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("Ollama model cannot be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Ollama base URL must use http:// or https://")
        _validate_timeout(self.timeout_seconds)
        if not math.isfinite(self.temperature) or self.temperature < 0:
            raise ValueError("Ollama temperature must be finite and non-negative")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("Ollama seed must be an integer")

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Request one non-streaming chat completion from Ollama."""
        return self.complete_with_sampling(
            system_prompt,
            user_prompt,
            temperature=self.temperature,
            seed=self.seed,
        )

    def complete_with_sampling(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        seed: int,
    ) -> LLMResponse:
        """Request one chat completion using per-call reproducible settings."""
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("Ollama temperature must be finite and non-negative")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("Ollama seed must be an integer")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/chat",
            data=json.dumps(
                {
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "options": {
                        "temperature": temperature,
                        "seed": seed,
                    },
                }
            ).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            payload = _post_json(request, self.timeout_seconds, "Ollama")
        except LLMProviderError as exc:
            if not _is_connection_refused(exc):
                raise
            payload = _post_json(request, self.timeout_seconds, "Ollama")
        message = payload.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise LLMProviderError("Ollama response is missing message content")
        input_tokens = _optional_token_count(payload, "prompt_eval_count", "Ollama")
        output_tokens = _optional_token_count(payload, "eval_count", "Ollama")
        return LLMResponse(message["content"], input_tokens, output_tokens, 0.0)


def create_provider(provider_name: str | None = None) -> LLMProvider:
    """Create a provider using `.env` and environment configuration."""
    load_dotenv()
    name = (provider_name or os.getenv("TESTPILOT_LLM_PROVIDER", "ollama")).lower()
    if name == "ollama":
        return OllamaProvider(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    if name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when using the Anthropic provider"
            )
        return AnthropicProvider(
            api_key=api_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"),
            input_cost_per_million=_environment_rate(
                "ANTHROPIC_INPUT_COST_PER_MILLION", 0.10
            ),
            output_cost_per_million=_environment_rate(
                "ANTHROPIC_OUTPUT_COST_PER_MILLION", 0.50
            ),
            input_cost_over_100k_per_million=_environment_rate(
                "ANTHROPIC_INPUT_COST_OVER_100K_PER_MILLION", 0.50
            ),
            output_cost_over_100k_per_million=_environment_rate(
                "ANTHROPIC_OUTPUT_COST_OVER_100K_PER_MILLION", 2.50
            ),
        )
    raise ValueError(f"Unsupported LLM provider: {name!r}")


def _post_json(
    request: urllib.request.Request,
    timeout_seconds: float,
    provider_name: str,
) -> dict[str, object]:
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise LLMProviderError(
            f"{provider_name} returned HTTP {exc.code}: {response_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise LLMProviderError(f"{provider_name} request failed: {exc.reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LLMProviderError(f"{provider_name} returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise LLMProviderError(f"{provider_name} response must be a JSON object")
    return cast(dict[str, object], payload)


def _token_count(
    usage: dict[str, object],
    key: str,
    provider_name: str,
) -> int:
    value = usage.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LLMProviderError(f"{provider_name} response has invalid {key}")
    return value


def _optional_token_count(
    payload: dict[str, object],
    key: str,
    provider_name: str,
) -> int:
    if key not in payload:
        return 0
    return _token_count(payload, key, provider_name)


def _validate_timeout(timeout_seconds: float) -> None:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Timeout must be a finite positive number")


def _validate_rate(rate: float, name: str) -> None:
    if not math.isfinite(rate) or rate < 0:
        raise ValueError(f"Anthropic {name} token rate must be finite and non-negative")


def _environment_rate(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _is_connection_refused(error: LLMProviderError) -> bool:
    """Identify a refused Ollama socket connection eligible for one retry."""
    return "connection refused" in str(error).lower()
