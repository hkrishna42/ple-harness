# ple-harness — Master Build Brief (Claude Code Handover)

**Read this file first. Then read `CLAUDE.md`, then `docs/handover/LATEST.md` if it exists.**
**Do not write harness code until Phase 0a is complete and its acceptance criteria pass.**
**Starting in an empty folder? Section 0.1 comes first.**

Owner: Hari, entering as an individual. Date issued: 2026-11-15.
Hard deadline: 2027-01-05 23:59 UTC (18:59 US Eastern). Internal submit date: 2027-01-03.

---

## 0. What we are building, in one paragraph

`ple-harness` is an open-source autonomous agent harness for the Kaggle competition
**"Google - Agent Harness on Physical-Engineering's Last Exam" (PLE)**. A harness is a
WebSocket server that drives one model through an isolated task container (shell, files,
local MCP tools, no internet, up to 6 hours) and leaves graded engineering deliverables:
calculation packages, review memos, schedules, IFC models, scripts. We submit on
**Claude Opus 5.5** (`google-cloud/claude-opus-5-5`). The same repository also holds a
**cost layer** (engine, policies, replay bench) and **run-time skills** (short playbooks
the model loads during a task). Goals, in order: (1) a valid entry that reaches Stage 2,
(2) the highest Stage 2 mean score we can reach, (3) the lowest cost per task at that
score. After the competition this repository becomes the agent engine for complychip-ED.
That integration is out of scope until 2027-01-06.

## 0.1 Fresh-folder start (run this before anything else)

This brief is written to work in an empty folder that holds only `HANDOVER.md` and
`CLAUDE.md`. Nothing else it mentions exists yet: the Makefile, the hooks, the agents,
`docs/handover/LATEST.md` and the worktrees are all created in Phase 0a. Until then, skip
any step that depends on a missing file and say that you skipped it.

1. **Git.** If the folder is not a git repository, run `git init -b main`. Commit
   `HANDOVER.md` and `CLAUDE.md` as the first commit on `main`. That bootstrap commit is
   the only work allowed directly on `main`; worktrees start after it.
2. **Tools.** Report the versions of `git`, `uv`, Python 3.12, Node and Docker. Report
   anything missing. Do not install system software without asking.
3. **Plugins.** Confirm the superpowers and ponytail commands are available. If they are
   not, stop and ask Hari to send the four install lines in section 4.1. An agent cannot
   run `/plugin` commands itself.
4. **Access.** Report each of these as ready or missing: competition joined on Kaggle,
   dataset terms accepted and `HF_TOKEN` set in the environment, the run VM reachable over
   SSH, a model key set in the environment. Never ask for a secret to be pasted into the
   chat or written to a file in the repository.
5. **Missing access does not block the start.** Phase 0a needs no account. Phase 0b and
   every evaluation run wait for Hari's steps in section 9.
6. **Report, then plan.** Finish this preflight with a short ready/missing table before
   brainstorming Phase 0.

## 1. Non-negotiables (violating any of these is a bug, not a trade-off)

1. **Fair play.** The harness never hard-codes answers and never detects a specific task
   to branch on it: no task IDs, titles, folder names or file hashes anywhere under
   `harness/`, `cost/`, `skills/` or `tools/`. Skills and policies are selected only by
   generic signals (file types and sizes, tool-catalog size, deliverable format, time
   left). The harness never reads grader files, reference files, or its own `artifacts/`.
   A breach disqualifies the entry.
2. **Grader firewall for the build team.** Only `experiment-runner` and `failure-analyst`
   may open grader files, reference files or per-constraint grader output. Builder agents
   receive failure *classes* ("unit error in a voltage-drop check"), never expected values.
3. **One declared model, no outside help.** The entry calls only the model named in
   `submission.yaml`. No provider-hosted tools (web search, web fetch, code execution),
   no other hosts, no secrets in the repository.
4. **The model picks the tool; deterministic code owns the number.** Wherever a number in
   a deliverable can be computed by a script or a tool in the task container, it is
   computed there, with units checked. The model does not do load-bearing arithmetic in
   its head.
