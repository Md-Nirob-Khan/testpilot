## 2026-10-30 — Phase 1 core
- Asked: Read CLAUDE.md, set up Python 3.10 and the virtual environment, then build Phase 1 core with unit tests; ask before system-wide installs.
- Done: Created a project-local Python 3.10 environment and implemented the Phase 1 core.
- Outcome: needed fixes

## 2026-10-30 — Phase 2 evaluator
- Asked: Read CLAUDE.md, implement Phase 2 evaluators only, run mutmut natively on macOS, run all tests, and commit.
- Done: Added isolated line/branch coverage evaluation, mutmut mutation scoring, wrong-test classification, tests, and evaluator documentation.
- Outcome: needed fixes

## 2026-10-30 — Anthropic pricing and Ollama validation
- Asked: Push Phase 2, update Anthropic model and tiered prices, run a real Ollama generate/evaluate flow, run all tests, then commit and push.
- Done: Pushed Phase 2 and added the requested Haiku model default, 100K-token pricing tiers, and pricing tests; Ollama installation and end-to-end validation are in progress.
- Outcome: needed fixes

## 2026-10-30 — Ollama fallback E2E completion
- Asked: Retry Ollama service/model setup as directed, use the smaller model after llama3.1 EOF failures, run the end-to-end evaluation, run all tests, commit, and push.
- Done: Generated example tests with qwen2.5-coder:1.5b, corrected three wrong float expectations before scoring, obtained 100% line coverage and a 100% mutation score, and added baseline validation before mutation scoring.
- Outcome: needed fixes

## 2026-10-30 — Phase 3 agent engine
- Asked: Add the raw-output scoring rule to CLAUDE.md, read it, implement Phase 3 only, run all tests, then commit and push.
- Done: Added a bounded iterative engine with wrong-test-first scoring, coverage/mutation feedback, highest-score selection, and unit tests.
- Outcome: needed fixes

## 2026-10-30 — Phase 4 Pynguin baseline
- Asked: Read CLAUDE.md, implement Phase 4 only with Pynguin in a separate Python 3.10 environment and a sandboxed subprocess, run all tests, then commit and push.
- Done: Created `.venv-pynguin`, added the isolated Pynguin runner and engine, tests, and setup documentation.
- Outcome: worked as is

## 2026-10-30 — Phase 5 dashboard
- Asked: Read CLAUDE.md, build the first half of Phase 5 as a Streamlit comparison dashboard with SQLite run history, run all tests, verify startup, then commit and push.
- Done: Added source upload/paste, function and engine selection, isolated generation/evaluation, metric comparisons, generated-test downloads, and SQLite history.
- Outcome: needed fixes

## 2026-10-30 — Phase 5 merge and quality checks
- Asked: Read CLAUDE.md, add the best-of merge, flaky-test check, and mutant explainer to the dashboard, run all tests, then commit and push.
- Done: Added greedy mutant-kill test merging, three-run per-test stability checks, diff-based survivor explanations, dashboard/history integration, and tests.
- Outcome: needed fixes

## 2026-10-30 — Phase 6 HumanEval trial
- Asked: Run all three engines on 10 HumanEval functions, save CSV results with model/settings/date, report the table and elapsed time, commit and push, then estimate the 164-function run and wait for approval.
- Done: Added a HumanEval JSONL loader and experiment command; saved 30 trial rows with model, settings, date, and evaluation metrics. The run took 663.5 seconds; 15 rows completed and 15 recorded engine/evaluation errors.
- Outcome: worked as is

## 2026-10-30 — Phase 6 fairness fixes
- Asked: Fix mutation diagnostics, score only passing tests, recover the agent from evaluator failures, retry Ollama connection refusals, and exclude xfail-marked tests from wrong-test and quality metrics; verify selected HumanEval cases.
- Done: Added clearer mutmut diagnostics, zero-score handling when no tests cover mutants, failure categorization and passing-only scoring, evaluator-error feedback, one Ollama refusal retry, and separate xfail counting/exclusion for all engines; preserved interrupted v1 CSVs and reran the six requested functions.
- Outcome: needed fixes

## 2026-10-30 — Reproducible HumanEval scoring
- Asked: Explain prior missing metrics, report zero scores with a no-scorable flag, make Ollama generation deterministic and record its settings, move the dataset into `data/`, rerun the six selected tasks, run all tests, then commit and push.
- Done: Added explicit no-scorable metrics/flagging, fixed Ollama temperature and seed metadata, moved the dataset to `data/HumanEval.jsonl.gz`, and reran the six selected tasks.
- Outcome: needed fixes

## 2026-10-30 — HumanEval scoring regression investigation
- Asked: Inspect HumanEval/53 artifacts, compare the regression with the prior commit, add an end-to-end add control, rerun six tasks, run all tests, then commit and push.
- Done: Found missing target imports in fixed-seed LLM output, made the import instruction explicit, corrected runtime failure classification, pinned Pynguin's seed, added the end-to-end add control, and reran the six selected tasks.
- Outcome: needed fixes
