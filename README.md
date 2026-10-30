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

## Configure a provider

Copy `.env.example` to `.env`. Ollama is the default provider and expects a local
server at `http://localhost:11434`; set `OLLAMA_MODEL` to an installed model.
For Anthropic, set `TESTPILOT_LLM_PROVIDER=anthropic` and provide
`ANTHROPIC_API_KEY`. The default Anthropic cost estimate uses the configured
per-million-token rates in `.env`; update them when using a differently priced
model. `.env` is ignored by git.

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
that either the test or implementation is wrong.

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

Run TestPilot's unit tests with:

```sh
python -m pytest
```
