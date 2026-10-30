"""Tests for LLM provider clients."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from testpilot.llm import (
    AnthropicProvider,
    LLMProviderError,
    OllamaProvider,
    create_provider,
)


def _mock_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return response


def test_anthropic_provider_sends_request_and_calculates_cost() -> None:
    payload = {
        "content": [{"type": "text", "text": "assert True\n"}],
        "usage": {"input_tokens": 1000, "output_tokens": 200},
    }
    with patch("urllib.request.urlopen", return_value=_mock_response(payload)) as urlopen:
        response = AnthropicProvider("secret").complete("system", "user")

    request = urlopen.call_args.args[0]
    request_data = json.loads(request.data)
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.get_header("X-api-key") == "secret"
    assert request_data["messages"] == [{"role": "user", "content": "user"}]
    assert response.content == "assert True\n"
    assert response.total_tokens == 1200
    assert response.estimated_cost_usd == pytest.approx(0.0002)


@pytest.mark.parametrize(
    ("input_tokens", "expected_cost"),
    [
        (100_000, 0.0105),
        (100_001, 0.0525005),
    ],
)
def test_anthropic_provider_uses_prompt_size_pricing_tier(
    input_tokens: int,
    expected_cost: float,
) -> None:
    payload = {
        "content": [{"type": "text", "text": "generated"}],
        "usage": {"input_tokens": input_tokens, "output_tokens": 1000},
    }
    with patch("urllib.request.urlopen", return_value=_mock_response(payload)):
        response = AnthropicProvider("secret").complete("system", "user")

    assert response.estimated_cost_usd == pytest.approx(expected_cost)


def test_anthropic_provider_defaults_to_requested_model() -> None:
    provider = AnthropicProvider("secret")

    assert provider.model == "claude-haiku-5-5"


def test_ollama_provider_reports_zero_cost_and_usage() -> None:
    payload = {
        "message": {"content": "assert True\n"},
        "prompt_eval_count": 8,
        "eval_count": 3,
    }
    with patch("urllib.request.urlopen", return_value=_mock_response(payload)) as urlopen:
        response = OllamaProvider(model="tiny", base_url="http://localhost:11434/").complete(
            "system",
            "user",
        )

    request = urlopen.call_args.args[0]
    request_data = json.loads(request.data)
    assert request.full_url == "http://localhost:11434/api/chat"
    assert request_data["stream"] is False
    assert request_data["options"] == {"temperature": 0.0, "seed": 42}
    assert response.total_tokens == 11
    assert response.estimated_cost_usd == 0


def test_ollama_provider_sends_configured_sampling_settings() -> None:
    payload = {"message": {"content": "generated"}}
    with patch("urllib.request.urlopen", return_value=_mock_response(payload)) as urlopen:
        OllamaProvider(temperature=0.25, seed=7).complete("system", "user")

    request_data = json.loads(urlopen.call_args.args[0].data)
    assert request_data["options"] == {"temperature": 0.25, "seed": 7}


@pytest.mark.parametrize(
    ("temperature", "seed"),
    [(-0.1, 42), (float("inf"), 42), (0.0, True)],
)
def test_ollama_provider_rejects_invalid_sampling_settings(
    temperature: float,
    seed: int,
) -> None:
    with pytest.raises(ValueError):
        OllamaProvider(temperature=temperature, seed=seed)


def test_provider_surfaces_connection_errors() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=URLError("offline")),
        pytest.raises(LLMProviderError, match="request failed"),
    ):
        OllamaProvider().complete("system", "user")


def test_ollama_retries_connection_refusal_once() -> None:
    payload = {"message": {"content": "generated"}, "prompt_eval_count": 1}
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            URLError(ConnectionRefusedError(61, "Connection refused")),
            _mock_response(payload),
        ],
    ) as urlopen:
        response = OllamaProvider().complete("system", "user")

    assert response.content == "generated"
    assert urlopen.call_count == 2


def test_ollama_does_not_retry_other_provider_errors() -> None:
    with (
        patch(
            "urllib.request.urlopen",
            side_effect=URLError("offline"),
        ) as urlopen,
        pytest.raises(LLMProviderError, match="request failed"),
    ):
        OllamaProvider().complete("system", "user")

    assert urlopen.call_count == 1


def test_ollama_stops_after_one_refused_connection_retry() -> None:
    with (
        patch(
            "urllib.request.urlopen",
            side_effect=URLError(
                ConnectionRefusedError(61, "Connection refused")
            ),
        ) as urlopen,
        pytest.raises(LLMProviderError, match="Connection refused"),
    ):
        OllamaProvider().complete("system", "user")

    assert urlopen.call_count == 2


def test_provider_rejects_malformed_response() -> None:
    with (
        patch("urllib.request.urlopen", return_value=_mock_response({"message": {}})),
        pytest.raises(LLMProviderError, match="missing message content"),
    ):
        OllamaProvider().complete("system", "user")


def test_create_provider_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("TESTPILOT_LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_INPUT_COST_PER_MILLION", raising=False)
    monkeypatch.delenv("ANTHROPIC_OUTPUT_COST_PER_MILLION", raising=False)
    monkeypatch.delenv("ANTHROPIC_INPUT_COST_OVER_100K_PER_MILLION", raising=False)
    monkeypatch.delenv("ANTHROPIC_OUTPUT_COST_OVER_100K_PER_MILLION", raising=False)

    provider = create_provider()

    assert isinstance(provider, AnthropicProvider)
    assert provider.api_key == "test-key"
    assert provider.model == "claude-haiku-5-5"
    assert provider.input_cost_per_million == 0.10
    assert provider.output_cost_per_million == 0.50
    assert provider.input_cost_over_100k_per_million == 0.50
    assert provider.output_cost_over_100k_per_million == 2.50


def test_create_anthropic_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        create_provider("anthropic")
