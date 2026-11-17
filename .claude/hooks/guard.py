"""Claude Code hook guard for ple-harness. Build time only; never part of the entry.

Usage: guard.py pre|post|start|stop, with the hook's JSON on stdin.
Rules: docs/superpowers/specs/2026-11-16-phase-0a-design.md, section 4.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ANALYSTS = frozenset({"experiment-runner", "failure-analyst"})
WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
PATH_FIELDS = ("file_path", "path", "notebook_path", "pattern", "glob", "command")
BODY_FIELDS = ("content", "new_string", "new_source", "command")
VENDORED = frozenset({"serve.py", "taskbridge.py"})

# ponytail: regexes over paths and command text stop honest mistakes, not a determined agent;
# an OS or Docker sandbox is the upgrade if that ever matters. Accepted residual risk: a Bash
# command that cds into the kit and uses relative paths, or recurses from ~/.cache.
TASK_CACHE = re.compile(r"\.cache/plebench/tasks[^\s'\"]*")
CACHE_ROOT = re.compile(r"\.cache/plebench/?(?![^\s'\"])")
VERIFIER = re.compile(r"\bruns/[^\s'\"]*verifier")
KIT_RUNS = re.compile(r"\bple/runs\b")
ARTIFACT_WORD = re.compile(r"\bartifacts\b")
ARTIFACT_WRITE = re.compile(
    r">|\btee\b|\brm\b|\bmv\b|\bcp\b|\bsed\s+-i|\btouch\b|\bmkdir\b|\brsync\b"
)
HARMLESS_REDIRECT = re.compile(r"\d*>&\d|\d*>\s*/dev/null")
ARTIFACT_EXPORTERS = re.compile(r"eval/run\.py|kit artifacts")
FORCE_PUSH = re.compile(
    r"\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*"
    r"(\s--force(-with-lease|-if-includes)?\b|\s-[A-Za-z]*f[A-Za-z]*\b|\s\+\S)"
)
# Same shape as the kit's KEY_RE (kit/check.py, Apache-2.0), plus AWS and fine-grained GitHub
# tokens. A body counts only when it mixes upper case, lower case and digits, like a real key.
KEY = re.compile(
    r"(?<![A-Za-z0-9])(?:(?P<prefix>sk-(?:ant-|proj-)?|AIza|gh[pousr]_|github_pat_|hf_"
    r"|xox[baprs]-)(?P<body>[A-Za-z0-9_-]{20,4000})|-----BEGIN [A-Z ]{0,64}PRIVATE KEY-----"
    r"|AKIA[0-9A-Z]{16}(?![0-9A-Z]))"
)


def project_root(payload: dict[str, Any]) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()


def texts(tool_input: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    found = [str(tool_input[f]) for f in fields if isinstance(tool_input.get(f), str)]
    if "new_string" in fields:
        found += [str(e.get("new_string", "")) for e in tool_input.get("edits") or []]
    return found


def task_cache_leak(text: str) -> bool:
    if CACHE_ROOT.search(text):
        return True  # the bare cache root: a recursive read would reach tasks/
    for match in TASK_CACHE.finditer(text):
        token = match.group(0)
        if "/tests" in token or "task_cards" in token:
            return True
        if "/environment/" in token or token.endswith("/instruction.md"):
            continue
        return True  # the cache or a task root: a recursive read would reach tests/
    return False


def kit_dir(root: Path) -> Path:
    if os.environ.get("PLE_KIT_DIR"):
        return Path(os.environ["PLE_KIT_DIR"])
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
    )
    if done.returncode == 0 and done.stdout.strip():
        return Path(done.stdout.strip()).parent.parent / "ple"
    return root.parent / "ple"


def reaches_protected(search_path: str, root: Path) -> bool:
    """True when a Grep/Glob path is, or sits above, the task cache or the kit's runs/."""
    target = (root / Path(search_path).expanduser()).resolve()
    protected = (Path.home() / ".cache" / "plebench" / "tasks", kit_dir(root) / "runs")
    return any(target == p.resolve() or target in p.resolve().parents for p in protected)


def looks_like_key(text: str) -> bool:
    for m in KEY.finditer(text):
        body = m.group("body")
        if body is None or (
            re.search("[A-Z]", body) and re.search("[a-z]", body) and re.search("[0-9]", body)
        ):
            return True
    return False


def deny_reason(payload: dict[str, Any]) -> str | None:
    tool = str(payload.get("tool_name", ""))
    tool_input: dict[str, Any] = payload.get("tool_input") or {}
    paths = texts(tool_input, PATH_FIELDS)
    root = project_root(payload)

    if payload.get("agent_type") not in ANALYSTS:
        search = tool_input.get("path")
        if tool in ("Grep", "Glob") and search and reaches_protected(str(search), root):
            return "grader firewall: this search would recurse into grader files or runs/."
        for text in paths:
            if task_cache_leak(text) or VERIFIER.search(text) or KIT_RUNS.search(text):
                return (
                    "grader firewall: only experiment-runner and failure-analyst may open "
                    "grader files, task_cards, verifier output or the kit's runs/. "
                    "Ask for failure classes instead."
                )

    if tool in WRITE_TOOLS:
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        parents = (root / str(target)).resolve().parents if target else ()
        if any(p.name == "artifacts" and (p.parent / "submission.yaml").exists() for p in parents):
            return "artifacts/ is exported by eval/run.py and never edited by hand."
    if tool == "Bash":
        command = str(tool_input.get("command", ""))
        if (
            ARTIFACT_WORD.search(command)
            and ARTIFACT_WRITE.search(HARMLESS_REDIRECT.sub("", command))
            and not ARTIFACT_EXPORTERS.search(command)
        ):
            return "artifacts/ is exported by eval/run.py and never edited by hand."
        if FORCE_PUSH.search(command):
            return "force push is blocked. Push a new commit instead."

    if any(looks_like_key(t) for t in texts(tool_input, BODY_FIELDS)):
        return "this looks like an API key or private key. Keys stay in env files outside the repo."
    return None


