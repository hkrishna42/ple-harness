---
name: ple-experiment-ledger
description: Use before and after any paid or evaluation run in ple-harness - announces the cost estimate, checks the budget line, and appends one ledger row per task run.
---

# Experiment ledger

## Before a run

1. State in chat: model, task set, task count, runs per task, estimated cost per task, total.
   The Opus 5.5 target is at most $15 per task until Phase 1 measures it.
2. Name the budget line it draws on (HANDOVER section 6): VM $100; tuning model and judge
   $150; Opus 5.5 API $250 now; $500 held back until Hari releases it. If the run would cross
   a line, stop and ask Hari.
3. Record `git rev-parse HEAD` and confirm `git status --porcelain` is empty.
4. The holdout set runs only once, at the code freeze (2026-12-28).

## After a run

Append one JSON object per task run, one line each, to `docs/eval/ledger.jsonl`:

| Field | Type | Notes |
|---|---|---|
| `run_id` | string | Unique per run, e.g. `2026-11-20-plan-verify-opus-a` |
| `date` | string | `YYYY-MM-DD` |
| `git_sha` | string | 40 hex characters |
| `config` | object | Flags and policy toggles in force |
| `model` | string | As in `submission.yaml` |
| `judge` | string | Judge model, or `none` for check-only tasks |
| `task_set` | string | `holdout`, `tuning`, `opus-subset` or `full` |
| `task` | string | Dev task id (allowed here: `docs/eval/` is not run-time code) |
| `outcome` | string | `done`, `error` or `timeout` |
| `score` | number | 0 to 1 |
| `input_tokens`, `output_tokens`, `cache_read_tokens` | integer | From the harness `usage` messages |
| `cost_usd` | number | Model cost for the task |
| `wall_sec` | number | Wall time |
| `note` | string | Anything a reader needs, else empty |

No number appears in docs or the writeup unless a row holds it.
