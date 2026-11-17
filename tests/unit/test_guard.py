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
        env={
            **{k: v for k, v in os.environ.items() if k != "PLE_STOP_GATE"},
            "CLAUDE_PROJECT_DIR": str(root),
            **env,
        },
        check=True,
    )
    return json.loads(done.stdout) if done.stdout.strip() else None


def decision(
    tool: str,
    tool_input: dict[str, Any],
    root: Path,
    agent: str | None = None,
    env: dict[str, str] | None = None,
) -> str:
    payload: dict[str, Any] = {"tool_name": tool, "tool_input": tool_input}
    if agent:
        payload["agent_type"] = agent
    out = run("pre", payload, root, **(env or {}))
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


Sandbox = tuple[Path, Path, Path, dict[str, str]]


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    """Project root, fake HOME and fake kit, none nested in another, plus the env naming them."""
    root, home, kit = tmp_path / "proj", tmp_path / "home", tmp_path / "ple"
    for d in (root, home / ".cache" / "plebench" / "ple-harness", kit / "docs"):
        d.mkdir(parents=True)
    return root, home, kit, {"HOME": str(home), "PLE_KIT_DIR": str(kit)}


@pytest.mark.parametrize(
    "tool,field,value,extra",
    [
        ("Bash", "command", "grep -rn error {home}/.cache/plebench/", {}),
        ("Bash", "command", "grep -rn error ~/.cache/plebench", {}),
        ("Grep", "path", "{home}/.cache/plebench", {"pattern": "x"}),
        ("Grep", "path", "~/.cache/plebench", {"pattern": "x"}),
        ("Glob", "path", "{home}/.cache/plebench", {"pattern": "tasks/*/tests/**"}),
        ("Grep", "path", "{kit}", {"pattern": "x"}),
        ("Grep", "path", "../ple", {"pattern": "x"}),
    ],
)
def test_firewall_denies_recursion_from_above(
    tool: str, field: str, value: str, extra: dict[str, str], sandbox: Sandbox
) -> None:
    root, home, kit, env = sandbox
    tool_input = {field: value.format(home=home, kit=kit), **extra}
    assert decision(tool, tool_input, root, env=env) == "deny"


@pytest.mark.parametrize(
    "tool,tool_input",
    [
        ("Read", {"file_path": "{home}/.cache/plebench/ple-harness/serve.log"}),
        ("Bash", {"command": "tail ~/.cache/plebench/ple-harness/serve.log"}),
        ("Grep", {"pattern": "x", "path": "{kit}/docs"}),
        ("Grep", {"pattern": "x", "path": "~/.cache/plebench/ple-harness"}),
        ("Grep", {"pattern": "x", "path": "src"}),
    ],
)
def test_firewall_allows_logs_and_kit_docs(
    tool: str, tool_input: dict[str, str], sandbox: Sandbox
) -> None:
    root, home, kit, env = sandbox
    filled = {k: v.format(home=home, kit=kit) for k, v in tool_input.items()}
    assert decision(tool, filled, root, env=env) == "allow"


def test_analyst_may_grep_kit_root(sandbox: Sandbox) -> None:
    root, _, kit, env = sandbox
    tool_input = {"pattern": "x", "path": str(kit)}
    assert decision("Grep", tool_input, root, "failure-analyst", env) == "allow"


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
    (tmp_path / "submission.yaml").write_text("x: 1\n")
    assert decision("Write", {"file_path": "artifacts/x/a.md", "content": "x"}, tmp_path) == "deny"
    assert decision("Write", {"file_path": "docs/a.md", "content": "x"}, tmp_path) == "allow"


def test_artifacts_write_tool_follows_worktrees(tmp_path: Path) -> None:
    (tmp_path / ".worktrees" / "eval").mkdir(parents=True)
    (tmp_path / ".worktrees" / "eval" / "submission.yaml").write_text("x: 1\n")
    (tmp_path / "notes" / "artifacts").mkdir(parents=True)
    wt = {"file_path": ".worktrees/eval/artifacts/a.md", "content": "x"}
    assert decision("Write", wt, tmp_path) == "deny"
    other = {"file_path": "notes/artifacts/a.md", "content": "x"}
    assert decision("Write", other, tmp_path) == "allow"


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


def later(path: Path, seconds: float = 5) -> None:
    t = time.time() + seconds
    os.utime(path, (t, t))


