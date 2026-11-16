---
name: ple-fair-play-review
description: Use before merging any ple-harness change, and twice a week for the kit and forum scan - checks the change against the fair-play rules and ends with SIGN-OFF or BLOCK.
---

# Fair-play review

Input: a branch. Review `git diff main...<branch>`.

Answer each item yes or no, with evidence as `file:line`:

1. No dev-task id, title, folder name or file hash under `harness/`, `cost/`, `skills/`,
   `tools/`. `make check` runs `tests/unit/test_fair_play.py`; also read the diff.
2. No branch on a specific task. Skills and policies are chosen only by generic signals:
   file types and sizes, tool-catalog size, deliverable format, time left.
3. Run-time code never reads graders, reference files, `artifacts/` or `runs/`.
4. The entry calls only the model in `submission.yaml`; no provider-hosted tools (web search,
   web fetch, code execution); no other host.
5. Nothing key-like in the diff; env files stay outside the repository.
6. Load-bearing numbers in deliverables come from code with units checked, not model arithmetic.
7. Deliverables and the final message are normal professional prose.
8. New dependencies are Apache-2.0 compatible (Apache, MIT, BSD, ISC, PSF). Adapted MIT text
   is credited in `NOTICE`. No copyrighted code-table text (NEC, IBC and similar).
9. A behaviour change has ledger rows, and the claimed gain is in `docs/eval/ledger.jsonl`.
10. `make check` is green on the branch. For a submission candidate, `make kit-check` ends
    with `ready to submit` and `model_api` is `google-cloud/claude-opus-5-5`.

Verdict: `SIGN-OFF`, or `BLOCK` followed by numbered reasons. Do not fix anything.

## Twice-weekly scan

1. Kit: `git -C <kit> fetch --quiet && git -C <kit> log --oneline HEAD..origin/main`, then
   read any changed file under `docs/`, `kit/README.md` and `eval/README.md`.
2. Forum: read the competition's Kaggle discussion pages.
3. Report rule changes, and any answer to HANDOVER section 10 question 5, to the lead.
   Moving the kit pin is the lead's call.
