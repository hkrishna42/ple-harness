"""Fair-play scan: no dev-task identifier may appear in run-time code (HANDOVER section 1.1).

The needles come from the kit's eval/dev_set.yaml at run time, so this repository never holds them.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCANNED = ("harness", "cost", "skills", "tools")


def kit_dir() -> Path:
    if os.environ.get("PLE_KIT_DIR"):
        return Path(os.environ["PLE_KIT_DIR"])
    common = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return Path(common).parent.parent / "ple"


def needles(dev_set: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    for task in dev_set["tasks"]:
        found.add(task["id"])
        found.add(task["title"].lower())
        if task.get("sha256"):
            found.add(task["sha256"])
        for path in task.get("deliverables", []):
            if not path.endswith("/"):  # a directory deliverable such as /app/output/ is generic
                found.add(path)
            found.update(part for part in path.strip("/").split("/")[:-1] if len(part) >= 12)
    return found


def find_leaks(roots: list[Path], needles: set[str]) -> list[str]:
    leaks = []
    for root in roots:
        for file in sorted(p for p in root.rglob("*") if p.is_file()):
            text = file.read_text(errors="ignore").lower()
            leaks += [f"{file}: {n}" for n in sorted(needles) if n.lower() in text]
    return leaks


def test_find_leaks_catches_a_planted_needle(tmp_path: Path) -> None:
    (tmp_path / "tool.py").write_text("CASE = 'Some-Task-Id'\n")
    assert find_leaks([tmp_path], {"some-task-id"}) == [f"{tmp_path / 'tool.py'}: some-task-id"]


def test_runtime_code_names_no_dev_task() -> None:
    dev_set_file = kit_dir() / "eval" / "dev_set.yaml"
    assert dev_set_file.is_file(), f"kit not found at {kit_dir()}: run `make kit`"
    dev_set = yaml.safe_load(dev_set_file.read_text())
    found = needles(dev_set)
    assert len(found) >= 29
    assert find_leaks([ROOT / d for d in SCANNED if (ROOT / d).is_dir()], found) == []
