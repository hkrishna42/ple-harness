---
name: ple-kit-checks
description: Use when checking whether ple-harness is a valid entry - kit validate, make kit-check, kit artifacts, and switching model_api back before a submission candidate.
---

# Kit checks

The kit sits next to the main checkout; `make kit` clones it at the pinned `KIT_SHA`.

| Need | Command | Requires |
|---|---|---|
| `submission.yaml` is valid | `make check` (runs `kit validate`) | nothing |
| Full entry check | `make kit-check`, plus `ARGS="--cancel-test"` or `ARGS="--env-file <file outside the repo>"` | Docker; `MODEL_PROXY_URL` and `MODEL_PROXY_KEY`, or your own key for a local-only `model_api` |
| Artifacts review | `cd <kit> && uv run python -m kit artifacts <repo>` | a dev run |

Rules:

- Run `make kit-check` and every evaluation on the x86 VM, not the laptop. Timed graders
  score lower under emulation.
- For local runs on your own key, `model_api` may be `anthropic/claude-opus-5-5`. Before any
  submission candidate, set it back to `google-cloud/claude-opus-5-5` and rerun `make kit-check`.
- A commit is a submission candidate only when `make kit-check` ends with `ready to submit`.
- Kit logs are in `~/.cache/plebench/<name>/`.
