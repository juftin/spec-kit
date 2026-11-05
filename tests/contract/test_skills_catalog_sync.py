"""The npx skills catalog must match the installed renderer's source templates."""

from specify_cli._assets import _repo_root
from specify_cli.sdd._skills_catalog import render_catalog


def test_skills_catalog_is_current():
    root = _repo_root()
    expected = render_catalog(root)
    assert set(expected) == {
        p.relative_to(root) for p in (root / "skills").glob("speckit*/SKILL.md")
    }
    for relative, content in expected.items():
        assert (root / relative).read_text(encoding="utf-8") == content, (
            f"Regenerate {relative} with python -m specify_cli.sdd._skills_catalog --write"
        )


def test_command_template_change_changes_catalog(tmp_path):
    commands = tmp_path / "templates/commands"
    commands.mkdir(parents=True)
    umbrella = tmp_path / "templates/skills"
    umbrella.mkdir()
    (umbrella / "speckit.md").write_text("guide")
    source = commands / "plan.md"
    source.write_text("---\ndescription: Planning\n---\nFirst\n")
    before = render_catalog(tmp_path)
    source.write_text("---\ndescription: Planning\n---\nChanged\n")
    assert render_catalog(tmp_path) != before
