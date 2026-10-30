"""Command-line entry point for Phase 1."""

import argparse
import sys
from pathlib import Path

from testpilot.analyzer import FunctionInfo, analyze_file
from testpilot.engines import SingleShotEngine
from testpilot.llm import create_provider
from testpilot.sandbox import SandboxRunner


def main(argv: list[str] | None = None) -> int:
    """Run the TestPilot command-line interface."""
    parser = argparse.ArgumentParser(prog="testpilot")
    commands = parser.add_subparsers(dest="command", required=True)
    generate_parser = commands.add_parser(
        "generate",
        help="Generate pytest tests for a Python source file",
    )
    generate_parser.add_argument("source", type=Path)
    generate_parser.add_argument("--function")
    generate_parser.add_argument("--provider", choices=("ollama", "anthropic"))
    generate_parser.add_argument("--output", type=Path)
    generate_parser.add_argument("--run", action="store_true")
    generate_parser.add_argument("--timeout", type=float, default=30.0)
    arguments = parser.parse_args(argv)

    if arguments.command == "generate":
        return _generate(arguments, parser)
    parser.error(f"Unknown command: {arguments.command}")
    return 2


def _generate(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    source_path: Path = arguments.source
    functions = analyze_file(source_path)
    function_info = _select_function(functions, arguments.function, parser)
    provider = create_provider(arguments.provider)
    suite = SingleShotEngine(provider).generate(function_info, source_path)

    if arguments.output is None:
        print(suite.test_code)
    else:
        arguments.output.write_text(suite.test_code + "\n", encoding="utf-8")
        print(f"Wrote generated tests to {arguments.output}", file=sys.stderr)

    print(
        f"Generated with {suite.engine_name}; {suite.llm_tokens_used} tokens; "
        f"${suite.estimated_cost_usd:.6f}; {suite.wall_clock_seconds:.2f}s",
        file=sys.stderr,
    )
    if arguments.run:
        result = SandboxRunner(arguments.timeout).run(suite.test_code, source_path)
        print(
            f"Sandbox: {result.passed} passed, {result.failed} failed, "
            f"{result.errors} errors, {result.skipped} skipped"
            + (" (timed out)" if result.timed_out else ""),
            file=sys.stderr,
        )
        if result.stdout:
            print(result.stdout, file=sys.stderr, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return 1 if result.timed_out or result.returncode != 0 else 0
    return 0


def _select_function(
    functions: list[FunctionInfo],
    requested_name: str | None,
    parser: argparse.ArgumentParser,
) -> FunctionInfo:
    if requested_name is not None:
        for function in functions:
            if function.name == requested_name:
                return function
        parser.error(f"Function {requested_name!r} was not found in the source file")
    if not functions:
        parser.error("No top-level functions were found in the source file")
    if len(functions) > 1:
        names = ", ".join(function.name for function in functions)
        parser.error(f"Source has multiple functions ({names}); choose one with --function")
    return functions[0]


if __name__ == "__main__":
    raise SystemExit(main())
