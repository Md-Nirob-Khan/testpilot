"""Tests for persisted experiment generation traces."""

import json
from pathlib import Path

import pytest

from testpilot.llm import LLMResponse
from testpilot.run_artifacts import (
    RecordingProvider,
    RunArtifactCapture,
    write_run_artifacts,
)


class FakeProvider:
    """Return queued outputs and record its input prompts."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.requests.append((system_prompt, user_prompt))
        return LLMResponse("def test_answer():\n    assert True\n", 2, 3, 0.0)


class SamplingFakeProvider(FakeProvider):
    """Record per-call sampling settings for artifact-wrapper tests."""

    def __init__(self) -> None:
        super().__init__()
        self.settings: list[tuple[float, int]] = []

    def complete_with_sampling(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        seed: int,
    ) -> LLMResponse:
        self.settings.append((temperature, seed))
        return self.complete(system_prompt, user_prompt)


def test_recording_provider_preserves_prompt_and_raw_output() -> None:
    provider = FakeProvider()
    capture = RunArtifactCapture()
    recording_provider = RecordingProvider(provider, capture)

    response = recording_provider.complete("system", "user prompt")

    assert provider.requests == [("system", "user prompt")]
    assert response.content == capture.completions[0].raw_output
    assert capture.completions[0].system_prompt == "system"
    assert capture.completions[0].user_prompt == "user prompt"


def test_recording_provider_preserves_per_call_sampling_settings() -> None:
    provider = SamplingFakeProvider()
    capture = RunArtifactCapture()
    recording_provider = RecordingProvider(provider, capture)

    recording_provider.complete_with_sampling(
        "system",
        "later-round prompt",
        temperature=0.7,
        seed=44,
    )

    assert provider.settings == [(0.7, 44)]
    assert capture.completions[0].temperature == 0.7
    assert capture.completions[0].seed == 44


def test_agent_artifacts_include_round_prompts_feedback_and_selected_round(
    tmp_path: Path,
) -> None:
    capture = RunArtifactCapture()
    capture.begin_completion(
        "system one",
        "initial user prompt",
        temperature=0.0,
        seed=42,
    )
    capture.record_output(
        0,
        LLMResponse("def test_first():\n    assert True\n", 1, 1, 0.0),
    )
    capture.begin_completion(
        "system two",
        "replacement prompt\n\nEvaluator feedback:\n"
        "Mutation score: 0.2\nSurviving mutants: ('mutant_1',)",
        temperature=0.7,
        seed=44,
    )
    capture.record_output(
        1,
        LLMResponse("def test_returned():\n    assert True\n", 1, 1, 0.0),
    )
    capture.begin_completion(
        "system three",
        "third prompt\n\nEvaluator feedback:\n"
        "Mutation score: 0.4\nSurviving mutants: none",
        temperature=0.7,
        seed=45,
    )
    capture.record_output(
        2,
        LLMResponse("def test_last():\n    assert True\n", 1, 1, 0.0),
    )
    capture.mutation_scores.update({0: 0.2, 1: 0.8, 2: 0.6})

    directory = write_run_artifacts(
        tmp_path,
        "HumanEval/10",
        "agent-llm",
        "def test_returned():\n    assert True",
        capture,
    )

    metadata = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert metadata["rounds_recorded"] == 3
    assert metadata["selected_round"] == 2
    assert [
        (item["temperature"], item["seed"])
        for item in metadata["round_details"]
    ] == [(0.0, 42), (0.7, 44), (0.7, 45)]
    assert [item["returned"] for item in metadata["round_details"]] == [
        False,
        True,
        False,
    ]
    assert (directory / "generated_test.py").read_text(encoding="utf-8") == (
        "def test_returned():\n    assert True"
    )
    assert (directory / "round_02/prompt.txt").read_text(encoding="utf-8") == (
        capture.completions[1].user_prompt
    )
    assert (directory / "round_02/raw_output.txt").read_text(encoding="utf-8") == (
        capture.completions[1].raw_output
    )
    assert (
        directory / "round_02/evaluator_feedback.txt"
    ).read_text(encoding="utf-8") == (
        "Mutation score: 0.2\nSurviving mutants: ('mutant_1',)"
    )
    assert (directory / "round_01/evaluator_feedback.txt").read_text(
        encoding="utf-8"
    ) == ""


def test_single_shot_artifacts_mark_its_only_generation_as_returned(
    tmp_path: Path,
) -> None:
    capture = RunArtifactCapture()
    capture.begin_completion(
        "system",
        "initial prompt",
        temperature=0.0,
        seed=42,
    )
    capture.record_output(
        0,
        LLMResponse("def test_returned():\n    assert True\n", 1, 1, 0.0),
    )

    directory = write_run_artifacts(
        tmp_path,
        "HumanEval/10",
        "single-shot-llm",
        "def test_returned():\n    assert True",
        capture,
    )

    metadata = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert metadata["selected_round"] == 1
    assert [item["returned"] for item in metadata["round_details"]] == [True]


def test_artifact_paths_reject_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid task ID"):
        write_run_artifacts(
            tmp_path,
            "HumanEval/../secret",
            "agent-llm",
            "test suite",
            RunArtifactCapture(),
        )


def test_failed_agent_run_saves_last_successful_round_output(
    tmp_path: Path,
) -> None:
    capture = RunArtifactCapture()
    capture.begin_completion("system", "first prompt")
    capture.record_output(
        0,
        LLMResponse("```python\nassert True\n```\n", 1, 1, 0.0),
    )
    capture.begin_completion("system", "retry prompt")
    capture.record_error(1, TimeoutError("timed out"))

    directory = write_run_artifacts(
        tmp_path,
        "HumanEval/2",
        "agent-llm",
        None,
        capture,
        "TimeoutError: timed out",
    )

    metadata = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert (directory / "generated_test.py").read_text(encoding="utf-8") == (
        "assert True"
    )
    assert metadata["suite_returned"] is False
    assert metadata["selected_round"] is None
    assert metadata["generated_test_source"] == (
        "last_successful_round_output; engine did not return"
    )
