"""Unit and CLI tests for SDD workflow commands: ``specify plan setup`` and ``specify tasks setup``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def test_plan_setup_no_active_feature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup exits with error 1 if no active feature is configured."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["plan", "setup"])
    assert result.exit_code == 1
    assert "Error: Not a Spec Kit project" in result.output


def test_plan_setup_missing_spec_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup exits with error 1 if spec.md is missing in the feature directory."""
    feature_dir = tmp_path / "docs" / "specs" / "001-test-feature"
    feature_dir.mkdir(parents=True)
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir(parents=True)
    (specify_dir / "feature.json").write_text(
        json.dumps({"feature_directory": "docs/specs/001-test-feature"}),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["plan", "setup"])
    assert result.exit_code == 1
    assert "Error: spec.md not found" in result.output


def test_plan_setup_creates_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup creates plan.md from template when spec.md exists."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "user-profile", "--number", "1"])

    result = runner.invoke(app, ["plan", "setup"])
    assert result.exit_code == 0

    plan_file = tmp_path / "docs" / "specs" / "001-user-profile" / "plan.md"
    assert plan_file.is_file()
    assert "# Implementation Plan:" in plan_file.read_text(encoding="utf-8")


def test_plan_setup_idempotent_no_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup does not overwrite existing plan.md."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "user-profile", "--number", "1"])
    runner.invoke(app, ["plan", "setup"])

    plan_file = tmp_path / "docs" / "specs" / "001-user-profile" / "plan.md"
    plan_file.write_text("# My Custom Existing Plan\n", encoding="utf-8")

    result = runner.invoke(app, ["plan", "setup"])
    assert result.exit_code == 0
    assert "FEATURE_DIR:" in result.output
    assert plan_file.read_text(encoding="utf-8") == "# My Custom Existing Plan\n"


def test_plan_setup_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup --json returns valid JSON metadata."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "notifications", "--number", "1"])

    result = runner.invoke(app, ["plan", "setup", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["feature_directory"] == "docs/specs/001-notifications"
    assert data["plan_file"] == "docs/specs/001-notifications/plan.md"
    assert data["created"] is True


def test_plan_setup_with_default_timestamp_feature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """plan setup works with default timestamp feature directories."""
    import re

    monkeypatch.chdir(tmp_path)
    res = runner.invoke(app, ["feature", "init", "live-feature", "--json"])
    assert res.exit_code == 0
    feat_data = json.loads(res.output)
    assert re.match(r"^\d{8}-\d{6}$", feat_data["feature_prefix"])

    result = runner.invoke(app, ["plan", "setup", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["feature_directory"] == feat_data["feature_directory"]
    assert data["plan_file"] == f"{feat_data['feature_directory']}/plan.md"


def test_tasks_setup_no_active_feature(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tasks setup exits with error 1 if no active feature is configured."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["tasks", "setup"])
    assert result.exit_code == 1
    assert "Error: Not a Spec Kit project" in result.output


def test_tasks_setup_missing_plan_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tasks setup exits with error 1 if plan.md is missing in the feature directory."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "payment-flow"])

    result = runner.invoke(app, ["tasks", "setup"])
    assert result.exit_code == 1
    assert "Error: plan.md not found" in result.output


def test_tasks_setup_returns_template_without_writing_tasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tasks setup leaves task creation to the agent."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "payment-flow", "--number", "1"])
    runner.invoke(app, ["plan", "setup"])

    result = runner.invoke(app, ["tasks", "setup"])
    assert result.exit_code == 0

    tasks_file = tmp_path / "docs" / "specs" / "001-payment-flow" / "tasks.md"
    assert not tasks_file.exists()
    assert "TASKS_TEMPLATE:" in result.output


def test_tasks_setup_idempotent_no_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tasks setup does not overwrite existing tasks.md."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "payment-flow", "--number", "1"])
    runner.invoke(app, ["plan", "setup"])
    runner.invoke(app, ["tasks", "setup"])

    tasks_file = tmp_path / "docs" / "specs" / "001-payment-flow" / "tasks.md"
    tasks_file.write_text("# My Custom Tasks\n", encoding="utf-8")

    result = runner.invoke(app, ["tasks", "setup"])
    assert result.exit_code == 0
    assert "FEATURE_DIR:" in result.output
    assert tasks_file.read_text(encoding="utf-8") == "# My Custom Tasks\n"


def test_tasks_setup_json_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tasks setup --json returns valid JSON metadata."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["feature", "init", "security-audit", "--number", "1"])
    runner.invoke(app, ["plan", "setup"])

    result = runner.invoke(app, ["tasks", "setup", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["feature_directory"] == "docs/specs/001-security-audit"
    assert data["tasks_file"] == "docs/specs/001-security-audit/tasks.md"
    assert data["created"] is False


def test_full_sdd_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """End-to-end SDD flow: feature init -> plan setup -> tasks setup."""
    monkeypatch.chdir(tmp_path)

    # 1. Feature init
    res_feat = runner.invoke(app, ["feature", "init", "shopping-cart", "--number", "1"])
    assert res_feat.exit_code == 0

    feat_dir = tmp_path / "docs" / "specs" / "001-shopping-cart"
    assert (feat_dir / "spec.md").is_file()

    # 2. Plan setup
    res_plan = runner.invoke(app, ["plan", "setup"])
    assert res_plan.exit_code == 0
    assert (feat_dir / "plan.md").is_file()

    # 3. Tasks setup
    res_tasks = runner.invoke(app, ["tasks", "setup"])
    assert res_tasks.exit_code == 0
    assert not (feat_dir / "tasks.md").exists()

    # 4. Verify feature current
    res_curr = runner.invoke(app, ["feature", "current"])
    assert res_curr.exit_code == 0
    assert "docs/specs/001-shopping-cart" in res_curr.output
