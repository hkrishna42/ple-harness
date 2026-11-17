# Phase 0a design: bootstrap the build harness

Status: approved by Hari on 2026-11-16. Scope: HANDOVER.md section 7, Phase 0a only.
No harness code is written in this phase.

## Goal

Turn the bootstrap commit into a repository that agents can work in safely:
skeleton, licences, tooling, CI, guard hooks, agents, project skills, a fair-play
scan, and the kit cloned next to the repository.

Phase 0a is accepted when:

1. `make check` passes on the laptop.
2. `docs/handover/LATEST.md` exists.
3. The Stop hook blocks a session that changed files without a fresh handover, and
   allows one that wrote it. Proven by subprocess tests and one live session end.

## Decisions taken during brainstorming

| Question | Decision | Why |
|---|---|---|
| Seed for the root files | Kit sample `plan-verify` | Defaults to `google-cloud/claude-opus-5-5`; planner, worker and verifier roles with time shares already resemble HANDOVER 3.1 |
| Root `harness.py` | Not created | The kit requires only `submission.yaml`, the file `serve` runs, and `artifacts/`. A root `harness.py` beside the `harness/` package makes `import harness` ambiguous |
| Git identity | Repo-local, `Harikrishnan Girikumar <harikrishnangirikumar@gmail.com>` | Hari's choice; the bootstrap commit was re-authored to match |
| Grader firewall mechanism | One stdlib Python hook keyed on the hook input's `agent_type` | Claude Code passes `agent_id` and `agent_type` to hooks for subagent tool calls, so the brief's session-wide analyst flag is not needed |

Rejected firewall options: native `permissions.deny` rules (cannot exempt the two
analyst agents; miss `grep -r` and scripts that open files themselves) and shell
plus `jq` hooks (the pattern that failed closed twice in complychip-ED; hard to test).

## Facts from the kit (checked 2026-11-15, kit commit `8320f0402fdca9f42476607f72bcfd5271cd50c9`)

- `kit check` stops at its second stage without `MODEL_PROXY_URL` and
  `MODEL_PROXY_KEY` (or a local model key). Phase 0b therefore needs model access as
  well as the VM. `kit validate` needs neither Docker nor a model.
- The `files` stage of `kit check` rejects any file that looks like an API key. Test
  fixtures must build fake keys at run time.
- Dev tasks download to `~/.cache/plebench/tasks/<commit>/`. In the dataset, grader
  files live in `tasks/<id>/tests/`; there is no `solution/` folder. The dataset root
  also holds `task_cards.jsonl` and `task_cards.parquet`.
- `eval/run.py` writes run output to `runs/<name>-<time>/` under the kit clone.
- The build stages tracked files plus untracked files that git does not ignore.

## 1. Branches, worktrees and the kit clone

- Phase 0a is built on branch `phase-0a`. The spec and plan are committed there.
- When Hari accepts Phase 0a, `phase-0a` fast-forwards into `main`.
- After that merge, seven worktrees are created under `.worktrees/<name>` (git-ignored)
  on branches `ws/<name>`: `harness`, `cost`, `domain-mech`, `domain-elec`,
  `domain-civil-struct`, `eval`, `writeup`. Creating them is the first step after
  acceptance, not part of Phase 0a.
- The kit is cloned to `/Users/hari/Desktop/ple` (a sibling of the main checkout),
  pinned at `KIT_SHA = 8320f0402fdca9f42476607f72bcfd5271cd50c9`. The Makefile
  finds it from the git common directory, so the same path works from every worktree.
  Moving the pin is a deliberate change with a handover note.

## 2. Entry files and skeleton

Copied unchanged from `sample_submissions/plan-verify/` at `KIT_SHA`:
`serve.py`, `taskbridge.py`, `requirements.txt`. Google's licence headers stay.

`submission.yaml`:

```yaml
name: ple-harness
model_api: google-cloud/claude-opus-5-5
install: >-
  uv venv --python 3.12 /opt/harness/venv
  && uv pip install --python /opt/harness/venv/bin/python -r {src}/requirements.txt
serve: /opt/harness/venv/bin/python {src}/serve.py
```

`serve.py` and `taskbridge.py` are vendored sample code. Ruff and mypy skip them,
with a `ponytail:` comment in `pyproject.toml` naming the exit: Phase 2 moves the loop
into `harness/` and keeps only a thin `serve.py`.

