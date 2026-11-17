# Decision log

One line per decision, newest last: date, who decided, the decision, why, and where it lives.
Every session adds its decisions the same day. Architectural ones also get an ADR in
`docs/adr/`. Lines only; no numbering, so branches merge cleanly (`merge=union` in
`.gitattributes`).

- 2026-11-16 · Hari · Seed the entry's root files from the kit's `plan-verify` sample. Why: the smallest entry the kit already validates. Ref: ADR-0001.
- 2026-11-16 · Hari · No root `harness.py`. Why: beside `harness/` it makes `import harness` ambiguous; `kit validate` does not need it. Ref: ADR-0001.
- 2026-11-16 · Hari · Git identity is the Gmail address, set in the repo's local config. Ref: bootstrap commit `9e5f3ea`.
- 2026-11-16 · Hari · Approve the Phase 0a design and run it subagent-driven. Ref: `docs/superpowers/specs/2026-11-16-phase-0a-design.md`.
- 2026-11-16 · Claude (ruling) · The grader firewall targets `tests/`, `task_cards` and the kit's `runs/`, including searches from above them. Why: the dataset has no `solution/` folders. Ref: ADR-0001.
- 2026-11-16 · Claude (ruling) · The lead has no agent file; the lead is the main session. Ref: ADR-0001.
- 2026-11-16 · Claude (ruling) · The secrets rule follows the kit's `KEY_RE` shape. Ref: ADR-0001.
- 2026-11-16 · Claude (ruling) · The Stop gate fingerprints the working tree, and a repeat stop needs only a fresh handover. Why: catch edits to already-dirty files; never trap a finished session. Ref: ADR-0001, spec 4.4.
- 2026-11-16 · Claude (ruling) · Park the remaining guard gaps (cache-root glob, Grep/Glob without a path, Monitor and terminal tools, no pruning of session records) for a Phase 2 guard pass. Ref: `docs/handover/LATEST.md`.
- 2026-11-16 · Hari · Accept Phase 0a and fast-forward `main`. Ref: `b2d6ef5`.
- 2026-11-16 · Hari · The GitHub repository is public from the start, so the `ple-submission` app is not needed. Ref: <https://github.com/hkrishna42/ple-harness>.
- 2026-11-16 · Hari · No Claude attribution on commits or pull requests. Ref: `67096f2`.
- 2026-11-16 · Hari · Dev runs use an existing Anthropic key, kept in `~/.config/ple-harness/dev.env` (owner-only, outside the repo). Ref: brief section 2.5.
- 2026-11-16 · Hari · Run VM on vast.ai through the existing `vastai` login (VM template, as the brief's budget table says). Ref: `HANDOVER.md` section 6.
- 2026-11-16 · Hari · The Stop gate needs `make check` after the last edit, not just after the session start. Ref: ADR-0002.
- 2026-11-16 · Hari · Each workstream session opens in its own worktree folder. Ref: ADR-0002, `CLAUDE.md`.
- 2026-11-16 · Hari · One handover file per workstream; the lead keeps `LATEST.md`. Ref: ADR-0002.
- 2026-11-16 · Hari · Skills such as ponytail must be actively used: builder agents preload ponytail and test-driven development, enforced by a config test; ponytail-review on every merge. Ref: ADR-0002.
- 2026-11-16 · Hari · Keep this decision log. Ref: ADR-0002.
- 2026-11-16 · Claude, unopposed · Accept `pathspec` (MPL-2.0) as a dev-only dependency. Ref: ADR-0001.
- 2026-11-16 · Claude, unopposed · Ignore every `.env*` file; move CI to `actions/checkout@v7` and `astral-sh/setup-uv@v10.3.3` (Node 24; setup-uv has no `v10` tag). Why: CI's Node 20 deprecation warning; the fair-play review.
- 2026-11-16 · Claude (ruling) · The Stop gate's last-edit check skips `docs/decisions.md` as well as handovers. Why: logging decisions after `make check` must not force a rerun (fair-play review).
