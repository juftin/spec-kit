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