def pre(payload: dict[str, Any]) -> dict[str, Any] | None:
    reason = deny_reason(payload)
    if reason is None:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"ple guard: {reason}",
        }
    }


def post(payload: dict[str, Any]) -> None:
    root = project_root(payload)
    target = (root / str((payload.get("tool_input") or {}).get("file_path", ""))).resolve()
    if target.suffix != ".py" or target.name in VENDORED or root not in target.parents:
        return
    subprocess.run(
        ["uv", "run", "--frozen", "--project", str(root), "ruff", "format", "--quiet", str(target)],
        capture_output=True,
        check=False,
    )


def git_out(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )
    return done.stdout


def git_state(root: Path) -> tuple[str, str]:
    digest = hashlib.sha256()
    digest.update(git_out(root, "status", "--porcelain", "-uall").encode())
    digest.update(git_out(root, "diff", "HEAD", "--binary").encode())
    for rel in sorted(
        git_out(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    ):
        try:
            data = (root / rel).read_bytes() if rel else None
        except OSError:
            continue
        if data is not None:
            digest.update(rel.encode() + b"\0" + data)
    return git_out(root, "rev-parse", "HEAD").strip(), digest.hexdigest()


def state_file(root: Path, session_id: str) -> Path:
    return root / ".claude" / "state" / f"session-{session_id}.json"


def start(payload: dict[str, Any]) -> None:
    root = project_root(payload)
    path = state_file(root, str(payload.get("session_id", "unknown")))
    if payload.get("source") == "compact" and path.exists():
        return
    head, status = git_state(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"start": time.time(), "head": head, "status": status}))


def newer(path: Path, than: float) -> bool:
    return path.exists() and path.stat().st_mtime > than


def handover_file(root: Path) -> str:
    # ADR-0002: a workstream branch ws/<name> writes docs/handover/<name>.md; main writes LATEST.md
    branch = git_out(root, "branch", "--show-current").strip()
    name = branch.removeprefix("ws/") if branch.startswith("ws/") else "LATEST"
    return f"docs/handover/{name}.md"


def last_edit(root: Path, head: str) -> float:
    # Newest mtime among files changed since the session's start commit, handovers excluded, so
    # `make check` must run after the last edit. ponytail: deletions carry no mtime and are missed.
    names = git_out(root, "diff", "--name-only", head).splitlines()
    names += git_out(root, "ls-files", "--others", "--exclude-standard").splitlines()
    times = [
        (root / n).stat().st_mtime
        for n in names
        if n and not n.startswith("docs/handover/") and (root / n).is_file()
    ]
    return max(times, default=0.0)


def stop(payload: dict[str, Any]) -> dict[str, Any] | None:
    if os.environ.get("PLE_STOP_GATE") == "off":
        return None
    root = project_root(payload)
    path = state_file(root, str(payload.get("session_id", "unknown")))
    if not path.exists():
        print("ple guard: no session start record; stop gate skipped", file=sys.stderr)
        return None
    began = json.loads(path.read_text())
    if git_state(root) == (began["head"], began["status"]):
        return None
    missing = []
    if not newer(
        root / ".claude/state/tests-ran", max(began["start"], last_edit(root, began["head"]))
    ):
        if payload.get("stop_hook_active"):
            # Already blocked once: only the handover is required, so a failing `make check`
            # cannot trap the session. The handover must record that result.
            print(
                "ple guard: stopping with a stale .claude/state/tests-ran marker", file=sys.stderr
            )
        else:
            missing.append("run `make check` until it passes")
    handover = handover_file(root)
    if not newer(root / handover, began["start"]):
        missing.append(f"write {handover} (skill ple-handover)")
    if not missing:
        return None
    return {
        "decision": "block",
        "reason": "ple stop gate: this session changed files. Before ending: "
        + "; ".join(missing)
        + ".",
    }


def main(event: str) -> int:
    raw = sys.stdin.read()
    try:
        payload: dict[str, Any] = json.loads(raw)
        if event == "pre":
            result = pre(payload)
        elif event == "stop":
            result = stop(payload)
        elif event in ("post", "start"):
            (post if event == "post" else start)(payload)
            result = None
        else:
            raise ValueError(f"unknown event {event!r}")
    except Exception as exc:  # every failure needs a decided outcome
        if event == "pre":
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"ple guard error, fix the hook: {exc!r}",
                }
            }
        else:
            print(f"ple guard {event} error (allowed): {exc!r}", file=sys.stderr)
            result = None
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
