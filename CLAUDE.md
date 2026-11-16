# CLAUDE.md — ple-harness

This repo is `ple-harness`: an open-source agent harness for the Kaggle competition
"Google - Agent Harness on Physical-Engineering's Last Exam" (PLE), plus its cost layer
and run-time skills. Full brief: `HANDOVER.md`. Deadline: 2027-01-05 23:59 UTC; we submit
on 2027-01-03.

## Bootstrap (only until Phase 0a is accepted)
The folder may hold nothing but `HANDOVER.md` and this file. If `docs/handover/LATEST.md`,
the `Makefile` or the hooks are missing, follow `HANDOVER.md` section 0.1 instead of the
session protocol below, skip any step whose file does not exist, and say what you skipped.

## Session protocol (every session once Phase 0a is accepted)
1. Read `docs/handover/LATEST.md`. Then `git log --oneline -20`. Then `make check`.
2. Work in the worktree for your workstream (`git worktree list`). Never on `main`, apart
   from the single bootstrap commit.
3. Before ending: run tests, write a handover (skill `ple-handover`), update
   `docs/handover/LATEST.md`. The Stop hook enforces this.

## Hard rules
- **Fair play.** No task IDs, titles, folder names or file hashes under `harness/`,
  `cost/`, `skills/` or `tools/`. No hard-coded answers. Skills and policies are chosen
  only by generic signals. The harness never reads graders, reference files, `artifacts/`
  or `runs/`.
- **Grader firewall.** Only `experiment-runner` and `failure-analyst` open grader or
  reference files. Builders get failure classes, never expected values.
- **One model, no outside help.** Only the model in `submission.yaml`. No provider-hosted
  tools. No secrets in the repo.
- **The model picks the tool; code owns the number.** Compute load-bearing numbers with
  scripts or tools in the task container, with units checked.
- **Never end without a gradable deliverable.** Draft early at the required path; always
  send `done` with a clear final message; handle `cancel`.
- **Deliverables are normal prose.** Terse style only in narration between tool calls.
- **Only a measured gain gets merged.** No number in docs or the writeup unless
  `docs/eval/ledger.jsonl` holds it with a run ID.
- **Cost never buys a score loss.** Lossless policies first; lossy ones behind a toggle.
- **Budget gates.** State the estimated cost before every paid run. No spend above a
  budget line without Hari's approval.
- **Licence.** Apache-2.0. Credit adapted MIT text in `NOTICE`. No copyrighted code-table
  text in the repo.

## Workflow
- `superpowers:brainstorm` → `superpowers:write-plan` → `superpowers:execute-plan`.
  Write the failing test first.
- `ponytail` level `full` in `harness/` and `cost/`; level `lite` in `tools/`.
  `ponytail:ponytail-review` on every merge.
- Delegate to the agents in `.claude/agents/`; keep the main context clean.
  `fair-play-reviewer` signs off before any merge.
- Any architectural choice → ADR in `docs/adr/`. No ADR, no merge.
- superpowers and ponytail are build-time tools. Neither is installed in the entry.

## Layout
```
submission.yaml serve.py harness.py   the entry's required root files
harness/     protocol, agent loop, phases, deadlines, final message
cost/        engine/ policies/ bench/
skills/      run-time playbooks: core/ mechanical/ electrical/ civil-structural/ style/
tools/       deterministic domain tools
tests/       unit/ protocol/ replay/
artifacts/   dev-set outputs exported by the kit; never edit by hand
docs/        adr/ handover/ eval/ writeup/
.claude/     build-time only: agents/ skills/ hooks
runs/        git-ignored saved runs for the replay bench
```

## Commands (Phase 0 creates these)
- `make check` — lint, types, unit and protocol tests; writes the tests-ran marker
- `make kit-check` — the kit's `python -m kit check` against this repo
- `make dev-run TASKS=<set> MODEL=<model>` — the kit's `eval/run.py` on a task set, then ledger rows
- `make replay` — the cost and verifier replay bench over `runs/`
- `make handover` — scaffold a handover file from the template

The kit lives next to this repo, never inside it: <https://github.com/google-research/ple>.

## Style
- Python 3.12, type hints everywhere, `ruff` and `mypy --strict` on `harness/` and `cost/`.
- Tools: explicit, boring, with the formula's source in a comment. Cleverness is a defect there.
- Run-time skills: short, one job each, a one-line description that says when to load it.
- Commit messages: `area: what` (for example `cost(engine): add cache breakpoints with tests`).
- Commits and PRs are Hari's: no `Co-Authored-By` trailer, no "Generated with" line. Older plans
  that ask for one are superseded; `.claude/settings.json` turns Claude Code's attribution off.
