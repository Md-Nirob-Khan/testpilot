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
    assert response.estimated_cost_usd == pytest.approx(0.006)


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
    assert response.total_tokens == 11
    assert response.estimated_cost_usd == 0


def test_provider_surfaces_connection_errors() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=URLError("offline")),
        pytest.raises(LLMProviderError, match="request failed"),
    ):
        OllamaProvider().complete("system", "user")


def test_provider_rejects_malformed_response() -> None:
    with (
        patch("urllib.request.urlopen", return_value=_mock_response({"message": {}})),
        pytest.raises(LLMProviderError, match="missing message content"),
    ):
        OllamaProvider().complete("system", "user")


def test_create_provider_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("TESTPILOT_LLM_PROVIDER", "anthropic")

    provider = create_provider()

    assert isinstance(provider, AnthropicProvider)
    assert provider.api_key == "test-key"


def test_create_anthropic_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        create_provider("anthropic")
