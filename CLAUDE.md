# TestPilot — Project Brief

Read this file before doing any work in this project.

## What this project is

TestPilot is a Streamlit web app that automatically generates pytest unit tests for Python functions using three alternative engines, then evaluates those tests honestly: coverage, mutation score, wrong tests, run time and cost.

This is a Master's-level course project. Requirements:
- Multiple alternatives in testing (three engines compared on the same benchmark)
- Good testing of TestPilot itself
- Honest reporting of hours spent and AI use

## Environment

- Python 3.10 for everything (Pynguin officially supports only 3.10).
- On Windows, the project runs inside WSL (mutmut needs fork support).
- Main app virtual environment: `.venv`
- Pynguin gets its own virtual environment: `.venv-pynguin` (called through subprocess).
- Secrets (API keys) go in `.env`, loaded with python-dotenv. `.env` must be in `.gitignore`. Never commit keys.

## Safety rule

Generated tests and Pynguin execute code. Always run them in an isolated subprocess, in a temporary directory, with a timeout. Never import or run generated or untrusted code in the main app process. Docker isolation is optional and can be added later.

## Architecture

```
testpilot/
├── analyzer/     # parse source with ast: functions, args, type hints, docstrings, branches; radon complexity
├── engines/      # common interface (see below)
│   ├── base.py
│   ├── llm_engine.py       # Engine B: LLM writes tests in one attempt
│   ├── agent_engine.py     # Engine C: iterative loop, up to N rounds
│   └── pynguin_engine.py   # Engine A: search-based baseline, no AI
├── llm/          # provider abstraction: Anthropic API and Ollama (local); records tokens and cost per call
├── sandbox/      # run pytest in a subprocess with timeout in a temp dir; capture pass/fail/errors
├── evaluator/    # coverage.py (line + branch), mutmut mutation score, wrong-test detector, flaky check
├── merge/        # best-of merge: greedy set cover to find the smallest test set that kills the most mutants
├── storage/      # SQLite run history
├── benchmarks/   # HumanEval loader (164 functions with canonical solutions) + examples/
└── app.py        # Streamlit dashboard
tests/            # TestPilot's own tests
```

### Engine interface

Every engine implements:

```python
def generate(function_info: FunctionInfo, source_path: Path) -> GeneratedSuite
```

`GeneratedSuite` holds: the pytest file text, engine name, wall-clock time, LLM tokens used, estimated cost (0 for Pynguin and local models), and number of rounds (agent only).

### Agent engine loop (Engine C)

1. Ask the LLM to write tests.
2. Run them in the sandbox.
3. Collect uncovered lines and surviving mutants.
4. Send that feedback to the LLM and ask it to improve the tests.
5. Stop when the mutation score stops improving or after N rounds (default 3).

### Wrong-test detector

- For benchmark functions (HumanEval), the canonical solution is correct, so a test that fails on it is a wrong test (AI hallucination). Count these separately from real bug findings.
- For the user's own code, correctness is unknown, so a failing test is labeled "needs human review: wrong test or real bug".
- Never correct generated tests by hand before scoring. Always score the raw output of each engine and let the wrong-test detector count incorrect tests.

### Flaky check

Run each generated test suite 3 times; flag tests whose result changes between runs.

## Coding rules

- Type hints and short docstrings on all public functions.
- Small, focused functions and modules.
- Every module gets unit tests in `tests/`. Include known-answer tests: functions with hand-written test suites of known quality, to confirm the evaluator measures correctly.
- Explain why before adding any new dependency.
- Work one phase at a time. Do not start the next phase unless asked.
- When a requirement is unclear, ask instead of guessing.
- Suggest a clear git commit message at the end of each working step.

## Build phases

1. **Core:** analyzer, LLM provider (Ollama + Anthropic), Engine B (single-shot), sandbox runner. Command-line interface first: `python -m testpilot generate examples/sample.py`.
2. **Evaluator:** coverage, mutation score, wrong-test detector.
3. **Engine C:** agent loop using evaluator feedback.
4. **Engine A:** Pynguin baseline in its own virtual environment.
5. **App:** Streamlit dashboard, best-of merge, flaky check, mutant explainer (plain-language description of each surviving mutant and the missing test case), SQLite history.
6. **Experiment:** run all three engines on HumanEval plus the developer's own code; export results to CSV for the report.

## AI-use log

Maintain `AI_USE_LOG.md`. After each task you complete, append one entry:

```
## YYYY-MM-DD — <short task name>
- Asked: <what the developer asked for>
- Done: <what was produced>
- Outcome: worked as is / needed fixes / discarded   (the developer confirms or corrects this line)
```

Never edit or delete past entries. The developer reviews each entry; the log is reported honestly in the final project report.