5. **Never end without a gradable deliverable.** Write a draft at the required path early,
   improve it, and always send `done` with a clear final message before the deadline.
   Handle `cancel`. A crash or timeout grades whatever is already in the container.
6. **Deliverables and the final message are normal professional prose.** Terse style is
   allowed only in narration between tool calls. A judge model reads the deliverables.
7. **Only a measured gain gets merged.** Every behaviour change has ledger rows (run ID,
   git SHA, config, model, task, score, tokens, cost, time). No number appears in docs or
   the writeup unless the ledger holds it.
8. **Holdout.** Ten of the 29 dev tasks are held out. Builder agents do not see their
   results until the code freeze.
9. **Cost never buys a score loss.** A cost policy that lowers the score on the tuning
   tasks is rejected. First place is decided on score alone.
10. **Licence.** Apache-2.0. Dependencies must be compatible. Text adapted from MIT
    projects (superpowers, ponytail) is credited in `NOTICE`. No copyrighted code-table
    text (NEC, IBC and similar) in the repository: each task carries its own governing
    documents and the harness reads them there.
11. **Budget gates.** Announce the estimated cost before every paid run. No spend above a
    budget line (section 6) without Hari's approval.
12. **Kit checks stay green.** A commit is a submission candidate only when
    `kit check` ends with `ready to submit`.

## 2. The competition, condensed

The kit repository is the source of truth: <https://github.com/google-research/ple>.
Clone it **next to** this repository, never into it, and re-read its `docs/` before
relying on anything below. Kaggle page:
<https://www.kaggle.com/competitions/physical-engineerings-last-exam>.

### 2.1 What an entry is

One commit of one GitHub repository, with at the root: `submission.yaml`, `serve.py`,
`harness.py`, an Apache-2.0 or MIT `LICENSE`, and the unpacked `artifacts/` produced by
`eval/run.py` on the dev set (at most 512 MiB and 10,000 files, no Git LFS, no symlinks,
never edited by hand). A private repository needs the `ple-submission` GitHub App and must
be public at the close.

`submission.yaml` fields: `name` (2-39 chars of `a-z0-9-`), `model_api`, `install`
(optional, runs once at build), `serve` (required, starts the server on `$PORT`), `env`
(non-secret settings only).

### 2.2 Where the code runs

| Container | What it is | Limits |
|---|---|---|
| Build | `debian:bookworm` with uv, Node 22, git, compilers. `install` runs as root with internet | 30 minutes. Everything must land under `/opt/harness`, at most 2 GiB packed. `apt-get` packages do not carry over. Create Python with `uv venv --python 3.12 /opt/harness/venv` |
| Serve (ours) | Our server, one per task, uid 1000, read-only root | 2 CPUs, 4 GB RAM, 512 processes, 1 GB `/tmp`, 1 GB `$HOME`. Must accept a WebSocket on `0.0.0.0:$PORT` within 120 s. Outbound traffic reaches the model API only; idle connections close after 30 minutes |
| Task | Project files and tools, no network | Reached only through the protocol below |

### 2.3 The serve protocol (version 1)

- First message from the evaluator: `task` with `instruction`, `workdir`, `limits`
  (`agent_timeout_sec`, `exec_timeout_sec`, `max_output_bytes`, `max_write_bytes`) and
  `mcp_servers`.
