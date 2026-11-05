"""SDD operations, independent of CLI presentation and transport."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from ._templates import SDDTemplateResolver as PresetResolver
from ._context import active_feature, branch, project_root, read_state, safe_path


def template_resolve(
    name: str, root: Path | None = None, *, project_directory: Path | None = None
) -> dict:
    resolver = PresetResolver(
        root or project_root(project_directory, allow_uninitialized=True)
    )
    content = resolver.resolve_template(name)
    if content is None:
        raise ValueError(f"Template '{name}' not found")
    return {"TEMPLATE_NAME": name, "TEMPLATE_CONTENT": content}


def available_docs(feature: Path, include_tasks: bool = False) -> list[str]:
    docs = [
        name for name in ("research.md", "data-model.md") if (feature / name).is_file()
    ]
    contracts = feature / "contracts"
    if contracts.is_dir() and any(contracts.iterdir()):
        docs.append("contracts/")
    for name in ("quickstart.md", "tasks.md") if include_tasks else ("quickstart.md",):
        if (feature / name).is_file():
            docs.append(name)
    return docs


def feature_current(*, project_directory: Path | None = None) -> dict:
    _, relative = active_feature(project_root(project_directory))
    return {"feature_directory": relative}


def feature_check(
    *,
    project_directory: Path | None = None,
    require_spec: bool = False,
    require_tasks: bool = False,
    include_tasks: bool = False,
    paths_only: bool = False,
    template: str | None = None,
) -> dict:
    root = project_root(project_directory)
    feature, _ = active_feature(root)
    if paths_only:
        return {
            "REPO_ROOT": str(root),
            "BRANCH": branch(feature),
            "FEATURE_DIR": str(feature),
            "FEATURE_SPEC": str(feature / "spec.md"),
            "IMPL_PLAN": str(feature / "plan.md"),
            "TASKS": str(feature / "tasks.md"),
        }
    required = (
        ["plan.md"]
        + (["spec.md"] if require_spec else [])
        + (["tasks.md"] if require_tasks else [])
    )
    for name in required:
        path = safe_path(root, str(feature / name))
        if not path.is_file() or (name == "plan.md" and path.stat().st_size == 0):
            raise ValueError(f"{name} not found or empty in {feature}")
    result = {
        "FEATURE_DIR": str(feature),
        "AVAILABLE_DOCS": available_docs(feature, include_tasks),
    }
    if template:
        result["TEMPLATE_CONTENT"] = template_resolve(template, root)[
            "TEMPLATE_CONTENT"
        ]
    return result


def feature_init(
    name: str,
    *,
    project_directory: Path | None = None,
    timestamp: bool = False,
    number: int | None = None,
    short_name: str | None = None,
    dry_run: bool = False,
    allow_existing_branch: bool = False,
) -> dict:
    root = project_root(project_directory, allow_uninitialized=True)
    slug = "".join(
        c if c.isalpha() or c.isdecimal() else "-"
        for c in (short_name or name).translate(
            str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
        )
    )
    slug = re.sub("-+", "-", slug).strip("-")
    if not slug:
        raise ValueError(
            "Feature name cannot be empty or contain only unsupported characters"
        )
    base = root / ("specs" if (root / "specs").is_dir() else "docs/specs")
    options = read_state(safe_path(root, ".specify/init-options.json"))
    if number is not None and not 0 <= number <= 9223372036854775807:
        raise ValueError("Feature number must be between 0 and 9223372036854775807")
    if timestamp and number is not None:
        raise ValueError("--timestamp and --number cannot be combined")
    if number is not None:
        prefix = f"{number:03d}"
    elif timestamp or options.get("feature_numbering") == "timestamp":
        prefix = datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        numbers = (
            [
                int(m.group(1))
                for p in base.iterdir()
                if p.is_dir()
                and (m := re.match(r"^(\d{3,})-", p.name))
                and not re.match(r"^\d{8}-\d{6}-", p.name)
            ]
            if base.is_dir()
            else []
        )
        prefix = f"{max(numbers, default=0) + 1:03d}"
    if prefix.isdigit() and int(prefix) > 9223372036854775807:
        raise ValueError("Feature number must be between 0 and 9223372036854775807")
    slug = (
        slug.encode("utf-8")[: 244 - len(prefix) - 1]
        .decode("utf-8", errors="ignore")
        .rstrip("-")
    )
    feature = safe_path(root, str(base / f"{prefix}-{slug}"))
    relative = feature.relative_to(root).as_posix()
    spec = safe_path(root, str(feature / "spec.md"))
    if spec.exists() or (feature.exists() and not allow_existing_branch):
        raise ValueError(f"Feature already exists; refusing to overwrite: {feature}")
    state_path = safe_path(root, ".specify/feature.json")
    state = read_state(state_path)
    content = template_resolve("spec-template", root)["TEMPLATE_CONTENT"]
    if not dry_run:
        feature.mkdir(parents=True, exist_ok=True)
        spec.write_text(content, encoding="utf-8")
        if os.environ.get("SPECIFY_FEATURE_NO_PERSIST", "").lower() not in {
            "1",
            "true",
        }:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state["feature_directory"] = relative
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return {
        "feature_prefix": prefix,
        "feature_name": slug,
        "feature_directory": relative,
        "spec_file": f"{relative}/spec.md",
    }


def plan_setup(*, project_directory: Path | None = None) -> dict:
    root = project_root(project_directory)
    feature, relative = active_feature(root)
    spec = safe_path(root, str(feature / "spec.md"))
    plan = safe_path(root, str(feature / "plan.md"))
    if not spec.is_file():
        raise ValueError(f"spec.md not found in {feature}")
    if plan.exists() and not plan.is_file():
        raise ValueError(f"plan.md is not a regular file in {feature}")
    created = not plan.exists()
    if created:
        content = template_resolve("plan-template", root)["TEMPLATE_CONTENT"]
        if not content.strip():
            raise ValueError("Resolved plan-template is empty")
        plan.write_text(content, encoding="utf-8")
    return {
        "feature_directory": relative,
        "spec_file": f"{relative}/spec.md",
        "plan_file": f"{relative}/plan.md",
        "created": created,
        "FEATURE_DIR": str(feature),
        "FEATURE_SPEC": str(spec),
        "IMPL_PLAN": str(plan),
        "BRANCH": branch(feature),
    }


def tasks_setup(*, project_directory: Path | None = None) -> dict:
    root = project_root(project_directory)
    feature, relative = active_feature(root)
    for name in ("plan.md", "spec.md"):
        if not safe_path(root, str(feature / name)).is_file():
            raise ValueError(f"{name} not found in {feature}")
    content = template_resolve("tasks-template", root)["TEMPLATE_CONTENT"]
    source = PresetResolver(root).resolve("tasks-template", template_type="template")
    return {
        "feature_directory": relative,
        "plan_file": f"{relative}/plan.md",
        "tasks_file": f"{relative}/tasks.md",
        "created": False,
        "FEATURE_DIR": str(feature),
        "IMPL_PLAN": str(feature / "plan.md"),
        "TASKS_FILE": str(feature / "tasks.md"),
        "AVAILABLE_DOCS": available_docs(feature),
        "TASKS_TEMPLATE": str(source) if source else "bundled:tasks-template",
        "TASKS_TEMPLATE_CONTENT": content,
    }
