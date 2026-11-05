"""Deterministically render the distributable skills catalog.

Run with ``python -m specify_cli.sdd._skills_catalog --write`` or ``--check``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from .._assets import _repo_root
from ..integrations.base import IntegrationBase, TomlIntegration

CLI_NOTE = (
    "> **Specify CLI Execution**: Install with "
    "`uv tool install specify-cli --from git+https://github.com/juftin/spec-kit.git` "
    "or run commands with `uvx --from git+https://github.com/juftin/spec-kit.git specify ...`. "
    "Features default to `docs/specs/`, with a fallback to existing `specs/`.\n\n"
)


def render_catalog(root: Path) -> dict[Path, str]:
    result = {}
    for source in sorted((root / "templates" / "commands").glob("*.md")):
        raw = source.read_text(encoding="utf-8")
        metadata, _ = TomlIntegration._split_frontmatter(raw)
        if isinstance(metadata, str):
            metadata = yaml.safe_load(metadata) or {}
        processed = IntegrationBase.process_template(
            raw, "claude", "sh", "$ARGUMENTS", bare=True
        )
        _, body = TomlIntegration._split_frontmatter(processed)
        header = {
            "name": f"speckit-{source.stem}",
            "description": metadata.get("description", ""),
            "compatibility": "Requires specify CLI; supports bare projects and global use",
            "metadata": {
                "author": "github-spec-kit",
                "source": f"templates/commands/{source.name}",
            },
        }
        content = (
            "---\n"
            + yaml.safe_dump(header, sort_keys=False, width=1000)
            + "---\n\n"
            + CLI_NOTE
            + body.lstrip()
        )
        result[Path("skills") / f"speckit-{source.stem}" / "SKILL.md"] = content
    result[Path("skills/speckit/SKILL.md")] = (
        root / "templates/skills/speckit.md"
    ).read_text(encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = _repo_root()
    stale = []
    expected = render_catalog(root)
    for relative, content in expected.items():
        path = root / relative
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        elif not path.is_file() or path.read_text(encoding="utf-8") != content:
            stale.append(str(relative))
    stale.extend(
        str(p.relative_to(root))
        for p in (root / "skills").glob("speckit*/SKILL.md")
        if p.relative_to(root) not in expected
    )
    if stale:
        print("Stale skills; regenerate with --write:\n" + "\n".join(stale))
    return int(bool(stale))


if __name__ == "__main__":
    raise SystemExit(main())
