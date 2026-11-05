"""Read-only defaults for workflows in bare projects."""
from __future__ import annotations

from pathlib import Path

from .._assets import _locate_bundled_workflow
from .._init_options import load_init_options


def bundled_workflow(root: Path, workflow_id: str) -> Path | None:
    if load_init_options(root).get("footprint") != "bare":
        return None
    from .catalog import WorkflowRegistry
    metadata = WorkflowRegistry(root).get(workflow_id)
    if metadata is not None:
        return None  # Registered overrides and disabled entries are authoritative.
    return _locate_bundled_workflow(workflow_id)
