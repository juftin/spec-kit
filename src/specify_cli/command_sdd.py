"""CLI adapters for SDD workflow commands: ``specify plan`` and ``specify tasks``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from ._console import console
from ._project import _resolve_init_dir_override
from .presets import PresetResolver

plan_app = typer.Typer(
    name="plan",
    help="Manage feature implementation plans.",
    add_completion=False,
)

tasks_app = typer.Typer(
    name="tasks",
    help="Manage feature task breakdowns.",
    add_completion=False,
)


def _resolve_project_root() -> Path:
    override = _resolve_init_dir_override()
    return override if override is not None else Path.cwd()


def _get_active_feature(project_root: Path) -> tuple[Path, str]:
    """Return (feature_dir, feature_dir_rel_str) from .specify/feature.json.

    Exits with error if .specify/feature.json or feature_directory is missing.
    """
    feature_json_path = project_root / ".specify" / "feature.json"
    feature_dir_rel_str: str | None = None
    if feature_json_path.is_file():
        try:
            data = json.loads(feature_json_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                feature_dir_rel_str = data.get("feature_directory")
        except Exception:
            pass

    if not feature_dir_rel_str:
        typer.echo(
            "Error: No active feature found in .specify/feature.json. Run 'specify feature init' first.",
            err=True,
        )
        raise typer.Exit(1)

    feature_dir = project_root / feature_dir_rel_str
    if not feature_dir.is_dir():
        typer.echo(f"Error: Feature directory '{feature_dir}' does not exist", err=True)
        raise typer.Exit(1)

    return feature_dir, feature_dir_rel_str


@plan_app.command("setup")
def plan_setup(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit plan setup metadata as JSON.",
    ),
) -> None:
    """Set up plan.md for the active feature from plan-template."""
    project_root = _resolve_project_root()
    feature_dir, feature_dir_rel_str = _get_active_feature(project_root)

    spec_file = feature_dir / "spec.md"
    if not spec_file.is_file():
        typer.echo(
            f"Error: spec.md not found in {feature_dir}. Create the spec first.",
            err=True,
        )
        raise typer.Exit(1)

    plan_file = feature_dir / "plan.md"
    created = False
    if not plan_file.is_file():
        resolver = PresetResolver(project_root)
        plan_content = resolver.resolve_template("plan-template")
        if plan_content is None:
            typer.echo("Error: Could not resolve plan-template", err=True)
            raise typer.Exit(1)
        plan_file.write_text(plan_content, encoding="utf-8")
        created = True

    spec_file_rel = (Path(feature_dir_rel_str) / "spec.md").as_posix()
    plan_file_rel = (Path(feature_dir_rel_str) / "plan.md").as_posix()

    if json_output:
        payload = {
            "feature_directory": feature_dir_rel_str,
            "spec_file": spec_file_rel,
            "plan_file": plan_file_rel,
            "created": created,
            "FEATURE_DIR": str(feature_dir),
            "FEATURE_SPEC": str(spec_file),
            "IMPL_PLAN": str(plan_file),
            "BRANCH": feature_dir.name,
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        if created:
            typer.echo(f"Created plan at {plan_file_rel}")
        else:
            typer.echo(f"Plan already exists at {plan_file_rel}, skipping template copy")


@tasks_app.command("setup")
def tasks_setup(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit tasks setup metadata as JSON.",
    ),
) -> None:
    """Set up tasks.md for the active feature from tasks-template."""
    project_root = _resolve_project_root()
    feature_dir, feature_dir_rel_str = _get_active_feature(project_root)

    plan_file = feature_dir / "plan.md"
    if not plan_file.is_file():
        typer.echo(
            f"Error: plan.md not found in {feature_dir}. Run 'specify plan setup' first.",
            err=True,
        )
        raise typer.Exit(1)

    resolver = PresetResolver(project_root)
    tasks_content = resolver.resolve_template("tasks-template")
    if tasks_content is None:
        typer.echo("Error: Could not resolve tasks-template", err=True)
        raise typer.Exit(1)

    tasks_file = feature_dir / "tasks.md"
    created = False
    if not tasks_file.is_file():
        tasks_file.write_text(tasks_content, encoding="utf-8")
        created = True

    plan_file_rel = (Path(feature_dir_rel_str) / "plan.md").as_posix()
    tasks_file_rel = (Path(feature_dir_rel_str) / "tasks.md").as_posix()

    if json_output:
        from .command_feature import _available_docs

        payload = {
            "feature_directory": feature_dir_rel_str,
            "plan_file": plan_file_rel,
            "tasks_file": tasks_file_rel,
            "created": created,
            "FEATURE_DIR": str(feature_dir),
            "IMPL_PLAN": str(plan_file),
            "TASKS_FILE": str(tasks_file),
            "AVAILABLE_DOCS": _available_docs(feature_dir, include_tasks=False),
            "TASKS_TEMPLATE": str(tasks_file),
            "TASKS_TEMPLATE_CONTENT": tasks_content,
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        if created:
            typer.echo(f"Created tasks at {tasks_file_rel}")
        else:
            typer.echo(f"Tasks already exists at {tasks_file_rel}, skipping template copy")


def register(app: typer.Typer) -> None:
    """Register plan and tasks commands on the parent application."""
    app.add_typer(plan_app, name="plan")
    app.add_typer(tasks_app, name="tasks")
