"""Unit and CLI tests for ``specify feature``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def test_feature_init_defaults_to_docs_specs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """When specs/ does not exist, feature init creates docs/specs/001-<name>."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["feature", "init", "user-auth"])
    assert result.exit_code == 0

    feature_dir = tmp_path / "docs" / "specs" / "001-user-auth"
    assert feature_dir.is_dir()

    spec_file = feature_dir / "spec.md"
    assert spec_file.is_file()
    assert "# Feature Specification:" in spec_file.read_text(encoding="utf-8")

    feature_json = tmp_path / ".specify" / "feature.json"
    assert feature_json.is_file()
    data = json.loads(feature_json.read_text(encoding="utf-8"))
    assert data["feature_directory"] == "docs/specs/001-user-auth"


def test_feature_init_uses_specs_if_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """When specs/ exists in project root, feature init uses specs/."""
    specs_legacy = tmp_path / "specs"
    specs_legacy.mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["feature", "init", "billing-portal"])
    assert result.exit_code == 0

    feature_dir = tmp_path / "specs" / "001-billing-portal"
    assert feature_dir.is_dir()
    assert (feature_dir / "spec.md").is_file()

    data = json.loads((tmp_path / ".specify" / "feature.json").read_text(encoding="utf-8"))
    assert data["feature_directory"] == "specs/001-billing-portal"


def test_feature_init_sequential_prefixes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature init increments sequential 3-digit prefixes."""
    monkeypatch.chdir(tmp_path)

    # First feature: 001
    res1 = runner.invoke(app, ["feature", "init", "first-feature"])
    assert res1.exit_code == 0
    assert (tmp_path / "docs" / "specs" / "001-first-feature").is_dir()

    # Second feature: 002
    res2 = runner.invoke(app, ["feature", "init", "second-feature"])
    assert res2.exit_code == 0
    assert (tmp_path / "docs" / "specs" / "002-second-feature").is_dir()

    # Third feature: 003
    res3 = runner.invoke(app, ["feature", "init", "third-feature"])
    assert res3.exit_code == 0
    assert (tmp_path / "docs" / "specs" / "003-third-feature").is_dir()

    # Active feature is the last one
    current_res = runner.invoke(app, ["feature", "current"])
    assert current_res.exit_code == 0
    assert "docs/specs/003-third-feature" in current_res.output


def test_feature_init_ignores_timestamp_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature init numbering ignores existing timestamp-style directories."""
    specs_dir = tmp_path / "docs" / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "20261101-120000-timestamped-feat").mkdir()
    (specs_dir / "001-existing-feature").mkdir()

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["feature", "init", "new-feature"])
    assert result.exit_code == 0
    assert (specs_dir / "002-new-feature").is_dir()


def test_feature_init_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature init --json emits complete structured metadata."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["feature", "init", "oauth-login", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["feature_prefix"] == "001"
    assert data["feature_name"] == "oauth-login"
    assert data["feature_directory"] == "docs/specs/001-oauth-login"
    assert data["spec_file"] == "docs/specs/001-oauth-login/spec.md"


def test_feature_init_invalid_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature init rejects empty or invalid name."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["feature", "init", "???"])
    assert result.exit_code == 1
    assert "Error: Feature name cannot be empty" in result.output


def test_feature_current_no_feature_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature current fails gracefully when .specify/feature.json is missing."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["feature", "current"])
    assert result.exit_code == 1
    assert "Error: Not a Spec Kit project" in result.output


def test_feature_current_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature current --json outputs active feature directory."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "analytics"])
    result = runner.invoke(app, ["feature", "current", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["feature_directory"] == "docs/specs/001-analytics"


def test_feature_check_paths_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature check --json --paths-only returns paths even before plan.md exists."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "search-api"])
    result = runner.invoke(app, ["feature", "check", "--json", "--paths-only"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["BRANCH"] == "001-search-api"
    assert data["FEATURE_DIR"].endswith("docs/specs/001-search-api")
    assert data["FEATURE_SPEC"].endswith("docs/specs/001-search-api/spec.md")


def test_feature_check_prerequisites_and_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """feature check validates prerequisites and resolves optional template."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "search-api"])

    # Fails before plan.md exists
    res_no_plan = runner.invoke(app, ["feature", "check", "--json"])
    assert res_no_plan.exit_code == 1

    # Set up the plan; the agent writes the generated tasks
    runner.invoke(app, ["plan", "setup"])
    runner.invoke(app, ["tasks", "setup"])
    (tmp_path / "docs/specs/001-search-api/tasks.md").write_text("# Generated tasks\n")

    res_ok = runner.invoke(
        app,
        [
            "feature",
            "check",
            "--json",
            "--require-spec",
            "--require-tasks",
            "--include-tasks",
            "--template",
            "checklist-template",
        ],
    )
    assert res_ok.exit_code == 0
    data = json.loads(res_ok.output)
    assert "tasks.md" in data["AVAILABLE_DOCS"]
    assert "TEMPLATE_CONTENT" in data
    assert len(data["TEMPLATE_CONTENT"]) > 0

