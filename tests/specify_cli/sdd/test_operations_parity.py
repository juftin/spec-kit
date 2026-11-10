"""SDD contracts, filesystem effects, and rejected input regression coverage."""

import json
import re

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.sdd import _operations as ops

runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ops.feature_init("auth", number=1)
    return tmp_path


def test_tasks_are_template_only(project):
    ops.plan_setup()
    result = runner.invoke(app, ["tasks", "setup", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    feature = project / "docs/specs/001-auth"
    assert not (feature / "tasks.md").exists()
    assert data["TASKS_TEMPLATE_CONTENT"].startswith("---")
    assert data["TASKS_TEMPLATE"] != str(feature / "tasks.md")
    (feature / "spec.md").unlink()
    assert runner.invoke(app, ["tasks", "setup", "--json"]).exit_code == 1


def test_nested_discovery_and_no_persist(project, monkeypatch):
    nested = project / "src/pkg"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", "docs/specs/001-auth")
    monkeypatch.setenv("SPECIFY_FEATURE_NO_PERSIST", "1")
    monkeypatch.setenv("SPECIFY_FEATURE", "override-branch")
    before = (project / ".specify/feature.json").read_bytes()
    assert ops.plan_setup()["BRANCH"] == "override-branch"
    assert ops.feature_check()["FEATURE_DIR"] == str(project / "docs/specs/001-auth")
    assert (project / ".specify/feature.json").read_bytes() == before
    assert not (nested / ".specify").exists()


def test_creation_options_and_collision(project, monkeypatch):
    result = ops.feature_init("é漢" * 150, number=7)
    assert len(result["feature_directory"].split("/")[-1].encode()) <= 244
    with pytest.raises(ValueError, match="already exists"):
        ops.feature_init("é漢" * 150, number=7, allow_existing_branch=True)
    before = sorted(project.rglob("*"))
    ops.feature_init("preview", dry_run=True)
    assert sorted(project.rglob("*")) == before
    with pytest.raises(ValueError, match="cannot be combined"):
        ops.feature_init("bad", timestamp=True, sequential=True)
    with pytest.raises(ValueError, match="cannot be combined"):
        ops.feature_init("bad", number=1, sequential=True)
    assert re.fullmatch(r"\d{8}-\d{6}", ops.feature_init("timed-default", dry_run=True)["feature_prefix"])
    assert ops.feature_init("seq-flag", sequential=True, dry_run=True)["feature_prefix"] == "008"
    monkeypatch.setenv("SPECIFY_FEATURE_NO_PERSIST", "true")
    state = (project / ".specify/feature.json").read_bytes()
    (project / ".specify/init-options.json").write_text(
        '{"feature_numbering":"sequential"}'
    )
    assert ops.feature_init("seq-opt")["feature_prefix"] == "008"
    (project / ".specify/init-options.json").write_text(
        '{"feature_numbering":"timestamp"}'
    )
    assert re.fullmatch(r"\d{8}-\d{6}", ops.feature_init("timed")["feature_prefix"])
    assert (project / ".specify/feature.json").read_bytes() == state


@pytest.mark.parametrize("value", ["../escape", "/tmp/outside"])
def test_escape_rejected(project, monkeypatch, value):
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", value)
    with pytest.raises(ValueError, match="inside"):
        ops.plan_setup()


def test_corrupt_state_has_json_error(project):
    (project / ".specify/feature.json").write_text("[]")
    result = runner.invoke(app, ["plan", "setup", "--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "JSON object" in json.loads(result.stderr)["error"]


def test_empty_plan_template_rejected(project, monkeypatch):
    monkeypatch.setattr(ops.PresetResolver, "resolve_template", lambda *a: "")
    with pytest.raises(ValueError, match="empty"):
        ops.plan_setup()
    assert not (project / "docs/specs/001-auth/plan.md").exists()


def test_uninitialized_checks_do_not_create_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for args in (["feature", "check"], ["plan", "setup"], ["tasks", "setup"]):
        result = runner.invoke(app, args + ["--json"])
        assert result.exit_code == 1
        assert "Not a Spec Kit project" in json.loads(result.stderr)["error"]
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "script, operation, keys",
    [
        (
            "setup_plan.py",
            ops.plan_setup,
            ("FEATURE_DIR", "FEATURE_SPEC", "IMPL_PLAN", "BRANCH"),
        ),
        (
            "setup_tasks.py",
            ops.tasks_setup,
            (
                "FEATURE_DIR",
                "AVAILABLE_DOCS",
                "TASKS_TEMPLATE",
                "TASKS_TEMPLATE_CONTENT",
            ),
        ),
        (
            "check_prerequisites.py",
            ops.feature_check,
            ("FEATURE_DIR", "AVAILABLE_DOCS"),
        ),
    ],
)
def test_script_json_parity(project, monkeypatch, script, operation, keys):
    import os
    import subprocess
    import sys
    from specify_cli._assets import _repo_root

    ops.plan_setup()
    overrides = project / ".specify/templates/overrides"
    overrides.mkdir(parents=True)
    (overrides / "tasks-template.md").write_text(
        ops.template_resolve("tasks-template")["TEMPLATE_CONTENT"]
    )
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project))
    result = subprocess.run(
        [sys.executable, str(_repo_root() / "scripts/python" / script), "--json"],
        cwd=project,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    expected = json.loads(result.stdout)
    actual = operation()
    assert {key: actual[key] for key in keys} == {key: expected[key] for key in keys}


def test_environment_feature_activates_unless_no_persist(project, monkeypatch):
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", "docs/specs/001-auth")
    (project / ".specify/feature.json").write_text("{}")
    ops.plan_setup()
    assert (
        json.loads((project / ".specify/feature.json").read_text())["feature_directory"]
        == "docs/specs/001-auth"
    )


def test_symlink_feature_is_rejected(project, monkeypatch):
    target = project / "docs/specs/001-auth"
    link = project / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks unavailable")
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", "linked")
    with pytest.raises(ValueError, match="symlinked"):
        ops.plan_setup()


@pytest.mark.parametrize("command", [["template", "spec-template"], ["plan", "setup"]])
def test_invalid_preset_is_json_failure(project, monkeypatch, command):
    pack = project / ".specify/presets/broken"
    pack.mkdir(parents=True)
    (pack / "preset.yml").write_text("schema_version: [invalid yaml")
    monkeypatch.setattr(
        ops.PresetResolver,
        "_get_all_presets_by_priority",
        lambda self: [("broken", {"enabled": True})],
    )
    result = runner.invoke(app, command + ["--json"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Invalid YAML" in json.loads(result.stderr)["error"]


@pytest.mark.parametrize("number", [-1, 9223372036854775808])
def test_invalid_feature_number_has_no_side_effects(project, number):
    before = sorted(project.rglob("*"))
    with pytest.raises(ValueError, match="between"):
        ops.feature_init("invalid", number=number)
    assert sorted(project.rglob("*")) == before


def test_number_zero_and_short_name(project):
    result = ops.feature_init(
        "An ignored long description", number=0, short_name="CUSTOM_Name"
    )
    assert result["feature_directory"] == "docs/specs/000-custom-name"


def test_explicit_projects_do_not_change_process_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
        ops.feature_init(root.name, project_directory=root, number=1)
        ops.plan_setup(project_directory=root)
    from pathlib import Path

    assert Path.cwd() == tmp_path
    for root in roots:
        assert ops.feature_check(project_directory=root)["FEATURE_DIR"] == str(
            root / f"docs/specs/001-{root.name}"
        )


def test_timestamp_uses_local_clock_like_helper_scripts(project, monkeypatch):
    from datetime import datetime

    class LocalClock:
        @staticmethod
        def now():
            return datetime(2026, 11, 5, 12, 34, 56)

    monkeypatch.setattr(ops, "datetime", LocalClock)
    assert (
        ops.feature_init("local", timestamp=True)["feature_prefix"] == "20261105-123456"
    )