- Requests, each with an `id`, at most 8 running at once: `exec` (default 120 s, capped
  at 600 s, output capped at 100 KB head and tail), `read_file` and `write_file` (10 MB
  per call, `append` for larger writes), `http` (only to the task's MCP server URLs).
- One-way messages: `log`, `usage` (model, input, output and cache-read tokens), `done`
  (`final_message`), `error`.
- On timeout the evaluator sends `cancel`; we then have 10 seconds to send `done`.
- More than 20 malformed frames, or any frame over 16 MiB, ends the task.
- Run the server without keepalive pings (`ping_interval=None`).
- A task's MCP tool catalog can hold hundreds of tools (about 500 KB). Never place it in
  context whole.
- Graders extract text from `.txt .md .csv .json .yaml .yml .py .html .xml .docx .xlsx
  .pptx .pdf`. Rubric graders also read the final message, so it must say what was
  produced and where.
- Stop any background process before sending `done`.

### 2.4 Scoring and stages

- Every task scores 0 to 1. Constraint tasks score each item as
  `s = 0.4 p + 0.6 G O'`: `p` is the share of constraints met, `G` is 1 only if every
  hard (safety and feasibility) constraint is met, `O'` is the normalized objective.
  **One broken hard constraint caps the item at 0.4.**
- Dev set: 29 public tasks (9 electrical, 9 civil, 7 mechanical, 4 structural; 12 graded
  by checks, 3 by checks plus judge, 14 by rubric). The list is in the kit's
  `eval/dev_set.yaml`. Do not copy task identifiers into this repository's runtime folders.
- **Stage 1** (gate): a Kaggle Writeup of at most 2,000 words, scored out of 100:
  Insight and failure analysis 25, Engineering reasoning 25, Cross-model generalizability
  15, Efficiency and scaling 20, Clarity and visuals 15. Required: a cover image and three
  figures (architecture diagram, score-versus-cost plot, dev-set failure breakdown), the
  repository URL and the 40-character commit SHA. The top 100 advance.
- **Stage 2** (ranking): 56 hidden tasks (23 mechanical, 18 electrical, 9 civil, 6
  structural), three runs each. Prizes go to the top three by mean score among entries on
  the score-versus-cost Pareto frontier. Minimum mean score 0.138. Google pays for these
  runs.
- Published baseline: Opus 5.5 scored 47.3% to 50.6% across seven harnesses. The best
  baseline met 91% of individual constraints on co-authored tasks but cleared every hard
  constraint on only 41.3% of deliverables. **Raising that pass rate is our main lever.**

### 2.5 Calling the model

- The server reads `MODEL_NAME`, `MODEL_BASE_URL` / `OPENAI_BASE_URL`, `MODEL_API_KEY` /
  `OPENAI_API_KEY`, and for Claude `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY`.
- Claude caches only at explicit breakpoints (up to 4): mark the system prompt and the
  newest message. Without them every turn re-processes the whole conversation.
- With no reasoning level given, the gateway uses the model's maximum. Set
  `reasoning_effort` explicitly per phase.
- Opus 5.5 returns `400` for `temperature`, `top_p`, `top_k`, a thinking budget,
  disabled thinking, or a forced tool choice. Use `auto`, and `max_tokens` around 32000.
- For local dev runs, set `model_api: anthropic/claude-opus-5-5` with `ANTHROPIC_API_KEY`
  in an env file outside the repository, or keep the `google-cloud/` name and point the
  kit at a local proxy (`MODEL_PROXY_URL`, `MODEL_PROXY_KEY`). Before any submission
  candidate, set `model_api` back to `google-cloud/claude-opus-5-5` and rerun `kit check`.
- Stream long calls. Retry `429`, timeouts and `5xx` with backoff. Never retry a `400`
  unchanged; an invalid request counts against the score.

## 3. Architecture

### 3.1 Run-time flow of one task

1. **Intake** (deterministic scripts run in the task container). Inventory files, sizes
   and types. Flag revisions and superseded documents. Write a project index file in the
   container. Digest the MCP catalog to names only and load tool schemas on demand.
2. **Plan.** List each required deliverable with its path and format. Build the
   **constraint ledger**: every hard limit with its source file and page. Choose the
   method and the checks.
3. **Draft early.** Write a minimal valid deliverable at the required path.
4. **Work.** Compute with scripts and tools in the container. Keep state in files (index,
   ledger, notes), not in conversation history.
5. **Self-check gate.** An executable checker written against the ledger. It must pass,
   or be waived with a stated reason when time is short.
6. **Independent verifier.** A fresh conversation that sees only the instruction, the
   ledger and the deliverable. It answers PASS or a numbered list of issues. At most two
   fix rounds.
7. **Finalize.** Check formats and paths, write the final message, send `done`.

Time budget: track `limits.agent_timeout_sec`. Planning takes at most 10% of the time,
and a wrap-up reserve is never spent on new work.

### 3.2 Runtime decision (settle in Phase 1, record as ADR-0001)

- **Option A: wrap the Claude Code CLI or Agent SDK.** Claude Code was the best published
  harness for Opus 5.5 (50.6%) and the kit docs anticipate it (`API_FORCE_IDLE_TIMEOUT=0`).
  File and shell tools must be redirected to the task container through an MCP bridge, as
  the kit's `agy-gemini` sample does. Verify that it fits the serve container limits and
  that its licence terms allow this use. If adopted, the runtime starts from its own
  `runtime/` folder with its own configuration so the build-time `.claude/` is never
  loaded into a task.
- **Option B: a custom Python loop** built from the kit's `plan-verify` sample and
  `taskbridge.py`. Smallest fixed context, full control, more to build.

Decide on measured score and cost on the Opus subset, not on preference.

### 3.3 Repository layout

```text
ple-harness/
  submission.yaml  serve.py  harness.py  LICENSE  NOTICE  CLAUDE.md  HANDOVER.md
  harness/     protocol, agent loop, phases, deadlines, final message
  cost/
    engine/    caching, compaction, output filters, memoization, effort
    policies/  declarative rules chosen at task start
    bench/     replay tests: tokens saved against score change
  skills/      run-time playbooks, loaded on demand during a task
    core/      intake, constraint ledger, verify before done, fix round
    mechanical/  electrical/  civil-structural/
    style/     terse narration between tool calls
  tools/       deterministic domain tools the skills call
  tests/       unit, protocol and replay tests
  artifacts/   dev-set outputs exported by the kit (never edited by hand)
  docs/        adr/ handover/ eval/ (run ledger, holdout list) writeup/
  .claude/     build-time only: agents/ skills/ hooks, settings.json
  runs/        ignored by git: saved runs for the replay bench
```

### 3.4 The cost layer

Three layers, because a skill file cannot set a cache breakpoint and prose in context
costs tokens on every step.

- `cost/engine/` (code): cache breakpoints, compaction at phase boundaries, tool-output
  digests, memoized file parses, per-phase reasoning effort, token metering.
- `cost/policies/` (data): declarative rules such as when to compact, budgets per phase
  and which outputs to digest. This is where decisions live without code changes.
- `skills/` (text): behaviour only the model can carry out.
- `cost/bench/`: replays saved runs and reports tokens saved against score change.

Order of adoption:

| Kind | Policies | Rule |
|---|---|---|
| Lossless | Prompt caching, trimmed tool schemas, memoization, sandbox pre-filtering | On by default from Phase 2 |
| Lossy | Compaction, lower reasoning effort, terse narration, turn limits | Behind a toggle; kept only if the score holds on the tuning tasks |

There is no model routing: any other model returns `403` in evaluation. Route reasoning
effort instead.

### 3.5 Run-time skills

- Each skill is a short markdown file with a name, a one-line description and a body.
  Only names and descriptions sit in context; a body loads when a generic signal fires.
- Every skill must pay for itself on the replay bench.
- superpowers is **not** installed at run time: its planning skills expect a person and
  its session hook adds fixed context. Rewrite its verify-before-completion and
  systematic-debugging ideas as short `skills/core/` playbooks for engineering
  deliverables, with attribution.
- ponytail is **off** at run time by default. It is built for coding requests, and a
  least-code bias can cut content a rubric expects. A script-only variant may be tested
  behind a toggle.

### 3.6 Domain tools

General, deterministic and tested on textbook cases, never on dev-task values. Priority
follows the hidden set: mechanical and electrical first (41 of 56 hidden tasks), then
civil and structural.

- Mechanical: IFC clash checks and routing helpers, life-cycle cost, review playbooks for
  simulation work.
- Electrical: cable sizing with voltage drop and derating from tables the task provides,
  one-line graph extraction, takeoffs and bills of materials.
- Civil and structural: load paths, diaphragm shear, settlement, site layout, estimates.
- Everywhere: unit handling and a checker pattern for hard limits.

Tools must fit the serve container (2 CPUs, 4 GB) or be written into the task container
with `write_file` and run there.

## 4. Development harness (how we build this with agents)

### 4.1 Plugins (send each line as its own prompt)

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

- **superpowers** is the workflow spine: `superpowers:brainstorm` →
  `superpowers:write-plan` → `superpowers:execute-plan`, test-first, systematic debugging,
  verification before completion, a worktree per workstream.
- **ponytail**: level `full` in `harness/` and `cost/`; level `lite` in `tools/`, where
  explicit formulas with their source beat short code. Run `ponytail:ponytail-review` on
  every merge and keep its `ponytail:` comments.

### 4.2 Agents (`.claude/agents/`, one self-contained briefing each)

| Agent | Job | Must not |
|---|---|---|
| `lead` (main session) | Picks one change at a time, assigns it, merges, keeps the budget ledger | Write harness code itself |
| `harness-engineer` | Protocol, agent loop, context, deadlines, early drafts, `cost/` | Open grader or reference files |
| `verifier-engineer` | Constraint ledger, self-check gate, independent verifier | Open grader or reference files |
| `domain-mechanical` | Mechanical tools and skills | Use values from dev tasks |
| `domain-electrical` | Electrical tools and skills | Use values from dev tasks |
| `domain-civil-structural` | Civil and structural tools and skills | Use values from dev tasks |
| `experiment-runner` | Starts and stops the VM, runs the kit, writes ledger rows | Change harness code |
| `failure-analyst` | Reads run logs and grader output, names failure classes | Pass expected answers to builders |
| `fair-play-reviewer` | Reviews every merge against section 1; checks licences and kit status; scans the forum and kit repo twice a week | Fix the code it reviews |
| `writeup-author` | Keeps the writeup and its three figures current from the ledger | State a number that is not in the ledger |

### 4.3 Project skills (`.claude/skills/`)

`ple-handover`, `ple-experiment-ledger`, `ple-fair-play-review`, `ple-kit-checks`,
`ple-runtime-skill-authoring`.

### 4.4 Hooks (`.claude/settings.json`)

- PostToolUse: format the touched file.
- PreToolUse: block builder agents from reading grader and reference paths (the `tests/`
  and solution folders of each downloaded task; confirm the exact paths in Phase 0; if
  hooks cannot tell agents apart, block by default and allow only in a session started
  with an explicit analyst flag);
  block hand edits under `artifacts/`; block `git push --force`; block any write that
  looks like an API key or token.
- Stop: refuse to end a session unless tests ran and a handover newer than the session
  start exists. Have `make check` itself write the tests-ran marker on success. In
  complychip-ED a separate matcher hook failed closed on passing runs twice.

### 4.5 Per-change workflow (mandatory)

brainstorm → write-plan → execute-plan with a failing test first → verification before
completion → `fair-play-reviewer` sign-off → ledger rows → handover. Any architectural
choice gets an ADR in `docs/adr/`. No ADR, no merge.

Worktrees: `harness`, `cost`, `domain-mech`, `domain-elec`, `domain-civil-struct`,
`eval`, `writeup`. Never work on `main`.

## 5. Experiment protocol

### 5.1 The loop

1. `lead` picks one change and names the score it expects to move.
2. A builder implements it test-first; `fair-play-reviewer` signs off or blocks.
3. `experiment-runner` runs the tuning model on the tuning tasks; `failure-analyst`
   classifies what failed.
4. A change that helps is rerun on the Opus subset.
5. If the gain holds: merge, ledger rows, figures updated. If not: drop it and log why.
   Failed ideas are material for the writeup.

### 5.2 Task sets (fixed once in Phase 1, recorded in `docs/eval/`)

| Set | Size | Mix | Use |
|---|---|---|---|
| Holdout | 10 | 3 electrical, 3 civil, 2 mechanical, 2 structural | Checked once at the freeze |
| Tuning | 19 | The rest | Daily iteration on the tuning model |
| Opus subset | 8 of the tuning set | 3 electrical, 2 mechanical, 2 civil, 1 structural; prefer check-graded tasks | Confirmation on Opus 5.5 |

Skip tasks that score near 0 or above 0.9 whatever we change; they carry no signal.

### 5.3 Models

- **Submission:** Opus 5.5.
- **Tuning:** Claude Sonnet 5.5 (same family, so changes should transfer better) or
  Gemini 3.8 Flash (cheapest). Choose in Phase 1 by measured cost and by how well its
  ranking of two harness variants matches Opus.
- **Second model for the writeup:** the tuning model's full 29-task pass.
- **Judge for iteration:** a cheaper judge is allowed; organizers re-score with Opus 5.5.
  Record the judge on every ledger row.

### 5.4 Noise (why one rerun proves nothing)

Repeat runs of the same task swung by about 15 points on average in the benchmark paper,
which implies a run-to-run standard deviation near 9 points per task (estimate).

| Comparison | Smallest gain to trust (estimate) |
|---|---|
| 8 tasks, one run per arm | about 9 points |
| 29 tasks, one run per arm | about 5 points |
| 29 tasks, three runs per arm | about 3 points |

Decide on the fixed sets, never on a single task. Stop a comparison early once it is
clearly losing.

### 5.5 Replay before rerun

Save every run's deliverables and logs under `runs/`. Test verifier and checker changes
against saved deliverables first; that costs a few verifier calls, not a full run. The
harness itself never reads `runs/` or `artifacts/`.

### 5.6 Ledger

`docs/eval/ledger.jsonl`, one row per task run: `run_id`, date, git SHA, config flags,
model, judge, task set, task, outcome (`done`, `error`, `timeout`), score, input, output
and cache-read tokens, cost, wall time, note.

## 6. Money and model access

Cash cap: **$1,000**, released in stages. Free sources are used first.

| Source | Cash | Notes |
|---|---|---|
| Monthly API credits on Hari's Claude plan | $0 | $100 or $200 a month depending on the plan tier; expires each billing cycle. Hari claims it and provides a key outside the repository |
| Plan usage limits through headless Claude Code | $0 | Only with Option A. Sign in with `CLAUDE_CODE_OAUTH_TOKEN` and leave `ANTHROPIC_API_KEY` unset, because a key wins in headless mode. Measure three runs with `/usage` first. The token is a secret |
| VM for runs | $100 | x86 Linux with its own Docker daemon. On vast.ai that means a VM template, since standard instances cannot run Docker. About 8 vCPUs, 32 GB RAM, 150 GB disk. Stop it between runs |
| Tuning model and judge | $150 | |
| Opus 5.5 through the API | $250 now | Target at most $15 per task; measure it in Phase 1 |
| Held back | $500 | Released by Hari at the Phase 1 gate and the Phase 3 gate, only on evidence |

- Run evaluations on the x86 VM, never under emulation on Apple silicon: timed graders
  score lower there.
- The final Opus pass on all 29 tasks costs about $435 at $15 per task. If money is
  short, committing outputs from a cheaper model is allowed when the writeup says so.
- Use only API providers that do not train on inputs until the hosts answer the open
  forum question on data use.

## 7. Phases and acceptance criteria

Each phase ends with: tests green, a handover written, ledger current, and the gate
decision recorded by Hari. Do not start the next phase without these.

### Phase 0a — Bootstrap on the laptop (2026-11-16, no accounts needed, no harness code)
- The fresh-folder preflight in section 0.1.
- Repository skeleton from section 3.3, `LICENSE` (Apache-2.0), `NOTICE`, `.gitignore`
  (`runs/`, env files, caches), `Makefile`, CI, the handover and ADR templates.
- Agents, project skills and hooks from section 4 in place.
- The kit cloned next to the repository (it is public, Apache-2.0, and needs no account).
  Root files `submission.yaml`, `serve.py` and `harness.py` start from one of the kit's
  samples under `sample_submissions/` (`minimal` or `plan-verify`), credited in `NOTICE`.
  The Kaggle page also names a `submission-template` folder; the kit clone checked on
  2026-11-15 had none, so use the samples.
- **Accept when:** `make check` passes on the laptop; `docs/handover/LATEST.md` exists;
  the Stop hook blocks a session that skips the handover and allows one that writes it.

### Phase 0b — Kit and VM (to 2026-11-18, needs Hari's steps in section 9)
- Harbor 0.20.0 installed on the VM; dataset access working with `HF_TOKEN`.
- **Accept when:** one of the kit's sample harnesses that uses MCP (for example
  `custom-openai`) passes `kit check` through its smoke and MCP stages on the VM.