def ran_tests(root: Path) -> None:
    # `make check` after the edits. Set the time explicitly: Linux CI stamps writes within one
    # clock tick with the same mtime, so an edit and the marker could otherwise tie.
    (root / ".claude" / "state" / "tests-ran").touch()
    later(root / ".claude" / "state" / "tests-ran", 1)


def test_unchanged_session_may_stop(repo: Path) -> None:
    assert stop(repo) is None


def test_changed_session_without_handover_is_blocked(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    out = stop(repo)
    assert out is not None and out["decision"] == "block"
    assert "make check" in out["reason"] and "LATEST.md" in out["reason"]


def test_changed_session_with_tests_and_handover_may_stop(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    ran_tests(repo)
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    assert stop(repo) is None


def test_tests_older_than_the_last_edit_block(repo: Path) -> None:
    (repo / ".claude" / "state" / "tests-ran").touch()  # e.g. `make check` at session start
    (repo / "new.py").write_text("x = 1\n")
    later(repo / "new.py")
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    out = stop(repo)
    assert out is not None and "make check" in out["reason"] and "LATEST.md" not in out["reason"]


def test_committed_edit_after_tests_blocks(repo: Path) -> None:
    (repo / ".claude" / "state" / "tests-ran").touch()
    (repo / "new.py").write_text("x = 1\n")
    later(repo / "new.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "edit")
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    out = stop(repo)
    assert out is not None and "make check" in out["reason"]


def test_handover_and_decision_log_after_tests_are_not_changes(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    ran_tests(repo)
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    (repo / "docs" / "decisions.md").write_text("- a decision\n")  # ple-handover step 5
    later(repo / "docs" / "handover" / "LATEST.md")
    later(repo / "docs" / "decisions.md")
    assert stop(repo) is None


def test_workstream_branch_needs_its_own_handover(repo: Path) -> None:
    git(repo, "switch", "-q", "-c", "ws/cost")
    (repo / "new.py").write_text("x = 1\n")
    ran_tests(repo)
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    out = stop(repo)
    assert out is not None and "docs/handover/cost.md" in out["reason"]
    (repo / "docs" / "handover" / "cost.md").write_text("new\n")
    assert stop(repo) is None


def test_compact_keeps_start_time(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    run("start", {"session_id": "s1", "source": "compact"}, repo)
    out = stop(repo)  # a re-recorded start would make the changed session look clean
    assert out is not None and out["decision"] == "block"


def test_edit_of_file_dirty_at_start_is_seen(repo: Path) -> None:
    (repo / ".gitignore").write_text(".claude/state/\n# dirty\n")
    run("start", {"session_id": "s1", "source": "startup"}, repo)
    assert stop(repo) is None
    (repo / ".gitignore").write_text(".claude/state/\n# dirty again\n")
    out = stop(repo)
    assert out is not None and out["decision"] == "block"


def test_edit_of_untracked_file_present_at_start_is_seen(repo: Path) -> None:
    (repo / "scratch.py").write_text("x = 1\n")
    run("start", {"session_id": "s1", "source": "startup"}, repo)
    assert stop(repo) is None
    (repo / "scratch.py").write_text("x = 2\n")
    out = stop(repo)
    assert out is not None and out["decision"] == "block"


def test_second_stop_needs_only_handover(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    payload = {"session_id": "s1", "stop_hook_active": True}
    out = run("stop", payload, repo)
    assert out is not None and out["decision"] == "block"
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    assert run("stop", payload, repo) is None  # tests-ran still stale: allowed with a warning


def test_second_stop_warns_about_stale_tests(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    (repo / "docs" / "handover" / "LATEST.md").write_text("new\n")
    done = subprocess.run(
        [sys.executable, str(GUARD), "stop"],
        input=json.dumps({"session_id": "s1", "stop_hook_active": True}),
        capture_output=True,
        text=True,
        env={
            **{k: v for k, v in os.environ.items() if k != "PLE_STOP_GATE"},
            "CLAUDE_PROJECT_DIR": str(repo),
        },
        check=True,
    )
    assert done.stdout.strip() == "" and "tests-ran" in done.stderr


def test_unknown_event_writes_no_session_record(tmp_path: Path) -> None:
    assert run("Stop", {"session_id": "s9"}, tmp_path) is None
    assert not list(tmp_path.glob(".claude/state/session-*.json"))


def test_gate_off_switch(repo: Path) -> None:
    (repo / "new.py").write_text("x = 1\n")
    assert stop(repo, PLE_STOP_GATE="off") is None


def test_missing_session_record_may_stop(tmp_path: Path) -> None:
    assert run("stop", {"session_id": "never-started"}, tmp_path) is None
