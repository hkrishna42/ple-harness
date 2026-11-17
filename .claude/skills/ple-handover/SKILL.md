---
name: ple-handover
description: Use at the end of every ple-harness session that changed files, before stopping - writes the branch's handover (docs/handover/<workstream>.md, or LATEST.md on main) so the next session can start cold.
---

# Writing the handover

1. Run `make check` after your last edit. Record the result honestly: pass, or the step
   that failed.
2. Run `make handover`. It copies `docs/handover/TEMPLATE.md` over your branch's handover:
   `docs/handover/<name>.md` on `ws/<name>`, `docs/handover/LATEST.md` on `main` (git keeps
   earlier handovers).
3. Fill every field. Write "none" rather than deleting a field. Keep it under 60 lines.
4. Name commits by short SHA and files by path. Ledger claims cite run IDs.
5. Anything that now differs from HANDOVER.md goes under "Deviations from the brief", with the reason.
   Every decision this session made is a line in `docs/decisions.md`; the handover lists them.
6. Commit it with the work: `docs(handover): <one-line summary>`.

The Stop hook blocks the end of a session that changed files until
`.claude/state/tests-ran` (written by a passing `make check`) is newer than your last edit and
your branch's handover is newer than the session start (ADR-0002). `PLE_STOP_GATE=off` is Hari's escape hatch, not yours.