Skeleton (HANDOVER 3.3):

- `harness/__init__.py`, `cost/__init__.py`: empty packages, so mypy and pytest have
  targets. Subpackages (`cost/engine` and the rest) arrive with their first code.
- `.gitkeep` in `skills/{core,mechanical,electrical,civil-structural,style}/`,
  `tools/`, `tests/{protocol,replay}/`, `docs/{adr,eval,writeup}/`.
- `tests/unit/` holds this phase's tests.
- `tools/CLAUDE.md`: one paragraph setting ponytail to `lite` there, with explicit
  formulas and their sources.
- `artifacts/` is not created; `eval/run.py` makes it.

`LICENSE`: the Apache-2.0 text copied from the kit. `NOTICE`: copyright line for
ple-harness, then credits for the PLE kit samples (Apache-2.0, Google LLC) and for
text adapted from superpowers and ponytail (MIT).

`.gitignore`: the sample's entries (`*.env`, `.venv/`, `__pycache__/`, `*.pyc`,
`runs/`) plus `.worktrees/`, `.claude/state/`, `.claude/settings.local.json`,
`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`.

## 3. Tooling

`pyproject.toml`: project `ple-harness`, `requires-python = ">=3.12,<3.13"`, no
runtime dependencies (those stay in `requirements.txt`, which the build installs),
dependency group `dev` = ruff, mypy, pytest, pyyaml, plus `types-PyYAML`. `uv.lock` is
committed. Ruff: line length 100, target py312, excludes `serve.py` and
`taskbridge.py`. Mypy: strict, Python 3.12.

Makefile targets:

| Target | Does |
|---|---|
| `check` | `ruff check`, `ruff format --check`, `mypy --strict harness cost .claude/hooks`, `pytest`, `kit validate`; on success writes `.claude/state/tests-ran` |
| `kit` | Clones the kit to the sibling path at `KIT_SHA` if missing |
| `kit-check` | Runs the kit's `kit check` against this repository |
| `handover` | Copies `docs/handover/TEMPLATE.md` to `docs/handover/LATEST.md` |

`dev-run` arrives in Phase 0b with the ledger script; `replay` arrives in Phase 2 with
the bench. `CLAUDE.md` lists both; each lands with the tool it wraps.

CI: `.github/workflows/check.yml` on push and pull request, Ubuntu, `setup-uv`,
`make kit`, `make check`. It goes live when Hari creates the GitHub repository.

## 4. Guard hooks

One file, `.claude/hooks/guard.py`, stdlib only, run as
`uv run --no-project --quiet --python 3.12 python "$CLAUDE_PROJECT_DIR/.claude/hooks/guard.py" <event>`
(about 0.2 s per call, measured). It reads the hook JSON on stdin.

`.claude/settings.json` registers:

| Event | Matcher | Argument |
|---|---|---|
| `PreToolUse` | `Read\|Write\|Edit\|MultiEdit\|NotebookEdit\|Grep\|Glob\|Bash` | `pre` |
| `PostToolUse` | `Write\|Edit\|MultiEdit` | `post` |
| `SessionStart` | (all) | `start` |
| `Stop` | (all) | `stop` |

### 4.1 PreToolUse rules

The hook gathers the text it inspects from `tool_input`: `file_path`, `path`,
`notebook_path`, `pattern`, `glob` and `command`. For the secret rule it also reads
`content`, `new_string`, `new_source` and each `edits[].new_string`. A rule match returns
`permissionDecision: "deny"` with a reason that names the rule.

