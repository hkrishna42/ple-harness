# Handover: 2026-11-16

- Phase: 0a accepted. Gate decisions 1-3 settled (ADR-0002); the seven workstream worktrees
  exist. Phase 0b is next. Hari has joined the competition on Kaggle.
- Branch and HEAD: `main` at this commit, pushed to `origin/main`. Worktrees:
  `.worktrees/<name>` on `ws/<name>` for harness, cost, domain-mech, domain-elec,
  domain-civil-struct, eval and writeup, each fast-forwarded to this commit.
- Session goal: settle the gate decisions, make skills such as ponytail actively used, start the
  decision log, create the worktrees.

## What changed

- `6897e33` build(hooks): the Stop gate needs `make check` after the last edit (handovers and
  `docs/decisions.md` excluded) and the branch's handover: `docs/handover/<name>.md` on
  `ws/<name>`, `LATEST.md` on `main`. `make handover` picks the same file.
- `3cc6122` build(agents): builders preload `ponytail:ponytail` and
  `superpowers:test-driven-development`; every agent preloads the `ple-*` skills its text names
  and has the Skill tool as a fallback. `tests/unit/test_claude_config.py` enforces it.
- `48bbc58` ci: `actions/checkout@v7` and setup-uv on Node 24 (pinned to `v10.3.3` in `2c795cd`).
- `19c4998` docs: `docs/decisions.md`, ADR-0001 (Phase 0a deviations), ADR-0002 (workstream
  sessions), `CLAUDE.md` session protocol and layout, `merge=union` for the log.
- `42592c9` build(hooks): ponytail-review shrinks.
- `2c795cd` fix: setup-uv pinned to `v10.3.3`, `.env*` ignored, the decision log skipped by the
  last-edit check; the log names only the key's path.
- test(guard), after the push: CI on `144d1e8` failed three new Stop tests. Linux gives two
  writes in one clock tick the same mtime, so "edit, then `make check`" could tie. The tests
  now set the marker's time explicitly; the gate itself is unchanged.

## make check

Result: pass at this commit. 75 passed; ruff, format and mypy clean; `kit validate` ok. CI: the
run on `144d1e8` failed as above (new actions themselves fine, no Node 20 warning); check the
run on this commit.

## Ledger rows added

none.

## Decisions and ADRs

`docs/decisions.md` now holds 22 lines: Phase 0a backfilled, plus today's. ADR-0001, ADR-0002.

## Reviews

- ponytail-review of `main..gate-decisions`: net -2 lines possible; both shrinks applied in
  `42592c9`; skipped swapping the extracted `git_out` back to a `functools.partial`.
- fair-play-reviewer: SIGN-OFF at `2c795cd` (checklist 1-10 pass; the first review blocked on
  `setup-uv@v10`, which has no such tag, fixed in `2c795cd`).

## Not verified

- Skill preloads in subagents. This session could not reload agent definitions. A probe saw
  ponytail in a subagent (the ponytail plugin injects it into every subagent at start) but not
  the newly listed preloads. First workstream session: ask a builder agent, with no tools,
  which skill texts are in its context. If preloads are missing, the fallback line makes the
  agent load them with the Skill tool; report it here.

## Blockers (who must act)

- Hari: confirm the spend cap on the dev-run Anthropic key.
- Hari: vast.ai credit is $12.60; the brief's VM line is $100. Top up before Phase 0b runs.

## Next step

Phase 0b in `.worktrees/eval` (experiment-runner): start a vast.ai VM template, set
`model_api: anthropic/claude-opus-5-5` on that branch for dev runs, and run
`make kit-check ARGS="--env-file ~/.config/ple-harness/dev.env"`. State the estimated cost first.

## Deviations from the brief

- Phase 0a's deviations are now ADR-0001. New: per-workstream handovers and the stricter tests
  check (ADR-0002). Dev runs use an Anthropic key instead of the Google Cloud proxy (brief 2.5
  allows it; switch `model_api` back before any submission candidate).
- Parked guard gaps and the `serve.py` fair-play scan stay open for Phase 2 (`docs/decisions.md`).
