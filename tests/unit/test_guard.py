"""Tests for .claude/hooks/guard.py, run as a subprocess the way Claude Code runs it."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

GUARD = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "guard.py"
TASKS = "/home/u/.cache/plebench/tasks/abc123/tasks/some-task"


def run(event: str, payload: dict[str, Any] | str, root: Path, **env: str) -> dict[str, Any] | None:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    done = subprocess.run(
        [sys.executable, str(GUARD), event],
        input=stdin,
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root), **env},
        check=True,
    )
    return json.loads(done.stdout) if done.stdout.strip() else None


def decision(tool: str, tool_input: dict[str, Any], root: Path, agent: str | None = None) -> str:
    payload: dict[str, Any] = {"tool_name": tool, "tool_input": tool_input}
    if agent:
        payload["agent_type"] = agent
    out = run("pre", payload, root)
    return "allow" if out is None else out["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "tool,tool_input",
    [
        ("Read", {"file_path": f"{TASKS}/tests/verify.py"}),
        ("Read", {"file_path": "/home/u/.cache/plebench/tasks/abc123/task_cards.jsonl"}),
        ("Grep", {"pattern": "x", "path": TASKS}),
        ("Glob", {"pattern": "**/*.py", "path": "/home/u/.cache/plebench/tasks"}),
        ("Bash", {"command": f"cat {TASKS}/tests/grader/x.py"}),
        ("Bash", {"command": "grep -r load ~/.cache/plebench/tasks/abc123"}),
        ("Read", {"file_path": "runs/r1/attempt1/t1/verifier/reward.json"}),
        ("Bash", {"command": "ls ../ple/runs/"}),
    ],
)
@pytest.mark.parametrize("agent", [None, "harness-engineer"])
def test_firewall_denies_builders(
    tool: str, tool_input: dict[str, Any], agent: str | None, tmp_path: Path
) -> None:
    assert decision(tool, tool_input, tmp_path, agent) == "deny"


@pytest.mark.parametrize("agent", ["experiment-runner", "failure-analyst"])
def test_firewall_allows_analysts(agent: str, tmp_path: Path) -> None:
    assert decision("Read", {"file_path": f"{TASKS}/tests/verify.py"}, tmp_path, agent) == "allow"


@pytest.mark.parametrize(
    "tool_input",
    [
        {"file_path": "tests/unit/test_guard.py"},
        {"file_path": f"{TASKS}/instruction.md"},
        {"file_path": f"{TASKS}/environment/files/site.pdf"},
    ],
)
def test_firewall_allows_task_inputs_and_own_tests(
    tool_input: dict[str, Any], tmp_path: Path
) -> None:
    assert decision("Read", tool_input, tmp_path) == "allow"


def test_artifacts_write_tool_denied(tmp_path: Path) -> None:
    assert decision("Write", {"file_path": "artifacts/x/a.md", "content": "x"}, tmp_path) == "deny"
    assert decision("Write", {"file_path": "docs/a.md", "content": "x"}, tmp_path) == "allow"


@pytest.mark.parametrize(
    "command,expected",
    [
        ("echo x > artifacts/a.md", "deny"),
        ("rm -rf artifacts", "deny"),
        ("ls artifacts/ 2>&1", "allow"),
        ("uv run python eval/run.py ../ple-harness", "allow"),
        ("uv run python -m kit artifacts ../ple-harness --from runs/r1", "allow"),
    ],
)
def test_artifacts_bash(command: str, expected: str, tmp_path: Path) -> None:
    assert decision("Bash", {"command": command}, tmp_path) == expected


@pytest.mark.parametrize(
    "command,expected",
    [
        ("git push --force", "deny"),
        ("git push -f origin x", "deny"),
        ("git push --force-with-lease origin x", "deny"),
        ("git push origin +main", "deny"),
        ("git push origin phase-0a", "allow"),
        ("git push -u origin ws/harness", "allow"),
        ("git push --follow-tags origin main", "allow"),
    ],
)
def test_force_push(command: str, expected: str, tmp_path: Path) -> None:
    assert decision("Bash", {"command": command}, tmp_path) == expected


def test_secrets(tmp_path: Path) -> None:
    fake = "sk-" + "ant-" + "Ab3dE" * 8  # built at run time so no key sits in this file
    assert decision("Write", {"file_path": "a.py", "content": f"K = '{fake}'"}, tmp_path) == "deny"
    assert decision("Edit", {"file_path": "a.py", "new_string": fake}, tmp_path) == "deny"
    assert decision("Bash", {"command": f"echo {fake} >> x"}, tmp_path) == "deny"
    words = "sk-" + "learn-is-a-url-path-not-a-key"
    assert decision("Write", {"file_path": "a.md", "content": words}, tmp_path) == "allow"


def test_malformed_input(tmp_path: Path) -> None:
    out = run("pre", "not json", tmp_path)
    assert out is not None and out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert run("stop", "not json", tmp_path) is None


# --- Stop gate -------------------------------------------------------------------------------


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".gitignore").write_text(".claude/state/\n")
    (tmp_path / "docs" / "handover").mkdir(parents=True)
    (tmp_path / "docs" / "handover" / "LATEST.md").write_text("old\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    past = time.time() - 3600
    os.utime(tmp_path / "docs" / "handover" / "LATEST.md", (past, past))
    run("start", {"session_id": "s1", "source": "startup"}, tmp_path)
    return tmp_path


def stop(root: Path, **env: str) -> dict[str, Any] | None:
    return run("stop", {"session_id": "s1", "stop_hook_active": False}, root, **env)


def test_unchanged_session_may_stop(repo: Path) -> None:
    assert stop(repo) is None


def test_changed_session_without_handover_is_blocked(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    out = stop(repo)
    assert out is not None and out["decision"] == "block"
    assert "make check" in out["reason"] and "LATEST.md" in out["reason"]


def test_changed_session_with_tests_and_handover_may_stop(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    (repo / ".claude" / "state" / "tests-ran").touch()
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    assert stop(repo) is None


def test_compact_keeps_start_time(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    (repo / ".claude" / "state" / "tests-ran").touch()
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    run("start", {"session_id": "s1", "source": "compact"}, repo)
    assert stop(repo) is None


def test_gate_off_switch(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    assert stop(repo, PLE_STOP_GATE="off") is None


def test_missing_session_record_may_stop(tmp_path: Path) -> None:
    assert run("stop", {"session_id": "never-started"}, tmp_path) is None