1. **Grader firewall.** Applies unless `agent_type` is `experiment-runner` or
   `failure-analyst`, so the main session is covered too. It denies text that matches:
   - any task-cache path (`.cache/plebench/tasks...`) except files under a task's
     `environment/` folder and its `instruction.md`. A path naming `/tests` or
     `task_cards` is always denied. The cache root and task roots are denied because
     a recursive read from there reaches `tests/`;
   - `runs/` followed by `verifier`;
   - `ple/runs/` (the kit clone's run output);
   - the bare cache root (`.cache/plebench` or `.cache/plebench/` at the end of a path
     token). Other plebench subfolders, such as the kit's `~/.cache/plebench/<name>/`
     logs, stay readable.

   For Grep and Glob it also resolves the `path` input (expanding `~`, relative to the
   project root) and denies it when it equals or sits above the task cache
   (`~/.cache/plebench/tasks`) or the kit's `runs/`. The kit is `$PLE_KIT_DIR`, else
   `ple` beside the main checkout (the Makefile's rule, falling back to
   `<project root>/../ple`). Accepted residual risk: Bash commands that `cd` into the
   kit and use relative paths, or recurse from `~/.cache`.

   It never matches this repository's own `tests/`. It is a guardrail for honest
   agents, not a sandbox (`ponytail:` comment: a Docker or OS sandbox is the upgrade).
2. **Artifacts.** Denies Write, Edit, MultiEdit and NotebookEdit under
   an `artifacts/` folder whose parent holds a `submission.yaml` (so worktrees are
   covered). Also denies Bash commands that mention `artifacts/` and
   contain a write verb (`>`, `tee`, `rm`, `mv`, `cp`, `sed -i`, `touch`, `mkdir`),
   unless the command runs `eval/run.py` or `kit artifacts`.
3. **Force push.** Denies `git push` with `--force`, `--force-with-lease`, a short
   flag cluster containing `f`, or a `+ref` refspec.
4. **Secrets.** Denies text shaped like the kit's `KEY_RE`: a prefix (`sk-`, `sk-ant-`,
   `sk-proj-`, `AIza`, `gh[pousr]_`, `github_pat_`, `hf_`, `xox[baprs]-`) followed by 20 or
   more key characters that mix upper case, lower case and digits; a PEM private-key
   header; or `AKIA` plus 16 uppercase alphanumerics.
5. **Errors.** An exception inside the PreToolUse handler denies the call, with the
   exception text in the reason. A guard bug shows up immediately rather than
   letting a call through silently.

### 4.2 PostToolUse

For a touched `.py` file inside the repository, other than `serve.py` and
`taskbridge.py`, runs `uv run --frozen ruff format <file>`. It never blocks and
ignores formatter failures.

### 4.3 SessionStart

On `source` `startup`, `resume` or `clear`, it writes
`.claude/state/session-<session_id>.json` with the start time, `HEAD`, and a SHA-256
fingerprint of the working tree (`git status --porcelain -uall`, `git diff HEAD --binary`
and the bytes of each untracked file). On `compact` it keeps the existing file, so the gate's
start time survives compaction. It prints nothing.

### 4.4 Stop gate

Checks run in this order:

1. If `PLE_STOP_GATE=off` is set, the session may stop.
2. If no session file exists, the session may stop, with a warning on stderr.
3. If `HEAD` and the fingerprint both equal their start values, the session changed
   nothing and may stop.
4. Otherwise it needs `.claude/state/tests-ran` (written by `make check` on success) to be
   newer than both the start time and the newest file changed since the start commit
   (handover files excluded), and the branch's handover to be newer than the start time:
   `docs/handover/<name>.md` on `ws/<name>`, `docs/handover/LATEST.md` elsewhere. If
   either is missing or stale, the hook returns `{"decision": "block", "reason": ...}`
   naming what to do. (Amended by ADR-0002 after the Phase 0a gate.)
5. When the Stop payload has `stop_hook_active: true` (the agent was already blocked
   once), only a fresh handover is required. If it is fresh but `tests-ran` is stale,
   the session may stop, with a warning on stderr naming the stale marker; a stale
   handover still blocks. The handover must record the `make check` result, so a
   failing check never traps the session.
6. An exception anywhere in the Stop handler lets the session stop, with a warning on
   stderr. A gate bug must never trap a finished session.

Subagents trigger `SubagentStop`, which is not registered, so subagents are not gated.

## 5. Agents and project skills

Nine files in `.claude/agents/`, one per row of HANDOVER 4.2 except `lead`. The lead
is the main session and follows `CLAUDE.md`. Each file has frontmatter (`name`,
`description` saying when to delegate, `tools`) and a body with: job, inputs, must-not
list, outputs, and a closing duty (report back in failure classes, never expected
values, for builder-facing output).

