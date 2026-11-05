"""CLI adapters for plan and task setup."""
from __future__ import annotations

import typer

from .sdd import _operations as operations
from .sdd._cli import invoke

plan_app = typer.Typer(name="plan", help="Manage feature implementation plans.", add_completion=False)
tasks_app = typer.Typer(name="tasks", help="Manage feature task breakdowns.", add_completion=False)


@plan_app.command("setup")
def plan_setup(json_output: bool = typer.Option(False, "--json")) -> None:
    result = invoke(operations.plan_setup, json_output, raw=True)
    if not json_output:
        if not result["created"]:
            typer.echo("Plan already exists, skipping template copy")
        for key in ("FEATURE_SPEC", "IMPL_PLAN", "FEATURE_DIR", "BRANCH"):
            typer.echo(f"{key}: {result[key]}")


@tasks_app.command("setup")
def tasks_setup(json_output: bool = typer.Option(False, "--json")) -> None:
    result = invoke(operations.tasks_setup, json_output, raw=True)
    if not json_output:
        for key in ("FEATURE_DIR", "TASKS_TEMPLATE", "AVAILABLE_DOCS"):
            typer.echo(f"{key}: {result[key]}")


def register(app: typer.Typer) -> None:
    app.add_typer(plan_app, name="plan")
    app.add_typer(tasks_app, name="tasks")
