---
name: ple-runtime-skill-authoring
description: Use when writing or changing a run-time skill under skills/ - the short playbooks the harness loads during a PLE task.
---

# Run-time skill authoring

A run-time skill is a markdown file the model loads mid-task. Only its name and description
sit in context; the body loads when a generic signal fires.

File: `skills/<area>/<name>.md`, with frontmatter fields `name` (kebab-case), `description`
(one line starting "Load when", naming the generic signal) and `signals` (the file types,
sizes, tool-catalog size, deliverable format or time left that trigger it). The body is
numbered steps, at most 40 lines, in professional prose.

Rules:

1. Generic signals only. Never a task id, title, folder name or file hash; `make check` scans `skills/`.
2. One job per skill. Every line costs tokens on every load.
3. Numbers come from scripts or tools in the task container, with units. The skill names the tool.
4. No copyrighted code-table text. Point the model at the governing documents in the task's files.
5. A skill ships only when the replay bench or a ledger comparison shows it pays for itself.
6. Credit text adapted from superpowers or ponytail in `NOTICE`.