- If access is still missing on 11-18, continue with Phase 2 design work that needs no
  runs, and record the blocker in the handover.

### Phase 1 — Baseline and go/no-go (to 2026-11-22)
- Task sets fixed (5.2). Tuning model chosen (5.3).
- Kit's `plan-verify` sample run on the Opus subset; a three-task spike of Option A.
- Failure classes written up from the baseline runs.
- One verification spike (self-check gate) measured on the tuning model.
- **Accept when:** infrastructure works end to end; cost per Opus task is known; the
  spike shows a repeatable gain; ADR-0001 chooses the runtime.

### Phase 2 — Core harness (2026-11-23 to 12-06)
- Sections 3.1 and 3.4 lossless policies: intake, index, constraint ledger, early draft,
  self-check gate, independent verifier, finalizer, caching, schema trimming, digests.
- **Accept when:** no run on the tuning tasks ends without a gradable deliverable;
  `kit check` ends `ready to submit`; fixed context per step is measured and recorded.

### Phase 3 — Domain tools and skills (2026-12-07 to 12-20)
- Mechanical and electrical first, then civil and structural. Each lands with its
  ablation in the ledger.
- **Accept when:** the Opus subset beats the Phase 1 baseline.

### Phase 4 — Cost and second model (2026-12-21 to 12-27)
- Lossy policies through the replay bench; score-versus-cost curve; full second-model
  pass.
