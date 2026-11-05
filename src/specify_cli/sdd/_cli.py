"""Presentation boundary for SDD CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .._project import ProjectResolutionError
from ..presets import PresetError


def invoke(operation, json_output: bool, *, raw: bool = False, **kwargs) -> dict:
    kwargs.setdefault("project_directory", Path.cwd())
    try:
        result = operation(**kwargs)
    except (ValueError, OSError, PresetError, ProjectResolutionError) as exc:
        typer.echo(
            json.dumps({"error": str(exc)}, ensure_ascii=True)
            if json_output
            else f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=True, indent=2))
    elif not raw:
        for key, value in result.items():
            typer.echo(f"{key}: {value}")
    return result
