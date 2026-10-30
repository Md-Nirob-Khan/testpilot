"""Build pytest selections that exclude generated test cases that failed."""

from dataclasses import dataclass
from collections.abc import Sequence
import ast

from testpilot.sandbox.runner import TestOutcome


@dataclass(frozen=True)
class PassingTestSelection:
    """Describe passing, wrong, and expected-failure pytest cases."""

    passing_test_count: int
    deselected_test_ids: tuple[str, ...]
    wrong_test_outcomes: tuple[TestOutcome, ...]
    expected_failure_outcomes: tuple[TestOutcome, ...]

    def for_test_file(self, test_file: str) -> tuple[str, ...]:
        """Return pytest deselection prefixes for a concrete test-file path."""
        return tuple(
            f"{test_file}::{node_id}" for node_id in self.deselected_test_ids
        )

    @property
    def expected_failure_count(self) -> int:
        """Return the number of collected xfail-marked pytest cases."""
        return len(self.expected_failure_outcomes)

    @property
    def wrong_test_count(self) -> int:
        """Return the number of failing cases not marked as expected failures."""
        return len(self.wrong_test_outcomes)


def passing_test_selection(
    test_code: str,
    outcomes: Sequence[TestOutcome],
) -> PassingTestSelection | None:
    """Separate passing/wrong/xfail cases and exclude wrong/xfail cases from scores."""
    if not outcomes:
        return None
    xfail_keys = _xfail_test_keys(test_code)
    passing_count = 0
    wrong: list[TestOutcome] = []
    expected_failures: list[TestOutcome] = []
    deselected: list[str] = []
    for outcome in outcomes:
        is_xfail = _is_xfail_outcome(outcome, xfail_keys)
        if is_xfail:
            expected_failures.append(outcome)
            deselected.append(_pytest_node_id(outcome.name))
        elif outcome.status in ("failed", "error"):
            wrong.append(outcome)
            deselected.append(_pytest_node_id(outcome.name))
        elif outcome.status == "passed":
            passing_count += 1
    return PassingTestSelection(
        passing_test_count=passing_count,
        deselected_test_ids=tuple(dict.fromkeys(deselected)),
        wrong_test_outcomes=tuple(wrong),
        expected_failure_outcomes=tuple(expected_failures),
    )


def _xfail_test_keys(
    test_code: str,
) -> set[tuple[str | None, str, str | None]]:
    """Find test functions decorated with xfail at module, class, or function scope."""
    try:
        module = ast.parse(test_code)
    except SyntaxError:
        return set()

    module_xfail = any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "pytestmark"
            for target in node.targets
        )
        and _contains_xfail_marker(node.value)
        for node in module.body
    )
    xfail_tests: set[tuple[str | None, str, str | None]] = set()
    for node in module.body:
        if _is_test_function(node):
            _add_function_xfail_keys(
                xfail_tests,
                node,
                None,
                module_xfail,
            )
        elif isinstance(node, ast.ClassDef):
            class_xfail = module_xfail or _has_direct_xfail_decorator(node) or any(
                isinstance(member, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "pytestmark"
                    for target in member.targets
                )
                and _contains_xfail_marker(member.value)
                for member in node.body
            )
            for member in node.body:
                if _is_test_function(member):
                    _add_function_xfail_keys(
                        xfail_tests,
                        member,
                        node.name,
                        class_xfail,
                    )
    return xfail_tests


def _add_function_xfail_keys(
    xfail_tests: set[tuple[str | None, str, str | None]],
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_name: str | None,
    inherited_xfail: bool,
) -> None:
    if inherited_xfail or _has_direct_xfail_decorator(node):
        xfail_tests.add((class_name, node.name, None))
        return
    xfail_tests.update(
        (class_name, node.name, parameter_id)
        for parameter_id in _xfail_parameter_ids(node)
    )


def _has_direct_xfail_decorator(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> bool:
    return any(_is_xfail_decorator(decorator) for decorator in node.decorator_list)


def _is_xfail_decorator(node: ast.expr) -> bool:
    if isinstance(node, ast.Call):
        return _is_xfail_decorator(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr == "xfail"
    return isinstance(node, ast.Name) and node.id == "xfail"


def _xfail_parameter_ids(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    parameter_ids: set[str] = set()
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call) or not _is_parametrize_call(
            decorator.func
        ):
            continue
        if len(decorator.args) < 2:
            continue
        parameters = decorator.args[1]
        if not isinstance(parameters, (ast.List, ast.Tuple)):
            continue
        for parameter in parameters.elts:
            if not isinstance(parameter, ast.Call) or not _is_param_call(
                parameter.func
            ):
                continue
            marks = next(
                (
                    keyword.value
                    for keyword in parameter.keywords
                    if keyword.arg == "marks"
                ),
                None,
            )
            if marks is None or not _contains_xfail_marker(marks):
                continue
            parameter_id = next(
                (
                    keyword.value.value
                    for keyword in parameter.keywords
                    if keyword.arg == "id"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ),
                None,
            )
            if parameter_id is None:
                parameter_id = _default_parameter_id(parameter.args)
            if parameter_id is not None:
                parameter_ids.add(parameter_id)
    return parameter_ids


def _is_parametrize_call(node: ast.expr) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "parametrize"


def _is_param_call(node: ast.expr) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "param"


def _default_parameter_id(arguments: list[ast.expr]) -> str | None:
    try:
        values = [ast.literal_eval(argument) for argument in arguments]
    except (ValueError, TypeError):
        return None
    if not values:
        return None
    return "-".join(str(value) for value in values)


def _contains_xfail_marker(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        return _contains_xfail_marker(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr == "xfail" or _contains_xfail_marker(node.value)
    if isinstance(node, ast.Name):
        return node.id == "xfail"
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return any(_contains_xfail_marker(item) for item in node.elts)
    return False


def _is_test_function(node: ast.stmt) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
        node.name.startswith("test_")
    )


def _outcome_key(name: str) -> tuple[str | None, str, str | None]:
    """Normalize a JUnit ID to its class, function, and parameter ID."""
    module_and_test = name.rsplit("::", maxsplit=1)
    test_name = module_and_test[-1]
    parameter_id = None
    if test_name.endswith("]") and "[" in test_name:
        test_name, parameter_id = test_name.rsplit("[", maxsplit=1)
        parameter_id = parameter_id[:-1]
    class_name = None
    if len(module_and_test) > 1:
        class_name = module_and_test[0].rsplit(".", maxsplit=1)[-1]
        if class_name == module_and_test[0]:
            class_name = None
    return class_name, test_name, parameter_id


def _is_xfail_outcome(
    outcome: TestOutcome,
    xfail_tests: set[tuple[str | None, str, str | None]],
) -> bool:
    class_name, test_name, parameter_id = _outcome_key(outcome.name)
    return any(
        marker_test == test_name
        and (marker_class is None or marker_class == class_name)
        and (marker_parameter is None or marker_parameter == parameter_id)
        for marker_class, marker_test, marker_parameter in xfail_tests
    )


def _pytest_node_id(junit_name: str) -> str:
    """Convert a JUnit class/name pair into its pytest class and case suffix."""
    module_and_class, test_name = (
        junit_name.rsplit("::", maxsplit=1)
        if "::" in junit_name
        else ("", junit_name)
    )
    module_parts = module_and_class.split(".")
    if len(module_parts) > 1:
        return f"{module_parts[-1]}::{test_name}"
    return test_name
