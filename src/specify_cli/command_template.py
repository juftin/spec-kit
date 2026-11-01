"""CLI adapter for ``specify template``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ._project import _resolve_init_dir_override
from .presets import PresetResolver


def template(
    name: str = typer.Argument(
        ...,
        help="Template name to resolve (e.g. spec-template, plan-template, tasks-template).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit template output as JSON.",
    ),
) -> None:
    """Resolve and output a template from presets, extensions, or core pack."""
    project_root = _resolve_init_dir_override() or Path.cwd()
    resolver = PresetResolver(project_root)
    content = resolver.resolve_template(name)

    if content is None:
        typer.echo(f"Error: Template '{name}' not found", err=True)
        raise typer.Exit(1)

    if json_output:
        payload = {
            "TEMPLATE_NAME": name,
            "TEMPLATE_CONTENT": content,
        }
        typer.echo(json.dumps(payload, ensure_ascii=True))
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")


def register(app: typer.Typer) -> None:
    """Register ``specify template`` on the root application."""
    app.command("template")(template)
