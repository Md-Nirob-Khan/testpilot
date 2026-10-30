# HumanEval Full Experiment Analysis

- Source: `results/v2/humaneval_full_164.csv`
- Run date: 2026-10-30
- LLM model: qwen2.5-coder:1.5b
- Functions in CSV: 164

## Paired comparison

All engine averages below use the same complete-case functions: each of the three engines must have line coverage, branch coverage, mutation score, wrong-test count, total time, and estimated cost.

| Engine | Functions included | Avg line coverage (%) | Avg branch coverage (%) | Avg mutation score | Avg wrong tests | Avg time (s) | Avg cost (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-shot LLM | 123 | 30.79 | 30.56 | 0.2895 | 0.236 | 18.48 | 0.000000 |
| Agent LLM | 123 | 30.79 | 30.56 | 0.2895 | 0.236 | 50.65 | 0.000000 |
| Pynguin | 123 | 51.80 | 48.65 | 0.2772 | 0.000 | 12.52 | 0.000000 |

## All-functions failure counts

Counts use all functions in the CSV for each engine. Categories are independent and can overlap; `no_scorable_tests` is a scoring state, not necessarily an infrastructure failure.

| Engine | Functions | Timeout | Token-repeat | No scorable tests | Infrastructure error |
|---|---:|---:|---:|---:|---:|
| Single-shot LLM | 164 | 29 | 1 | 92 | 0 |
| Agent LLM | 164 | 32 | 1 | 90 | 0 |
| Pynguin | 164 | 4 | 0 | 65 | 0 |

## Paired Wilcoxon signed-rank tests

Two-sided tests compare mutation scores on every task with a score from both engines in that pair. The reported `n` is the number of paired tasks; p-values are unadjusted.

| Engine pair | Paired functions | Statistic | p-value |
|---|---:|---:|---:|
| Single-shot LLM vs Agent LLM | 128 | 0.0000 | 1 |
| Single-shot LLM vs Pynguin | 126 | 1795.5000 | 0.746484 |
| Agent LLM vs Pynguin | 123 | 1667.5000 | 0.731472 |

## Pynguin xfail-only suites

Pynguin produced **65** suites with at least one xfail-marked test and no passing or wrong tests.

## Charts

![Mutation score by engine](humaneval_mutation_score.png)

![Line and branch coverage by engine](humaneval_coverage.png)

![Average time by engine](humaneval_average_time.png)