- **Accept when:** the submitted configuration is chosen and written in an ADR.

### Phase 5 — Freeze and writeup (2026-12-28 to 2027-01-03)
- Code freeze on 12-28. Holdout check. Final dev pass exported by `eval/run.py`.
  `kit check` and `kit artifacts` green.
- Writeup of at most 2,000 words with the three figures and a cover image. State the
  judge and any model that produced the committed outputs. State plainly that no licensed
  engineer reviewed the work unless one did.
- **Accept when:** Hari has read the writeup and submitted it. 01-04 and 01-05 are buffer.

## 8. What NOT to build

A UI, an API server, a database, multi-model routing, fine-tuning, a local LLM inside
the serve container, task-specific solvers, anything that reads graders, a copy of the
kit inside this repository, web access at run time, complychip-ED integration, a general
plugin marketplace.

## 9. What only Hari does

- Joins the competition on Kaggle as an individual and accepts the rules.
- Accepts the Hugging Face dataset terms and creates a read token.
- Opens the VM account, adds an SSH key and sets a spend limit.
- Claims the plan's API credits and creates capped model keys.
- Creates the private GitHub repository and installs the `ple-submission` GitHub App.
- Approves each phase gate and any spend above a budget line.
- Reads, edits and submits the writeup.

## 10. Open questions (resolve, then record in an ADR or a handover)

