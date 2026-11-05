"""Project and active-feature discovery shared by SDD entry points."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .._project import _resolve_init_dir_override_unrendered, preflight_project_policy


def read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def project_root(
    directory: Path | None = None, *, allow_uninitialized: bool = False
) -> Path:
    override = _resolve_init_dir_override_unrendered()
    if override is not None:
        return override
    cwd = (directory if directory is not None else Path.cwd()).resolve()
    for root in (cwd, *cwd.parents):
        if (root / ".specify").exists() or (root / ".specify").is_symlink():
            preflight_project_policy(root)
            return root
    if allow_uninitialized or os.environ.get("SPECIFY_FEATURE_DIRECTORY"):
        preflight_project_policy(cwd)
        return cwd
    raise ValueError("Not a Spec Kit project (no .specify/ directory)")


def safe_path(root: Path, value: str) -> Path:
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Feature path must stay inside the project: {value}")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing symlinked feature path: {parent}")
    return path.resolve()


def active_feature(root: Path) -> tuple[Path, str]:
    state_path = safe_path(root, ".specify/feature.json")
    override = os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    state = read_state(state_path)
    value = override or state.get("feature_directory")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "No active feature found in .specify/feature.json. Run 'specify feature init' first."
        )
    path = safe_path(root, value)
    relative = path.relative_to(root).as_posix()
    if override and os.environ.get("SPECIFY_FEATURE_NO_PERSIST", "") not in {
        "1",
        "true",
    }:
        if state.get("feature_directory") != relative:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state["feature_directory"] = relative
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path, relative


def branch(feature: Path) -> str:
    return os.environ.get("SPECIFY_FEATURE") or feature.name
