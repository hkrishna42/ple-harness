"""Checks that .claude/ config, CI and templates match what guard.py and the brief expect."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CLAUDE = ROOT / ".claude"


def test_settings_register_every_guard_event() -> None:
    hooks = json.loads((CLAUDE / "settings.json").read_text())["hooks"]
    expected = {"PreToolUse": "pre", "PostToolUse": "post", "SessionStart": "start", "Stop": "stop"}
    for event, arg in expected.items():
        commands = [h["command"] for group in hooks[event] for h in group["hooks"]]
        assert any(f'guard.py" {arg}' in c for c in commands), event
    first = {e: [h["command"] for g in hooks[e] for h in g["hooks"]][0] for e in expected}
    assert "|| true" not in first["PreToolUse"]  # pre fails closed
    assert "|| true" in first["Stop"]  # a broken launcher must not trap the session
    pre_matcher = hooks["PreToolUse"][0]["matcher"]
    assert set(pre_matcher.split("|")) >= {"Read", "Write", "Edit", "Grep", "Glob", "Bash"}


AGENTS = {
    "harness-engineer",
    "verifier-engineer",
    "domain-mechanical",
    "domain-electrical",
    "domain-civil-structural",
    "experiment-runner",
    "failure-analyst",
    "fair-play-reviewer",
    "writeup-author",
}


def frontmatter(path: Path) -> dict[str, Any]:
    _, head, _ = path.read_text().split("---\n", 2)
    data: dict[str, Any] = yaml.safe_load(head)
    return data


def test_agents_have_matching_frontmatter() -> None:
    files = {p.stem: p for p in (CLAUDE / "agents").glob("*.md")}
    assert set(files) == AGENTS
    for name, path in files.items():
        meta = frontmatter(path)
        assert meta["name"] == name
        assert meta["description"].startswith("Use ")
        assert "Read" in meta["tools"]


def test_firewall_analysts_are_real_agents() -> None:
    spec = importlib.util.spec_from_file_location("guard", CLAUDE / "hooks" / "guard.py")
    assert spec is not None and spec.loader is not None
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    assert guard.ANALYSTS <= AGENTS


def test_reviewer_cannot_edit() -> None:
    tools = frontmatter(CLAUDE / "agents" / "fair-play-reviewer.md")["tools"]
    assert "Edit" not in tools and "Write" not in tools


SKILLS = {
    "ple-handover",
    "ple-experiment-ledger",
    "ple-fair-play-review",
    "ple-kit-checks",
    "ple-runtime-skill-authoring",
}


def test_skills_have_matching_frontmatter() -> None:
    dirs = {p.parent.name: p for p in (CLAUDE / "skills").glob("*/SKILL.md")}
    assert set(dirs) == SKILLS
    for name, path in dirs.items():
        meta = frontmatter(path)
        assert meta["name"] == name
        assert meta["description"].startswith("Use ")


def test_templates_exist() -> None:
    assert (ROOT / "docs" / "handover" / "TEMPLATE.md").is_file()
    assert (ROOT / "docs" / "adr" / "0000-template.md").is_file()


def test_ci_runs_make_check() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "check.yml").read_text())
    steps = workflow["jobs"]["check"]["steps"]
    assert any(step.get("run") == "make check" for step in steps)
