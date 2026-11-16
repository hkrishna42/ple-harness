"""Checks that .claude/ config, CI and templates match what guard.py and the brief expect."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAUDE = ROOT / ".claude"


def test_settings_register_every_guard_event() -> None:
    hooks = json.loads((CLAUDE / "settings.json").read_text())["hooks"]
    expected = {"PreToolUse": "pre", "PostToolUse": "post", "SessionStart": "start", "Stop": "stop"}
    for event, arg in expected.items():
        commands = [h["command"] for group in hooks[event] for h in group["hooks"]]
        assert any(c.endswith(f'guard.py" {arg}') for c in commands), event
    pre_matcher = hooks["PreToolUse"][0]["matcher"]
    assert set(pre_matcher.split("|")) >= {"Read", "Write", "Edit", "Grep", "Glob", "Bash"}
