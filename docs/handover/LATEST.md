# Handover: 2026-11-16

- Phase: 0a complete, awaiting Hari's gate decision.
- Branch and HEAD: `phase-0a` at `f894158`, plus this handover commit. Not pushed, not merged.
- Session goal: Task 8 of `docs/superpowers/plans/2026-11-16-phase-0a.md`, the acceptance checks.

## What changed

- `73db2f2` docs: Phase 0a design spec and implementation plan.
- `291cac4` entry: kit `plan-verify` sample, `submission.yaml`, `LICENSE`, `NOTICE`.
- `3ac86ca` build: uv, ruff, mypy, pytest, `Makefile`, skeleton, fair-play scan.
- `91269da` build(hooks): `.claude/hooks/guard.py` with subprocess tests.
- `5f55bdb` build(hooks): `.claude/settings.json` registers the guard for four events.
- `c2a8d12` build(agents): nine build agents. `2600038` build(skills): five skills, templates.
- `ef46942` ci: `make check` on push and pull request. `56df1a4` build(hooks): final-review fixes.
- `334056f` test, `f894158` docs(notice): this session's review fixes (see below).

## Acceptance evidence (this session)

- Firewall, live: `failure-analyst` reading `~/.cache/plebench/tasks/none/tests/x.txt` got
  "File does not exist." (allowed). `harness-engineer` got "ple guard: grader firewall: only
  experiment-runner and failure-analyst may open grader files, task_cards, verifier output or
  the kit's runs/. Ask for failure classes instead." So the hook's `agent_type` is the agent name.
- Stop gate, live: after `make handover` with `tests-ran` older than the session start, ending
  the turn was blocked with "ple stop gate: this session changed files. Before ending: run
  `make check` until it passes." Only `make check` was named because `LATEST.md` was fresh.
  The second-stop rule was not run live (it would have ended the session); two subprocess
  tests cover it.
- ponytail-review: net -2 lines possible. Dropped one redundant assert; skipped a 1-line shrink
  in `guard.py`; kept the fair-play test's own `kit_dir`. It also surfaced a real bug, fixed in
  `334056f`: one Stop test failed whenever `PLE_STOP_GATE=off` was exported.
- fair-play-reviewer: SIGN-OFF at `334056f`, all ten items yes or not applicable yet (no harness
  code). Its non-blocking note on `NOTICE` (credit `submission.yaml` to the kit sample) is fixed
  in `f894158`; its other notes are in the gate decisions below.

## make check

Result: pass at `f894158`. 70 passed; ruff, format and mypy clean; `kit validate` printed
"ok: ple-harness, google-cloud/claude-opus-5-5 (Claude Opus 5.5); egress none".

## Ledger rows added

none.

## Decisions and ADRs

none. Phase 0a decisions are in `docs/superpowers/specs/2026-11-16-phase-0a-design.md`;
ADR-0001 is a Phase 1 item.

## Blockers (who must act)

- Hari: join the competition on Kaggle.
- Hari: open the x86 VM account with an SSH key and a spend limit.
- Hari: set up model access for `kit check`: a Google Cloud project for `kit/model_proxy`, or
  a capped Anthropic key in an env file outside the repo.
- Hari: create the private GitHub repository and install the `ple-submission` app.
- Hari: export `HF_TOKEN` or keep the cached `hf` login (already works).
- CI, including the kit clone from Actions, is unverified until the GitHub repository exists.

## Decisions for Hari at the Phase 0a gate

1. The tests half of the Stop gate is weak: the session protocol runs `make check` at start,
   so `tests-ran` is fresh before any edit. Option: require it newer than the newest change.
2. Must sessions start inside their worktree? That needs a `CLAUDE.md` line.
3. One handover file per workstream, or a lead-only `LATEST.md`? Decide before the worktrees.
4. Parked guard residuals: the glob `~/.cache/plebench/*` is not caught; Grep and Glob without
   a `path` (cwd) are unchecked; Monitor and terminal MCP tools are not matched; nothing prunes
   `.claude/state/session-*.json` (background Claude processes here wrote eight in 30 s).
5. From the fair-play review: accept dev-only `pathspec` (MPL-2.0, a mypy dependency, never
   shipped); whether the spec's decisions (no root `harness.py`, which `CLAUDE.md`'s layout still
   lists) need ADRs under "No ADR, no merge"; add `serve.py` and root modules to the fair-play
   scan once Phase 2 edits them; widen `.gitignore` beyond `*.env` (`.env.local`, `.envrc`).

## Next step

Hari decides the Phase 0a gate. On yes, run the plan's "After Hari accepts Phase 0a" commands
(fast-forward `main`, create the seven worktrees), then start Phase 0b.

## Deviations from the brief

- No root `harness.py` (2.1, 3.3): beside `harness/` it makes `import harness` ambiguous.
- The dataset has no `solution/` folders; the firewall targets `tests/` and `task_cards` (4.4).
- `lead` has no agent file (4.2): the lead is the main session and follows `CLAUDE.md`.
- `dev-run` and `replay` are deferred to Phase 0b and Phase 2, with the tools they wrap.
- Phase 0b needs model proxy access as well as the VM, because `kit check` requires it.
- Stop hook (4.4): a repeat stop needs only a fresh `LATEST.md`, which records the `make check`
  result, so a red suite cannot trap a finished session (spec 4.4 rule 5).
- `fair-play-reviewer` has WebFetch for the forum scan (spec 5). Build time only.
- The secrets rule follows the kit's `KEY_RE` (spec 4.1), so a token without a known prefix passes.
- The live firewall and Stop gate checks behaved as the plan expected.
