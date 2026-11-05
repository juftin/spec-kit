"""CLI adapters for feature operations."""
from __future__ import annotations

import typer

from .sdd import _operations as operations
from .sdd._cli import invoke

feature_app = typer.Typer(name="feature", help="Manage feature specifications.", add_completion=False)


@feature_app.command("init")
def feature_init(
    name: str = typer.Argument(..., help="Feature description."),
    json_output: bool = typer.Option(False, "--json"),
    timestamp: bool = typer.Option(False, "--timestamp"),
    number: int | None = typer.Option(None, "--number"),
    short_name: str | None = typer.Option(None, "--short-name"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    allow_existing_branch: bool = typer.Option(False, "--allow-existing-branch"),
) -> None:
    invoke(operations.feature_init, json_output, name=name, timestamp=timestamp,
           number=number, short_name=short_name, dry_run=dry_run,
           allow_existing_branch=allow_existing_branch)


@feature_app.command("current")
def feature_current(json_output: bool = typer.Option(False, "--json")) -> None:
    result = invoke(operations.feature_current, json_output, raw=True)
    if not json_output:
        typer.echo(result["feature_directory"])


@feature_app.command("check")
def feature_check(
    json_output: bool = typer.Option(False, "--json"),
    require_spec: bool = typer.Option(False, "--require-spec"),
    require_tasks: bool = typer.Option(False, "--require-tasks"),
    include_tasks: bool = typer.Option(False, "--include-tasks"),
    paths_only: bool = typer.Option(False, "--paths-only"),
    template: str | None = typer.Option(None, "--template"),
) -> None:
    invoke(operations.feature_check, json_output, require_spec=require_spec,
           require_tasks=require_tasks, include_tasks=include_tasks,
           paths_only=paths_only, template=template)


def register(app: typer.Typer) -> None:
    app.add_typer(feature_app, name="feature")
