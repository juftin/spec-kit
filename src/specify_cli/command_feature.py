"""CLI adapter for ``specify feature``."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import typer

from ._console import console
from ._project import _resolve_init_dir_override
from .presets import PresetResolver

feature_app = typer.Typer(
    name="feature",
    help="Manage feature specifications.",
    add_completion=False,
)


def _resolve_project_root() -> Path:
    override = _resolve_init_dir_override()
    return override if override is not None else Path.cwd()


def _resolve_specs_base(project_root: Path) -> tuple[Path, Path]:
    """Return (absolute_specs_dir, relative_specs_dir).

    If `specs/` exists at the project root, use it; otherwise default to `docs/specs/`.
    """
    specs_legacy = project_root / "specs"
    if specs_legacy.is_dir():
        return specs_legacy, Path("specs")
    return project_root / "docs" / "specs", Path("docs/specs")


def _get_next_prefix(specs_dir: Path) -> str:
    """Scan existing NNN-<name> directories and return next sequential 3-digit prefix."""
    highest = 0
    if specs_dir.is_dir():
        for entry in specs_dir.iterdir():
            if not entry.is_dir():
                continue
            # Match sequential prefix NNN- (>=3 digits), skip timestamp format YYYYMMDD-HHMMSS-
            m = re.match(r"^([0-9]{3,})-", entry.name)
            if m and not re.match(r"^[0-9]{8}-[0-9]{6}-", entry.name):
                try:
                    num = int(m.group(1), 10)
                    highest = max(highest, num)
                except ValueError:
                    pass
    return f"{highest + 1:03d}"


def _clean_feature_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not cleaned:
        typer.echo(
            "Error: Feature name cannot be empty or contain only unsupported characters",
            err=True,
        )
        raise typer.Exit(1)
    return cleaned


@feature_app.command("init")
def feature_init(
    name: str = typer.Argument(
        ...,
        help="Feature name (e.g. user-auth, billing-portal).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit feature metadata as JSON.",
    ),
) -> None:
    """Initialize a new feature directory with spec.md and activate it."""
    project_root = _resolve_project_root()
    cleaned_name = _clean_feature_name(name)
    specs_dir, specs_dir_rel = _resolve_specs_base(project_root)

    prefix = _get_next_prefix(specs_dir)
    dir_name = f"{prefix}-{cleaned_name}"
    feature_dir = specs_dir / dir_name
    feature_dir_rel = specs_dir_rel / dir_name
    feature_dir.mkdir(parents=True, exist_ok=True)

    resolver = PresetResolver(project_root)
    spec_content = resolver.resolve_template("spec-template")
    if spec_content is None:
        typer.echo("Error: Could not resolve spec-template", err=True)
        raise typer.Exit(1)

    spec_file = feature_dir / "spec.md"
    spec_file.write_text(spec_content, encoding="utf-8")

    # Update/write .specify/feature.json
    specify_dir = project_root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    feature_json_path = specify_dir / "feature.json"
    feature_data: dict[str, Any] = {}
    if feature_json_path.is_file():
        try:
            loaded = json.loads(feature_json_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                feature_data = loaded
        except Exception:
            pass

    relative_dir_str = feature_dir_rel.as_posix()
    feature_data["feature_directory"] = relative_dir_str
    feature_json_path.write_text(json.dumps(feature_data, indent=2) + "\n", encoding="utf-8")

    spec_file_rel = (feature_dir_rel / "spec.md").as_posix()
    if json_output:
        payload = {
            "feature_prefix": prefix,
            "feature_name": cleaned_name,
            "feature_directory": relative_dir_str,
            "spec_file": spec_file_rel,
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(f"Created feature {prefix}-{cleaned_name} in {relative_dir_str}")


@feature_app.command("current")
def feature_current(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit active feature directory as JSON.",
    ),
) -> None:
    """Print the currently active feature directory."""
    project_root = _resolve_project_root()
    feature_json_path = project_root / ".specify" / "feature.json"
    feature_dir: str | None = None
    if feature_json_path.is_file():
        try:
            data = json.loads(feature_json_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                feature_dir = data.get("feature_directory")
        except Exception:
            pass

    if not feature_dir:
        typer.echo("Error: No active feature found in .specify/feature.json", err=True)
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps({"feature_directory": feature_dir}, indent=2))
    else:
        typer.echo(feature_dir)


def _available_docs(feature_dir: Path, include_tasks: bool = False) -> list[str]:
    docs: list[str] = []
    if (feature_dir / "research.md").is_file():
        docs.append("research.md")
    if (feature_dir / "data-model.md").is_file():
        docs.append("data-model.md")
    contracts_dir = feature_dir / "contracts"
    try:
        if contracts_dir.is_dir() and any(contracts_dir.iterdir()):
            docs.append("contracts/")
    except OSError:
        pass
    if (feature_dir / "quickstart.md").is_file():
        docs.append("quickstart.md")
    if include_tasks and (feature_dir / "tasks.md").is_file():
        docs.append("tasks.md")
    return docs


@feature_app.command("check")
def feature_check(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output prerequisite check results as JSON.",
    ),
    require_spec: bool = typer.Option(
        False,
        "--require-spec",
        help="Require spec.md to exist.",
    ),
    require_tasks: bool = typer.Option(
        False,
        "--require-tasks",
        help="Require tasks.md to exist.",
    ),
    include_tasks: bool = typer.Option(
        False,
        "--include-tasks",
        help="Include tasks.md in AVAILABLE_DOCS list.",
    ),
    paths_only: bool = typer.Option(
        False,
        "--paths-only",
        help="Only output path variables without validating prerequisites.",
    ),
    template: str | None = typer.Option(
        None,
        "--template",
        help="Include composed template content in JSON output.",
    ),
) -> None:
    """Validate feature prerequisites and output feature paths and available documents."""
    project_root = _resolve_project_root()
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
        typer.echo("Error: No active feature found in .specify/feature.json", err=True)
        raise typer.Exit(1)

    feature_dir = (project_root / feature_dir_rel_str).resolve()
    spec_file = feature_dir / "spec.md"
    plan_file = feature_dir / "plan.md"
    tasks_file = feature_dir / "tasks.md"

    if paths_only:
        payload = {
            "REPO_ROOT": str(project_root.resolve()),
            "BRANCH": feature_dir.name,
            "FEATURE_DIR": str(feature_dir),
            "FEATURE_SPEC": str(spec_file),
            "IMPL_PLAN": str(plan_file),
            "TASKS": str(tasks_file),
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2))
        else:
            for k, v in payload.items():
                typer.echo(f"{k}: {v}")
        return

    if not feature_dir.is_dir():
        typer.echo(f"Error: Feature directory not found: {feature_dir}", err=True)
        raise typer.Exit(1)

    if not plan_file.is_file() or plan_file.stat().st_size == 0:
        typer.echo(f"Error: plan.md not found or empty in {feature_dir}", err=True)
        raise typer.Exit(1)

    if require_spec and not spec_file.is_file():
        typer.echo(f"Error: spec.md not found in {feature_dir}", err=True)
        raise typer.Exit(1)

    if require_tasks and not tasks_file.is_file():
        typer.echo(f"Error: tasks.md not found in {feature_dir}", err=True)
        raise typer.Exit(1)

    docs = _available_docs(feature_dir, include_tasks=include_tasks)
    template_content: str | None = None
    if template:
        resolver = PresetResolver(project_root)
        template_content = resolver.resolve_template(template)
        if template_content is None:
            typer.echo(f"Error: Could not resolve template '{template}'", err=True)
            raise typer.Exit(1)

    if json_output:
        out: dict[str, Any] = {
            "FEATURE_DIR": str(feature_dir),
            "AVAILABLE_DOCS": docs,
        }
        if template is not None:
            out["TEMPLATE_CONTENT"] = template_content
        typer.echo(json.dumps(out, indent=2))
    else:
        typer.echo(f"FEATURE_DIR:{feature_dir}")
        typer.echo(f"AVAILABLE_DOCS: {', '.join(docs)}")


def register(app: typer.Typer) -> None:
    """Register feature commands on the parent application."""
    app.add_typer(feature_app, name="feature")
