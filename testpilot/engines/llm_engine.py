"""Single-shot test generation using an LLM provider."""

import ast
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
        started = time.perf_counter()
        user_prompt = build_test_prompt(function_info, source_path)
        response = self._provider.complete(_SYSTEM_PROMPT, user_prompt)
        test_code = _strip_markdown_fence(response.content)
        if not test_code.strip():
            raise ValueError("The LLM provider returned an empty test suite")
        return GeneratedSuite(
            test_code=test_code,
            engine_name="single-shot-llm",
            wall_clock_seconds=time.perf_counter() - started,
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
`testpilot_target`. Import the function from testpilot_target and do not copy or redefine it.
At the top of your test module, include this import:
`from testpilot_target import {function_info.name}`. Call the imported function
by name in every test. The tests must exercise the implementation from
`testpilot_target`; never shadow `{function_info.name}` in the test module. A
suite that passes by testing a local reimplementation is invalid. Test normal
behavior and meaningful edge cases based on the implementation.

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


def target_usage_issue(test_code: str, function_name: str) -> str | None:
    """Describe whether tests import and directly call the requested target."""
    try:
        module = ast.parse(test_code)
    except SyntaxError as exc:
        return f"the generated module has a syntax error: {exc.msg}"

    definitions = [
        node.name
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == function_name
    ]
    if definitions:
        return (
            f"the generated module defines {function_name!r}; import the target "
            "instead of redefining it"
        )

    imported_names: set[str] = set()
    module_names: set[str] = set()
    sys_module_names: set[str] = set()
    for node in ast.walk(module):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "testpilot_target"
        ):
            imported_names.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name == function_name
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "testpilot_target":
                    module_names.add(
                        alias.asname or alias.name.split(".", maxsplit=1)[0]
                    )
                elif alias.name == "sys":
                    sys_module_names.add(alias.asname or alias.name)

    module_aliases_from_sys_modules: dict[str, ast.Name] = {}
    for node in ast.walk(module):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not _is_target_sys_modules_lookup(value, sys_module_names):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                module_aliases_from_sys_modules[target.id] = target
    module_names.update(module_aliases_from_sys_modules)

    if not imported_names and not module_names:
        return (
            f"the generated module does not import {function_name!r} "
            "from testpilot_target"
        )

    imported_bindings = imported_names | module_names
    for node in ast.walk(module):
        bound_name = None
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if any(
                node is assignment_target
                for assignment_target in module_aliases_from_sys_modules.values()
            ):
                continue
            bound_name = node.id
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            bound_name = node.name
        elif isinstance(node, ast.arg):
            bound_name = node.arg
        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Store)
            and node.attr == function_name
            and isinstance(node.value, ast.Name)
            and node.value.id in module_names
        ):
            return (
                f"the generated module redefines target attribute "
                f"{function_name!r}"
            )
        if bound_name in imported_bindings:
            return (
                "the generated module shadows imported target binding "
                f"{bound_name!r}"
            )

    test_functions = [
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not test_functions:
        return "the generated module has no pytest test functions that call the target"

    calls_target = any(
        _calls_target(node, function_name, imported_names, module_names)
        for test_function in test_functions
        for node in ast.walk(test_function)
        if isinstance(node, ast.Call)
    )
    if not calls_target:
        return f"no pytest test directly calls {function_name!r}"
    return None


def _is_target_sys_modules_lookup(
    value: ast.expr | None,
    sys_module_names: set[str],
) -> bool:
    """Return whether an expression retrieves testpilot_target from sys.modules."""
    return (
        isinstance(value, ast.Subscript)
        and isinstance(value.value, ast.Attribute)
        and value.value.attr == "modules"
        and isinstance(value.value.value, ast.Name)
        and value.value.value.id in sys_module_names
        and isinstance(value.slice, ast.Constant)
        and value.slice.value == "testpilot_target"
    )


def _calls_target(
    call: ast.Call,
    function_name: str,
    imported_names: set[str],
    module_names: set[str],
) -> bool:
    """Check whether one call targets the imported function or module member."""
    if isinstance(call.func, ast.Name):
        return call.func.id in imported_names
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == function_name
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id in module_names
    )


def _strip_markdown_fence(content: str) -> str:
    """Remove one optional outer Markdown code fence."""
    lines = content.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return content.strip()
