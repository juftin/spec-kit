"""Tests for ``specify init --bare`` / ``--zero-footprint``."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def test_init_bare_flags(tmp_path: Path):
    """Test specify init my-proj --bare --integration copilot --non-interactive."""
    proj = tmp_path / "my-proj"

    result = runner.invoke(
        app,
        [
            "init",
            str(proj),
            "--bare",
            "--integration",
            "copilot",
            "--non-interactive",
        ],
    )
    assert result.exit_code == 0, f"Init failed with output:\n{result.output}"

    # Assert that .specify/scripts is NOT created
    assert not (proj / ".specify" / "scripts").exists()

    # Assert that .specify/templates is NOT created
    assert not (proj / ".specify" / "templates").exists()

    # Assert that .specify/workflows is NOT created
    assert not (proj / ".specify" / "workflows").exists()

    # Assert that .specify/init-options.json contains "footprint": "bare"
    init_opts_path = proj / ".specify" / "init-options.json"
    assert init_opts_path.is_file()
    opts = json.loads(init_opts_path.read_text(encoding="utf-8"))
    assert opts.get("footprint") == "bare"

    # Assert .specify/.gitignore is created
    assert (proj / ".specify" / ".gitignore").is_file()

    # Assert copilot agent prompt uses CLI invocation instead of shell script
    specify_skill = proj / ".github" / "skills" / "speckit-specify" / "SKILL.md"
    assert specify_skill.is_file()
    skill_content = specify_skill.read_text(encoding="utf-8")
    assert "specify template spec-template --json" in skill_content
    assert "scripts/bash/resolve-template.sh" not in skill_content


def test_init_zero_footprint_alias(tmp_path: Path):
    """Test specify init --zero-footprint works as an alias for --bare."""
    proj = tmp_path / "zf-proj"

    result = runner.invoke(
        app,
        [
            "init",
            str(proj),
            "--zero-footprint",
            "--integration",
            "copilot",
            "--non-interactive",
        ],
    )
    assert result.exit_code == 0, f"Init failed with output:\n{result.output}"

    assert not (proj / ".specify" / "scripts").exists()
    assert not (proj / ".specify" / "templates").exists()
    assert not (proj / ".specify" / "workflows").exists()

    opts = json.loads((proj / ".specify" / "init-options.json").read_text(encoding="utf-8"))
    assert opts.get("footprint") == "bare"


def test_init_bare_claude_skills(tmp_path: Path):
    """Test specify init --bare with Claude (skills agent)."""
    proj = tmp_path / "claude-proj"

    result = runner.invoke(
        app,
        [
            "init",
            str(proj),
            "--bare",
            "--integration",
            "claude",
            "--non-interactive",
        ],
    )
    assert result.exit_code == 0, f"Init failed with output:\n{result.output}"

    assert not (proj / ".specify" / "scripts").exists()
    assert not (proj / ".specify" / "templates").exists()
    assert not (proj / ".specify" / "workflows").exists()

    opts = json.loads((proj / ".specify" / "init-options.json").read_text(encoding="utf-8"))
    assert opts.get("footprint") == "bare"

    # Verify skill files were created and use CLI invocation
    plan_skill = proj / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
    assert plan_skill.is_file()
    skill_content = plan_skill.read_text(encoding="utf-8")
    assert "specify plan setup --json" in skill_content


def test_init_default_is_bare(tmp_path: Path):
    """Test specify init defaults to bare zero-footprint mode when --script is omitted."""
    proj = tmp_path / "default-bare-proj"

    result = runner.invoke(
        app,
        [
            "init",
            str(proj),
            "--integration",
            "copilot",
            "--non-interactive",
        ],
    )
    assert result.exit_code == 0, f"Init failed with output:\n{result.output}"

    assert not (proj / ".specify" / "scripts").exists()
    assert not (proj / ".specify" / "templates").exists()
    assert not (proj / ".specify" / "workflows").exists()

    opts = json.loads((proj / ".specify" / "init-options.json").read_text(encoding="utf-8"))
    assert opts.get("footprint") == "bare"

