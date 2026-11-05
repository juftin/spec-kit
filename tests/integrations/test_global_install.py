"""Tests for ``specify integration install --global``."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def test_global_install_claude(monkeypatch, tmp_path: Path):
    """Test specify integration install claude --global."""
    tmp_home = tmp_path / "fake_home"
    tmp_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_home)

    workdir = tmp_path / "empty_workdir"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    result = runner.invoke(app, ["integration", "install", "claude", "--global"])
    assert result.exit_code == 0, f"Global install failed with output:\n{result.output}"
    normalized_output = " ".join(result.output.split())
    assert f"Integration 'claude' installed globally in {tmp_home}" in normalized_output

    # Assert skills are written to tmp_home / ".claude" / "skills"
    skills_dir = tmp_home / ".claude" / "skills"
    assert skills_dir.is_dir()
    plan_skill = skills_dir / "speckit-plan" / "SKILL.md"
    assert plan_skill.is_file()
    specify_skill = skills_dir / "speckit-specify" / "SKILL.md"
    assert specify_skill.is_file()

    # Assert project-local .specify was not required or created
    assert not (workdir / ".specify").exists()


def test_global_install_short_flag(monkeypatch, tmp_path: Path):
    """Test specify integration install claude -g."""
    tmp_home = tmp_path / "fake_home_short"
    tmp_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_home)

    workdir = tmp_path / "empty_workdir_short"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    result = runner.invoke(app, ["integration", "install", "claude", "-g"])
    assert result.exit_code == 0, f"Global install failed with output:\n{result.output}"
    normalized_output = " ".join(result.output.split())
    assert f"Integration 'claude' installed globally in {tmp_home}" in normalized_output

    skills_dir = tmp_home / ".claude" / "skills"
    assert skills_dir.is_dir()
    assert (skills_dir / "speckit-plan" / "SKILL.md").is_file()
    assert not (workdir / ".specify").exists()


def test_global_manifest_roundtrip_and_modified_protection(tmp_path, monkeypatch):
    import hashlib
    import json
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    result = runner.invoke(app, ["integration", "install", "claude", "-g"])
    assert result.exit_code == 0, result.output
    path = home / ".specify/integrations/claude.manifest.json"
    data = json.loads(path.read_text())
    assert data["files"]
    skill = home / ".claude/skills/speckit-plan/SKILL.md"
    assert "specify plan setup --json" in skill.read_text()
    assert ".specify/scripts/" not in skill.read_text()
    assert hashlib.sha256(skill.read_bytes()).hexdigest() in str(data)
    skill.write_text("User edits")
    assert runner.invoke(app, ["integration", "upgrade", "claude", "-g"]).exit_code == 1
    assert skill.read_text() == "User edits"
    assert runner.invoke(app, ["integration", "upgrade", "claude", "-g", "--force"]).exit_code == 0
    skill.write_text("User edits")
    assert runner.invoke(app, ["integration", "uninstall", "claude", "-g"]).exit_code == 0
    assert skill.read_text() == "User edits"


def test_global_rejects_workspace_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = runner.invoke(app, ["integration", "install", "copilot", "-g", "--integration-options=--commands"])
    assert result.exit_code == 1
    assert "skills" in result.output
    assert not (tmp_path / ".vscode").exists()


def test_global_uninstall_rejects_forged_manifest_path(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert runner.invoke(app, ["integration", "install", "claude", "-g"]).exit_code == 0
    manifest = tmp_path / ".specify/integrations/claude.manifest.json"
    data = json.loads(manifest.read_text())
    unrelated = tmp_path / ".bashrc"
    unrelated.write_text("user configuration")
    data["files"][".bashrc"] = "forged"
    manifest.write_text(json.dumps(data))
    result = runner.invoke(app, ["integration", "uninstall", "claude", "-g", "--force"])
    assert result.exit_code == 1
    assert unrelated.read_text() == "user configuration"


def test_global_install_preserves_existing_unmanaged_skill(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    skill = tmp_path / ".claude/skills/speckit-plan/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("custom skill")
    result = runner.invoke(app, ["integration", "install", "claude", "-g"])
    assert result.exit_code == 1
    assert skill.read_text() == "custom skill"
    assert runner.invoke(app, ["integration", "install", "claude", "-g", "--force"]).exit_code == 0
    assert "specify plan setup" in skill.read_text()
