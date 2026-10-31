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
Both LLM engines are instructed to import and call the target from
`testpilot_target` without copying or redefining it. Single-shot makes exactly
one generation request; experiment rows separately flag suites that fail the
AST target-usage check and assign those suites zero coverage and mutation. The
check recognizes direct function imports and aliases, module imports and
aliases, plus Pynguin's `sys.modules["testpilot_target"]` module reference.
It flags suites that redefine or shadow the function or never call it.
Generated tests are never edited before they are run or scored.
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
The agent uses temperature 0 for round 1 and temperature 0.7 for later Ollama
rounds, with seed `42 + round number`; its CSV records the sampling settings of
the returned suite. Target-valid raw suites are sent to the wrong-test detector first. Passing
suites are measured for coverage and mutation score; failing suites are
reported to the next model round unchanged. Suites that redefine the target or
do not directly call its imported implementation are rejected with explicit
correction feedback. Repeated candidate suites stop the loop without another
evaluation. The engine returns the passing suite with the highest mutation
score.
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

Install the base project dependencies and start Streamlit from the repository
root:

```sh
python -m pip install -e ".[dev]"
python -m streamlit run app.py
```

The app opens on `localhost` with a dark, wide-layout interface. Its sidebar
lets you choose engines, the LLM provider and model, and the agent's maximum
rounds. Configure provider credentials and local Ollama settings in `.env`
before running LLM engines.

On **Generate & compare**, select one of four built-in examples or paste/upload
Python source. The default `grade(score)` example includes threshold branches
and boundary values, so it can be run immediately. Choose functions and
engines, then select **Generate, evaluate & compare**. Results show per-engine
metric cards, a coverage/mutation comparison chart, and syntax-highlighted
engine tabs with downloads. Best-of merge output, repeated-run flaky checks,
and expandable surviving-mutant explanations are shown with the run.

Every submitted comparison, including engine failures, is stored in the local
SQLite database `testpilot_runs.sqlite3`. Set `TESTPILOT_DB_PATH` to choose a
different database location. **Run history** restores saved metrics and
generated suites. Generated tests and Pynguin run in the existing
timeout-bounded subprocesses with a minimal environment that does not inherit
provider credentials. These are not OS-level security sandboxes.

**Experiment results** reads
`results/v3/humaneval_full_164_rescored.csv` and computes the engine summaries,
charts, failure counts, target-call callout, and paired Wilcoxon p-values from
that CSV. Install the optional analysis dependencies to enable its statistical
tests:

```sh
python -m pip install -e ".[analysis]"
```

Run TestPilot's unit tests with:

```sh
python -m pytest
```

## HumanEval experiment

The bundled `data/HumanEval.jsonl.gz` dataset is the MIT-licensed benchmark
from [OpenAI's human-eval repository](https://github.com/openai/human-eval).
Run a bounded trial before considering the full benchmark:

```sh
python -m testpilot.experiment \
  --dataset data/HumanEval.jsonl.gz \
  --output results/humaneval_trial_10.csv \
  --limit 10
```

Each CSV row records the run date, configured LLM model, Ollama temperature and
seed, engine settings, generation and evaluation time, line/branch coverage,
mutation score, and wrong-test results. Ollama uses temperature `0` and seed
`42` by default. Rows with no passing, non-xfail tests, or whose passing tests
never execute the target code, record zero coverage and mutation scores and set
`no_scorable_tests`; these rows remain included in aggregates instead of
disappearing as missing values. The three engines are
single-shot LLM, Agent LLM
(three-round maximum), and Pynguin (30-second search, 120-second subprocess
timeout, fixed seed `42`). Benchmark suites are checked against the canonical
solutions. Sampling metadata is blank for Pynguin because it does not use the
LLM; its seed is recorded in the engine settings.
All scoring subprocesses use pytest's `--runxfail` so generated
`xfail(strict=True)` markers cannot hide failing assertions or interfere with
mutmut's forced-failure check. Xfail-marked cases are counted separately in
`expected_failure_count` and are neither classified as wrong tests nor included
in coverage or mutation scoring. The raw suite remains unchanged; pytest
deselection excludes wrong and xfail cases from scoring, while the CSV records
each wrong test and its syntax/import/assertion/runtime-error category. If
passing tests exist but an evaluator fails, the row retains the evaluator error
rather than substituting a zero. If no passing test
executes mutated code, mutmut's early-exit diagnostic is reported as a zero
mutation score with all generated mutants classified as surviving.
An Ollama connection refusal is retried once; a second refusal is labeled as an
infrastructure error. Generated test files are not edited.
Generated tests and Pynguin continue to run only in their timeout-bounded
subprocesses. Running all 164 problems requires explicitly changing `--limit`;
measure a trial first and estimate the full run from its observed elapsed time.
After reviewing and approving the trial, the remaining records can be run
without repeating the first 10:

```sh
python -m testpilot.experiment \
  --dataset data/HumanEval.jsonl.gz \
  --output results/humaneval_remaining_154.csv \
  --limit 154 \
  --offset 10
```

Use `--task-ids HumanEval/41 HumanEval/42` to rerun selected cases across all
three engines without running the full benchmark.
Add `--resume` to append completed rows and skip task/engine pairs already
present in the output CSV after an interrupted run.
Use `--artifact-dir results/artifacts` to retain each generated suite. For LLM
engines, this also saves prompts and raw responses by round; agent traces include
the evaluator feedback sent to each round and the selected returned round. Limit
generation with `--engines single-shot-llm agent-llm` when Pynguin is not needed.

Analyze a completed HumanEval CSV and generate a Markdown report plus PNG
charts. Install the optional analysis dependencies, then run:

```sh
python -m pip install -e ".[analysis]"
python -m testpilot.humaneval_analysis \
  --input results/v2/humaneval_full_164.csv \
  --output-dir results/v2
```

The report includes a complete-case comparison across all three engines,
all-function failure counts, and paired Wilcoxon signed-rank tests. Charts use
the same complete-case cohort as the paired comparison.
