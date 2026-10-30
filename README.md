# TestPilot

TestPilot generates pytest tests for Python functions and runs generated tests in a
temporary subprocess. Phase 1 supports function analysis, Ollama and Anthropic
providers, single-shot generation, and a sandbox runner.

## Setup

The project targets Python 3.10. The local `.venv` is a Conda environment. Activate
it with:

```sh
conda activate ./.venv
```

Install the package and test dependencies:

```sh
python -m pip install -e ".[dev]"
```

`radon` supplies cyclomatic complexity in the analyzer, `python-dotenv` loads
provider settings from `.env`, and `pytest` runs the project and generated tests.
The provider clients use Python's standard-library HTTP support rather than an
additional SDK.
Streamlit is the web dashboard runtime.

## Configure a provider

Copy `.env.example` to `.env`. Ollama is the default provider and expects a local
server at `http://localhost:11434`; set `OLLAMA_MODEL` to an installed model.
For Anthropic, set `TESTPILOT_LLM_PROVIDER=anthropic` and provide
`ANTHROPIC_API_KEY`. The default Anthropic cost estimate uses the configured
per-million-token rates in `.env`, selecting the higher tier when the prompt
exceeds 100,000 input tokens. `.env` is ignored by git.

## Generate tests

```sh
python -m testpilot generate examples/sample.py
```

The command prints the generated suite to stdout. Use `--function` when the
source file contains multiple functions, `--output tests_generated.py` to save
the suite, and `--run` to run it in the sandbox. The sandbox copies the source
file and generated suite into a temporary directory, launches pytest in a
subprocess with a timeout, and removes the temporary directory afterward.
This subprocess boundary and timeout are not an OS-level security sandbox;
Docker isolation is not currently included.

## Evaluate generated tests

The Phase 2 evaluators are available as Python APIs. Coverage uses coverage.py
to report line and branch results; mutation evaluation uses mutmut to report
killed and surviving mutants. Both copy the target and generated tests into a
temporary directory and execute them in subprocesses with timeouts. The wrong
test detector runs tests against a canonical benchmark solution or user code;
failures against user code are reported as needing human review, not as proof
that either the test or implementation is wrong. Mutation evaluation first
checks that the tests pass on the original source and rejects failing suites
instead of counting those failures as mutant kills.

```python
from pathlib import Path

from testpilot.evaluator import CoverageEvaluator, MutationEvaluator

source = Path("examples/sample.py")
tests = "from testpilot_target import is_even\n\ndef test_even():\n    assert is_even(2)\n"

coverage = CoverageEvaluator().evaluate(tests, source)
mutation = MutationEvaluator().evaluate(tests, source)
print(coverage.line_percent, coverage.branch_percent)
print(mutation.mutation_score, mutation.surviving_mutant_names)
```

Mutmut runs natively on macOS, with its `use_setproctitle` option disabled.

## Iterative agent engine

Phase 3 adds `AgentEngine`, which generates up to three suites by default.
Every raw suite is sent to the wrong-test detector first. Passing suites are
measured for coverage and mutation score; failing suites are reported to the
next model round unchanged. The engine returns the passing suite with the
highest mutation score, or the last raw suite if none pass.
The result reports benchmark wrong-test failures and user-code failures needing
human review separately across all attempted rounds.

```python
from pathlib import Path

from testpilot.analyzer import analyze_file
from testpilot.engines import AgentEngine
from testpilot.llm import create_provider

function_info = analyze_file(Path("examples/sample.py"))[0]
suite = AgentEngine(create_provider()).generate(
    function_info,
    Path("examples/sample.py"),
)
print(
    suite.test_code,
    suite.rounds,
    suite.wrong_test_count,
    suite.needs_human_review_count,
)
```

Set `is_benchmark=True` when constructing `AgentEngine` for a canonical
benchmark implementation so failing tests are classified as wrong tests rather
than cases needing human review.

## Pynguin baseline

Phase 4 runs Pynguin in its own Python 3.10 environment. Create it from the
project's Python 3.10 interpreter and install the pinned Pynguin dependency:

```sh
./.venv/bin/python -m venv .venv-pynguin
./.venv-pynguin/bin/python -m pip install -r requirements-pynguin.txt
```

On Windows, use `.venv-pynguin\Scripts\python.exe` for the environment's
interpreter. `PynguinEngine` launches Pynguin only in a timeout-bounded
subprocess, copies the source into a temporary directory, and returns the raw
generated suite. The `PYNGUIN_DANGER_AWARE` opt-in is added only to that child
process's environment.

```python
from pathlib import Path

from testpilot.analyzer import analyze_file
from testpilot.engines import PynguinEngine

source = Path("examples/sample.py")
suite = PynguinEngine().generate(analyze_file(source)[0], source)
print(suite.test_code)
```

## Dashboard and run history

Start the Streamlit dashboard from the project root:

```sh
streamlit run app.py
```

Paste Python source or upload a `.py` file, select functions and generation
engines, then generate and evaluate their suites. The comparison shows line and
branch coverage, mutation score, wrong-test status, elapsed time, and estimated
cost, with a download button for each generated suite. LLM engines use the
provider configured through `.env`; Pynguin runs in `.venv-pynguin`.

Every submitted comparison, including engine failures, is stored in the local
SQLite database `testpilot_runs.sqlite3`. Set `TESTPILOT_DB_PATH` to choose a
different database location. Use the Run history page to review saved metrics
and download previously generated suites. Generated tests and Pynguin run in
the existing timeout-bounded subprocesses with a minimal environment that does
not inherit provider credentials. These are not OS-level security sandboxes.

Run TestPilot's unit tests with:

```sh
python -m pytest
```
