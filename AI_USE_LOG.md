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

## 2026-10-30 — HumanEval generation artifact capture
- Asked: Save generated suites and agent round prompts, outputs, evaluator feedback, and returned-round metadata; reproduce selected HumanEval cases without modifying scoring or agent logic.
- Done: Added opt-in experiment artifact capture and saved traces for HumanEval/2, /10, /11, and /18 using single-shot and agent engines. The agent run for /2 timed out during its second provider call; its first-round output and failed retry prompt were preserved.
- Outcome: needed fixes

## 2026-10-30 — HumanEval generation validation
- Asked: After reviewing the reproduction evidence, implement target-usage validation and stop agent rounds when a generated suite repeats exactly.
- Done: Added AST validation with one corrective retry for single-shot generation, explicit target-usage feedback for agent rounds, duplicate-candidate stopping, artifact returned-round accuracy, documentation, and regression tests.
- Outcome: needed fixes

## 2026-10-31 — HumanEval target-flag audit
- Asked: Cross-check all flagged v3 suites, rescore rows whose flags were wrong using saved artifacts, generate the rescored analysis and charts, run all tests, then commit and push.
- Done: Confirmed 160 Pynguin target-usage flags were false positives and 73 LLM flags were confirmed; rescored all 160 affected Pynguin rows, recorded three mutmut errors per row, generated the v3 summary and charts, and passed all 140 tests.
- Outcome: needed fixes

## 2026-10-30 — HumanEval v3 full experiment
- Asked: Keep single-shot to one attempt, record target-usage failures, vary deterministic agent sampling after round one, validate the reproduction, run all tests, commit and push, then start a resumable artifact-captured 164-function run.
- Done: Completed the requested settings and measurement changes, reproduced selected HumanEval cases, passed the full test suite, and started the v3 full run with `caffeinate`.
- Outcome: worked as is

## 2026-10-30 — HumanEval full-run analysis
- Asked: Analyze the completed 164-function CSV with paired metrics, failure counts, Wilcoxon tests, Pynguin xfail-only count, and charts; test the summary logic, run all tests, then commit and push.
- Done: Added an optional SciPy/Matplotlib analysis command, generated `results/v2/summary.md` and three charts, and validated the complete 492-row dataset.
- Outcome: needed fixes

## 2026-10-31 — Dashboard redesign (GitHub Copilot, first half)
- Asked: Redesign the Streamlit dashboard (wide layout, dark theme, sidebar settings, sample dropdown, metric cards, engine tabs, mutant cards, Experiment results page, `width` parameter instead of `use_container_width`) without touching engines, evaluator, scoring or experiment code.
- Done: GitHub Copilot produced most of `app.py`, `.streamlit/config.toml`, `testpilot/dashboard_summary.py`, its tests and a README draft, then ran out of credits before finishing, with the work uncommitted and the test suite not yet verified.
- Outcome: needed fixes

## 2026-10-31 — Dashboard redesign (finished with Claude Code)
- Asked: Switch from Copilot to Claude Code after Copilot's credit limit; inspect the uncommitted diff, finish the remaining work without redoing it, update README and this log, run all tests, then commit and push.
- Done: Reviewed the Copilot changes and confirmed that all seven dashboard items were already implemented, including no remaining `use_container_width` and a CSV-derived Experiment results page. Ran the full suite and found one failing test (`test_history_page_renders_flaky_merge_and_mutant_details`): Copilot's change renders selected merge tests as markdown, but the test still looked for them in text elements. I fixed the test assertion only. The suite then passed with 143 tests. I did not run the dashboard in a browser, so the visual look is not verified. Untracked experiment artifacts under `results/` and `.vscode/` were not part of this commit.
- Outcome: worked as is

## 2026-10-31 — Colorful dashboard polish
- Asked: Give each engine a fixed color, add gradient hero headers, accent metric cards with a Best badge, labeled status badges, transparent Plotly charts, a prominent headline callout, and Inter font styling, with UI changes only.
- Done: Added `testpilot/dashboard_ui.py` (colors, CSS, HTML builders, Plotly figure) with tests, rewired `app.py` to use it, and added the `plotly` dependency because the request names Plotly charts. Updated two app tests whose visible-text checks moved from title and warning elements to markdown. All 150 tests pass. I did not view the result in a browser, so the visual polish, per-tab colors and Google Fonts loading are unverified.
- Outcome: worked as is

## 2026-10-31 — Dashboard UI fixes (icons, Best badges, errors, cost, order)
- Asked: Fix the "uploadUpload" icon-font bug, make Best badges direction-aware with no badge on ties, show plain-English error causes with collapsed technical details, label zero cost as local, and fix engine order.
- Done: Scoped Inter away from Material icon elements; added per-metric `best_flags`, `classify_failure` and `ordered_by_engine` in `testpilot/dashboard_ui.py` with tests; zero cost shows "$0.00 (local model)" (Pynguin shows "$0.00 (no LLM)" because it uses no model). All 160 tests pass. The icon fix and the look of every page were not checked in a browser (no browser tool here), so please confirm that no icon names still show as text.
- Outcome: worked as is

## 2026-10-31 — Demo improvements (wrong-test reasons, mutant titles, local time)
- Asked: Show why each wrong test is wrong, give surviving-mutant cards plain-language titles sorted by number, and show Run history timestamps in local time.
- Done: Added `testpilot/failure_reasons.py` (runs the suite in the sandbox after generation and parses pytest's failing assertion), a "Why this test is wrong" box, mutant titles and numeric sorting, and local-time formatting, with tests; 170 tests pass. The reasons are stored in a new additive `wrong_test_reasons_json` column of the SQLite history, so this goes slightly beyond UI code; older runs show no reasons. Mutmut's diff line numbers are relative to the function's first line, not the file, so titles read "Line 2 of ticket_price()", which I checked on a real mutmut run. The extra sandbox run happens only for suites that have wrong tests. Not checked in a browser.
- Outcome: worked as is
