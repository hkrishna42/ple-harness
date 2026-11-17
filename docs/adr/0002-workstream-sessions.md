# ADR-0002: Workstream sessions, handovers and skills

- Status: accepted
- Date: 2026-11-16

## Context

After the Phase 0a gate, work splits into seven worktrees on `ws/<name>` branches. Three
gaps remained from the Phase 0a review: the Stop gate's tests check was satisfied by the
`make check` that the session protocol runs at start; the hooks judge the folder a session
starts in; and seven branches writing one `LATEST.md` would conflict on every merge. Hari also
asked that skills such as ponytail be actively used, and that every decision be tracked.

## Decision

1. The Stop gate needs `.claude/state/tests-ran` to be newer than the newest file changed
   since the session's start commit (handover files excluded), so `make check` must run after
   the last edit.
2. Each workstream session opens in its worktree folder (`.worktrees/<name>`), never in the
   main checkout. The main checkout is the lead's, for merges into `main`.
3. Each workstream writes its own handover, `docs/handover/<name>.md`, on `ws/<name>`. The
   lead writes `docs/handover/LATEST.md` on `main`. `make handover` and the Stop gate pick the
   file from the branch name.
4. Builder agents preload `ponytail:ponytail` and `superpowers:test-driven-development`;
   every agent preloads the `ple-*` skills its text names, and has the Skill tool as a fallback.
   A config test enforces both. The ponytail plugin also injects ponytail into every subagent.
   The lead runs `ponytail:ponytail-review` on every merge and records it in the handover.
5. Every decision gets one line in `docs/decisions.md`, with who decided and why.
   `.gitattributes` merges that file with `merge=union`, so lines from two branches both stay.

## Alternatives considered

- One `LATEST.md` written by every workstream: conflicts on every merge.
- A tests marker per edited file: more state for the same guarantee.
- Numbered decision IDs: two branches would take the same number.

## Consequences

A session that edits after `make check` must run it again before it can stop. Deleting a file
carries no mtime, so a deletion alone does not make the tests marker stale. GitHub's web merge
ignores `merge=union`; the lead merges locally.

## Evidence

none: build-time decisions, taken before any evaluation run.
