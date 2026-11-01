"""Unit and CLI tests for ``specify template``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetResolver

runner = CliRunner()


def test_preset_resolver_resolve_template_direct(tmp_path: Path):
    """PresetResolver.resolve_template resolves core templates in memory."""
    resolver = PresetResolver(tmp_path)
    spec_content = resolver.resolve_template("spec-template")
    assert spec_content is not None
    assert "# Feature Specification:" in spec_content

    # .md suffix stripped
    spec_md = resolver.resolve_template("spec-template.md")
    assert spec_md == spec_content

    # fallback to -template
    spec_short = resolver.resolve_template("spec")
    assert spec_short == spec_content

    # plan and tasks templates
    plan_content = resolver.resolve_template("plan-template")
    assert plan_content is not None
    assert "# Implementation Plan:" in plan_content

    tasks_content = resolver.resolve_template("tasks-template")
    assert tasks_content is not None
    assert "# Tasks:" in tasks_content

    # nonexistent
    assert resolver.resolve_template("non-existent-template-xyz") is None


def test_preset_resolver_resolve_template_override(tmp_path: Path):
    """PresetResolver.resolve_template respects project overrides."""
    override_dir = tmp_path / ".specify" / "templates" / "overrides"
    override_dir.mkdir(parents=True)
    custom_content = "# Custom Spec Template Override\n"
    (override_dir / "spec-template.md").write_text(custom_content, encoding="utf-8")

    resolver = PresetResolver(tmp_path)
    assert resolver.resolve_template("spec-template") == custom_content


def test_command_template_stdout_plain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """specify template <name> prints content directly to stdout."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["template", "spec-template"])
    assert result.exit_code == 0
    assert "# Feature Specification:" in result.output


def test_command_template_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """specify template <name> --json returns JSON with TEMPLATE_NAME and TEMPLATE_CONTENT."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["template", "plan-template", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["TEMPLATE_NAME"] == "plan-template"
    assert "# Implementation Plan:" in data["TEMPLATE_CONTENT"]


def test_command_template_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """specify template <missing> returns clean exit code 1 with error message."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["template", "non-existent-template-xyz"])
    assert result.exit_code == 1
    assert "Error: Template 'non-existent-template-xyz' not found" in result.output


def test_command_template_not_found_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """specify template <missing> --json also exits with code 1."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["template", "non-existent-template-xyz", "--json"])
    assert result.exit_code == 1
    assert "Error: Template 'non-existent-template-xyz' not found" in result.output


def test_command_template_with_init_dir_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """SPECIFY_INIT_DIR override is respected when resolving overrides."""
    other_dir = tmp_path / "custom_project"
    override_dir = other_dir / ".specify" / "templates" / "overrides"
    override_dir.mkdir(parents=True)
    (override_dir / "spec-template.md").write_text("# Project Custom Spec\n", encoding="utf-8")

    monkeypatch.setenv("SPECIFY_INIT_DIR", str(other_dir))
    result = runner.invoke(app, ["template", "spec-template"])
    assert result.exit_code == 0
    assert "# Project Custom Spec" in result.output