| Agent | Tools |
|---|---|
| `harness-engineer`, `verifier-engineer`, `domain-mechanical`, `domain-electrical`, `domain-civil-structural` | Read, Grep, Glob, Edit, Write, Bash |
| `experiment-runner` | Read, Grep, Glob, Edit, Write, Bash (writes ledger rows; must not change harness code) |
| `failure-analyst` | Read, Grep, Glob, Write, Bash (writes failure classes to `docs/eval/failure-classes.md`) |
| `fair-play-reviewer` | Read, Grep, Glob, Bash, WebFetch (WebFetch for the forum scan; no edit tools) |
| `writeup-author` | Read, Grep, Glob, Edit, Write, Bash |

Five skills in `.claude/skills/<name>/SKILL.md`:

- `ple-handover`: when to write one; fields of `docs/handover/TEMPLATE.md`; write
  `LATEST.md`; record deviations from the brief.
- `ple-experiment-ledger`: the row schema from HANDOVER 5.6; announce the estimated
  cost before every paid run; budget lines from section 6; no number in docs without
  a row.
- `ple-fair-play-review`: the section 1 checklist, `make check` (which runs the
  scan), a licence check of new dependencies, a sign-off or block verdict.
- `ple-kit-checks`: `kit validate`, `make kit-check`, `kit artifacts`; switch
  `model_api` back to `google-cloud/claude-opus-5-5` before any submission candidate.
- `ple-runtime-skill-authoring`: format of a run-time skill (name, one-line
  description, body); generic signals only; it must pay for itself on the replay
  bench; credit adapted MIT text in `NOTICE`.

Templates: `docs/handover/TEMPLATE.md` (date, phase, what changed, `make check`
result, ledger rows added, decisions and ADRs, blockers, next step, deviations from
the brief) and `docs/adr/0000-template.md` (context, decision, alternatives,
consequences, evidence as ledger run IDs).

## 6. Fair-play scan

`tests/unit/test_fair_play.py` contains a `find_leaks(roots, needles)` function and
two tests:

- **Planted needle:** a needle written into a `tmp_path` file is found. This proves
  the scanner works.
- **Real scan:** load the kit's `eval/dev_set.yaml` and build needles from every task's
  `id`, its `title` (matched case-insensitively), its `sha256` (if present), each full
  file deliverable path (directory deliverables such as `/app/output/` are generic and
  skipped), and each directory component of a deliverable path that is at least
  12 characters long (so `app`, `files` and `output` are not needles, and neither are
  final file names such as `solution.py`). Then assert that `harness/`, `cost/`,
  `skills/` and `tools/` contain none of them.

A missing kit clone fails the test with "run `make kit`"; it never skips. The
repository never contains the needles, because they are read at run time.

## 7. Tests for Phase 0a

`tests/unit/test_guard.py` runs `guard.py` as a subprocess with crafted JSON:

- Firewall: denies a builder (no `agent_type`, and `harness-engineer`) for each blocked
  pattern, including Grep and `grep -r` on a task root; allows `experiment-runner` and
  `failure-analyst`; allows a task's `instruction.md` and `environment/` files and this
  repository's `tests/unit/x.py`.
- Artifacts: denies Write under `artifacts/` and `echo x > artifacts/a`; allows
  `uv run python eval/run.py ...`.
- Force push: denies `git push --force`, `git push -f origin x`, `git push origin +main`;
  allows `git push origin phase-0a`.
- Secrets: denies a Write whose content holds a key assembled at run time; allows
  ordinary text.
- Error path: malformed stdin to `pre` denies; malformed stdin to `stop` allows.
- Stop gate, with a temporary git repository as the project directory: an unchanged
  session may stop; a changed session with a stale handover is blocked; a changed
  session with fresh `tests-ran` and `LATEST.md` may stop; `compact` keeps the start
  time; `PLE_STOP_GATE=off` allows.

## 8. Deviations from HANDOVER.md, recorded in the first LATEST.md

- No root `harness.py` (section 2.1 and the 3.3 layout).
- No `solution/` folders exist in the dataset; the firewall targets `tests/` and
  `task_cards` (section 4.4).
- `lead` has no agent file (section 4.2).
- `dev-run` and `replay` targets are deferred to Phase 0b and Phase 2.
- Phase 0b needs model proxy access as well as the VM, because `kit check` requires it.

## Out of scope

Harness code, the ledger script, `dev-run`, the replay bench, the VM, any paid run,
the GitHub repository, and creating the seven worktrees (done right after acceptance).
