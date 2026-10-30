"""Single-shot test generation using an LLM provider."""

import time
from pathlib import Path

from testpilot.analyzer import FunctionInfo
from testpilot.engines.base import GeneratedSuite
from testpilot.llm import LLMProvider


class SingleShotEngine:
    """Generate a pytest suite in one provider request."""

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize the engine with its provider."""
        self._provider = provider

    def generate(
        self,
        function_info: FunctionInfo,
        source_path: Path,
    ) -> GeneratedSuite:
        """Generate one pytest suite and preserve provider usage metrics."""
        system_prompt = _SYSTEM_PROMPT
        user_prompt = build_test_prompt(function_info, source_path)
        started = time.perf_counter()
        response = self._provider.complete(system_prompt, user_prompt)
        elapsed = time.perf_counter() - started
        test_code = _strip_markdown_fence(response.content)
        if not test_code.strip():
            raise ValueError("The LLM provider returned an empty test suite")
        return GeneratedSuite(
            test_code=test_code,
            engine_name="single-shot-llm",
            wall_clock_seconds=elapsed,
            llm_tokens_used=response.total_tokens,
            estimated_cost_usd=response.estimated_cost_usd,
            rounds=1,
        )


_SYSTEM_PROMPT = (
    "You write concise, correct pytest unit tests for Python functions. "
    "Return only executable Python source code, without Markdown fences."
)


def build_test_prompt(
    function_info: FunctionInfo,
    source_path: Path,
    feedback: str | None = None,
    previous_tests: str | None = None,
) -> str:
    """Build the shared function context and optional iterative feedback prompt."""
    prompt = f"""Write a pytest test module for the function below.

The source file is {Path(source_path).name!r}. In the sandbox, it is imported as
`testpilot_target`. At the top of your test module, include this import:
`from testpilot_target import {function_info.name}`. Call the imported function
by name in every test; do not rely on it being a global and do not duplicate the
implementation in the tests. Test normal behavior and meaningful edge cases
based on the implementation.

Function: {function_info.name}
Arguments: {function_info.arguments!r}
Return annotation: {function_info.return_annotation!r}
Docstring: {function_info.docstring or "(none)"}
Branches: {function_info.branches!r}
Cyclomatic complexity: {function_info.complexity}

Source:
```python
{function_info.source_code}
```
"""
    if previous_tests is not None and feedback is not None:
        prompt += f"""
Improve the previous test suite using the evaluator feedback. Return a complete
replacement pytest module, not a patch. Do not assume a failing assertion is
incorrect when the implementation is user code; use the provided evidence and
avoid unsupported expectations.

Previous raw generated tests:
```python
{previous_tests}
```

Evaluator feedback:
{feedback}
"""
    return prompt


def _strip_markdown_fence(content: str) -> str:
    """Remove one optional outer Markdown code fence."""
    lines = content.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return content.strip()
