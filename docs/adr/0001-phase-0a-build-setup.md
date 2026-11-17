# ADR-0001: Phase 0a build setup and its deviations from the brief

- Status: accepted
- Date: 2026-11-16

## Context

Phase 0a built the repository skeleton, the guard hooks, the build agents and project skills
from `docs/superpowers/specs/2026-11-16-phase-0a-design.md`. A few choices differ from
`HANDOVER.md`. The fair-play review asked that they be recorded as an ADR under "No ADR, no
merge". Hari accepted Phase 0a on 2026-11-16.

## Decision

1. The entry's root files come from the kit's `plan-verify` sample (`serve.py`,
   `taskbridge.py`, `requirements.txt`, `LICENSE`, `submission.yaml` adapted).
2. No root `harness.py`. Next to the `harness/` package it makes `import harness`
   ambiguous, and `kit validate` does not require it.
3. The grader firewall targets `tests/` and `task_cards` in the task cache and the kit's
   `runs/`: the dataset has no `solution/` folders. Searches that start above those folders
   are blocked too.
4. The lead has no agent file. The lead is the main session and follows `CLAUDE.md`.
5. The secrets rule follows the kit's `KEY_RE` shape, so a token without a known prefix passes.
6. The Stop gate's repeat stop needs only a fresh handover, which records the `make check`
   result, so a failing check never traps a finished session.
7. `pathspec` (MPL-2.0) is accepted as a dev-only dependency: mypy pulls it in, and it is
   never part of the entry.
8. `fair-play-reviewer` has WebFetch for the forum scan, and no edit tools.

## Alternatives considered

- A root `harness.py` shim that re-exports `harness/`: rejected, it adds a file for no check
  that needs it.
- Gating `solution/` folders as the brief says: there are none in the dataset.

## Consequences

`CLAUDE.md`'s layout drops `harness.py`. The fair-play scan covers `harness/`, `cost/`,
`skills/` and `tools/`; `serve.py` and other root modules join it once Phase 2 edits them.

## Evidence

none: build-time decisions, taken before any evaluation run.
