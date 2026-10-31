"""Capture generation inputs, outputs, and selected suites for experiment runs."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from testpilot.evaluator.mutation import MutationResult
from testpilot.llm import LLMProvider, LLMResponse


class _MutationEvaluator(Protocol):
    """Describe the mutation evaluator interface used by the agent engine."""

    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        deselected_test_ids: tuple[str, ...] = (),
    ) -> MutationResult:
        """Evaluate mutation score for one generated suite."""


@dataclass
class CompletionArtifact:
    """Record one provider request, response, or generation error."""

    system_prompt: str
    user_prompt: str
    raw_output: str = ""
    error: str = ""
    temperature: float | None = None
    seed: int | None = None


class RunArtifactCapture:
    """Collect provider calls and per-round mutation evaluator results."""

    def __init__(self) -> None:
        """Initialize an empty generation trace."""
        self.completions: list[CompletionArtifact] = []
        self.mutation_scores: dict[int, float] = {}
        self.mutation_errors: dict[int, str] = {}
        self.current_round_index: int | None = None

    def begin_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> int:
        """Record a request before contacting the LLM provider."""
        self.completions.append(
            CompletionArtifact(
                system_prompt,
                user_prompt,
                temperature=temperature,
                seed=seed,
            )
        )
        self.current_round_index = len(self.completions) - 1
        return self.current_round_index

    def record_output(self, round_index: int, response: LLMResponse) -> None:
        """Attach the exact provider response to its recorded request."""
        self.completions[round_index].raw_output = response.content

    def record_error(self, round_index: int, error: Exception) -> None:
        """Attach the provider error to the request that raised it."""
        self.completions[round_index].error = _format_error(error)


class RecordingProvider:
    """Delegate completions while retaining exact prompts and raw responses."""

    def __init__(
        self,
        provider: LLMProvider,
        capture: RunArtifactCapture,
    ) -> None:
        """Initialize with a provider and a per-engine trace."""
        self._provider = provider
        self._capture = capture

    @property
    def temperature(self) -> float | None:
        """Return the wrapped provider's default temperature when available."""
        value = getattr(self._provider, "temperature", None)
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def seed(self) -> int | None:
        """Return the wrapped provider's default seed when available."""
        value = getattr(self._provider, "seed", None)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @property
    def supports_sampling_overrides(self) -> bool:
        """Report whether the wrapped provider accepts per-call sampling."""
        return callable(getattr(self._provider, "complete_with_sampling", None))

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Record one provider call without changing its inputs or response."""
        round_index = self._capture.begin_completion(
            system_prompt,
            user_prompt,
            self.temperature,
            self.seed,
        )
        try:
            response = self._provider.complete(system_prompt, user_prompt)
        except Exception as exc:
            self._capture.record_error(round_index, exc)
            raise
        self._capture.record_output(round_index, response)
        return response

    def complete_with_sampling(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        seed: int,
    ) -> LLMResponse:
        """Record and delegate a completion with per-call sampling settings."""
        round_index = self._capture.begin_completion(
            system_prompt,
            user_prompt,
            temperature,
            seed,
        )
        try:
            complete_with_sampling = getattr(
                self._provider,
                "complete_with_sampling",
                None,
            )
            if not callable(complete_with_sampling):
                raise TypeError(
                    "The configured provider does not support per-call sampling"
                )
            response = complete_with_sampling(
                system_prompt,
                user_prompt,
                temperature=temperature,
                seed=seed,
            )
        except Exception as exc:
            self._capture.record_error(round_index, exc)
            raise
        self._capture.record_output(round_index, response)
        return response


class RecordingMutationEvaluator:
    """Delegate mutation evaluation and retain scores by agent round."""

    def __init__(
        self,
        evaluator: _MutationEvaluator,
        capture: RunArtifactCapture,
    ) -> None:
        """Initialize with the unchanged evaluator and its trace."""
        self._evaluator = evaluator
        self._capture = capture

    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        deselected_test_ids: tuple[str, ...] = (),
    ) -> MutationResult:
        """Return the delegate result and record its round association."""
        round_index = self._capture.current_round_index
        if round_index is None:
            raise RuntimeError("Mutation evaluation has no recorded LLM round")
        try:
            result = self._evaluator.evaluate(
                test_code,
                source_path,
                deselected_test_ids,
            )
        except Exception as exc:
            self._capture.mutation_errors[round_index] = _format_error(exc)
            raise
        self._capture.mutation_scores[round_index] = result.mutation_score
        return result


def write_run_artifacts(
    artifact_root: Path,
    task_id: str,
    engine_name: str,
    test_code: str | None,
    capture: RunArtifactCapture,
    generation_error: str = "",
) -> Path:
    """Write a generated suite and its available LLM round trace to disk."""
    directory = _artifact_directory(artifact_root, task_id, engine_name)
    directory.mkdir(parents=True, exist_ok=True)
    saved_test_code = test_code
    test_code_source = "engine_returned_suite"
    if saved_test_code is None:
        successful_outputs = [
            completion.raw_output
            for completion in capture.completions
            if completion.raw_output
        ]
        if successful_outputs:
            saved_test_code = _strip_markdown_fence(successful_outputs[-1])
            test_code_source = "last_successful_round_output; engine did not return"
    if saved_test_code is not None:
        (directory / "generated_test.py").write_text(
            saved_test_code,
            encoding="utf-8",
        )
    if generation_error:
        (directory / "generation_error.txt").write_text(
            generation_error,
            encoding="utf-8",
        )

    selected_round = _selected_round(engine_name, test_code, capture)
    round_metadata = []
    for index, completion in enumerate(capture.completions):
        round_directory = directory / f"round_{index + 1:02d}"
        round_directory.mkdir(parents=True, exist_ok=True)
        (round_directory / "system_prompt.txt").write_text(
            completion.system_prompt,
            encoding="utf-8",
        )
        (round_directory / "prompt.txt").write_text(
            completion.user_prompt,
            encoding="utf-8",
        )
        (round_directory / "raw_output.txt").write_text(
            completion.raw_output,
            encoding="utf-8",
        )
        (round_directory / "evaluator_feedback.txt").write_text(
            _feedback_from_prompt(completion.user_prompt),
            encoding="utf-8",
        )
        round_metadata.append(
            {
                "round": index + 1,
                "returned": index + 1 == selected_round,
                "provider_error": completion.error,
                "temperature": completion.temperature,
                "seed": completion.seed,
                "mutation_score": capture.mutation_scores.get(index),
                "mutation_error": capture.mutation_errors.get(index, ""),
            }
        )

    metadata = {
        "task_id": task_id,
        "engine_name": engine_name,
        "rounds_recorded": len(capture.completions),
        "selected_round": selected_round,
        "suite_returned": test_code is not None,
        "generated_test_source": test_code_source if saved_test_code else None,
        "generation_error": generation_error,
        "round_details": round_metadata,
    }
    (directory / "run.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return directory


def _selected_round(
    engine_name: str,
    test_code: str | None,
    capture: RunArtifactCapture,
) -> int | None:
    """Infer the returned round from its output and evaluation outcomes."""
    if test_code is None or not capture.completions:
        return None
    if engine_name != "agent-llm":
        normalized_code = _strip_markdown_fence(test_code)
        matching_rounds = [
            index + 1
            for index, completion in enumerate(capture.completions)
            if _strip_markdown_fence(completion.raw_output) == normalized_code
        ]
        return matching_rounds[-1] if matching_rounds else len(capture.completions)

    best_round: int | None = None
    best_score = -1.0
    previous_score: float | None = None
    for index in range(len(capture.completions)):
        score = capture.mutation_scores.get(index)
        if score is None:
            continue
        if score > best_score:
            best_score = score
            best_round = index + 1
        if previous_score is not None and score <= previous_score:
            break
        previous_score = score
    if best_round is not None:
        return best_round

    normalized_code = _strip_markdown_fence(test_code)
    matching_rounds = [
        index + 1
        for index, completion in enumerate(capture.completions)
        if _strip_markdown_fence(completion.raw_output) == normalized_code
    ]
    return matching_rounds[-1] if matching_rounds else len(capture.completions)


def _feedback_from_prompt(prompt: str) -> str:
    """Extract the exact evaluator-feedback portion included in a prompt."""
    marker = "\nEvaluator feedback:\n"
    if marker not in prompt:
        return ""
    return prompt.rsplit(marker, maxsplit=1)[1]


def _strip_markdown_fence(content: str) -> str:
    """Normalize one optional outer Markdown code fence like the engine does."""
    lines = content.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return content.strip()


def _artifact_directory(
    artifact_root: Path,
    task_id: str,
    engine_name: str,
) -> Path:
    """Resolve and validate task and engine components under the artifact root."""
    task_parts = task_id.split("/")
    if any(part in {"", ".", ".."} for part in task_parts):
        raise ValueError(f"Invalid task ID for artifact path: {task_id!r}")
    if not re.fullmatch(r"[a-z0-9-]+", engine_name):
        raise ValueError(f"Invalid engine name for artifact path: {engine_name!r}")
    return Path(artifact_root).joinpath(*task_parts, engine_name)


def _format_error(error: Exception) -> str:
    """Format an exception without multiline output."""
    message = " ".join(str(error).split()) or "(no details)"
    return f"{type(error).__name__}: {message}"
