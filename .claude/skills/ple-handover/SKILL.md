---
name: ple-handover
description: Use at the end of every ple-harness session that changed files, before stopping - writes docs/handover/LATEST.md so the next session can start cold.
---

# Writing the handover

1. Run `make check`. Record the result honestly: pass, or the step that failed.
2. Run `make handover`. It copies `docs/handover/TEMPLATE.md` over `docs/handover/LATEST.md`
   (git keeps earlier handovers).
3. Fill every field. Write "none" rather than deleting a field. Keep it under 60 lines.
4. Name commits by short SHA and files by path. Ledger claims cite run IDs.
5. Anything that now differs from HANDOVER.md goes under "Deviations from the brief", with the reason.
6. Commit it with the work: `docs(handover): <one-line summary>`.

The Stop hook blocks the end of a session that changed files until both
`.claude/state/tests-ran` (written by a passing `make check`) and `docs/handover/LATEST.md`
are newer than the session start. `PLE_STOP_GATE=off` is Hari's escape hatch, not yours.
