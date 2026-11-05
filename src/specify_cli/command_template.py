"""CLI adapter for ``specify template``."""

from __future__ import annotations

import sys

import typer


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
    from .sdd._cli import invoke
    from .sdd._operations import template_resolve
    payload = invoke(template_resolve, json_output, name=name, raw=True)
    if not json_output:
        content = payload["TEMPLATE_CONTENT"]
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")


def register(app: typer.Typer) -> None:
    """Register ``specify template`` on the root application."""
    app.command("template")(template)