1. Real Opus cost per task with a lean harness.
2. Option A or Option B (ADR-0001), including Claude Code CLI licence terms and container
   fit.
3. How many task runs the plan's usage limits allow per week.
4. vast.ai VM against a plain x86 cloud VM for a box with no GPU.
5. Forum answers still pending: offline use of per-constraint grader output, how cached
   tokens count in the cost ranking, and the reproducibility check when committed outputs
   come from another model.

## 11. First message to send Claude Code

> Read `HANDOVER.md` and `CLAUDE.md`. Run the fresh-folder preflight in section 0.1 and
> show me the ready/missing table. Then run `superpowers:brainstorm` for Phase 0a only.
> Produce a plan with `superpowers:write-plan`, stop, and show me the plan before
> executing anything.

## Sources

- Kaggle overview and rules: <https://www.kaggle.com/competitions/physical-engineerings-last-exam/overview>
- Competition kit: <https://github.com/google-research/ple> (`docs/protocol.md`, `docs/models.md`, `docs/rules.md`, `kit/README.md`, `eval/README.md`)
- Benchmark paper: <https://arxiv.org/abs/2610.30537>
- Plan API credits: <https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans>
- Headless sign-in: <https://code.claude.com/docs/en/authentication>
- superpowers: <https://github.com/obra/superpowers> · ponytail: <https://github.com/DietrichGebert/ponytail>
