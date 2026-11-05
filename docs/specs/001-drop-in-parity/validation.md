# Drop-In Parity Implementation Validation

Phases 1–4 are implemented. The optional MCP exposure phase remains deferred;
SDD operations accept an explicit project directory and keep CLI rendering out
of the domain layer so a future MCP adapter can reuse them.

## Implemented Behavior

- SDD commands discover ancestor projects, respect explicit project and feature
  overrides, validate manifest/state errors, and reject unsafe feature paths.
- Feature creation supports sequential and timestamp numbering, explicit numbers
  and short names, Unicode and UTF-8 byte limits, dry runs, and collision guards.
- Plan setup preserves existing plans and rejects empty templates. Tasks setup
  requires a spec and plan and returns the resolved template without creating
  an unfilled `tasks.md`.
- Global skills use bare rendering and persisted SHA-256 manifests. Upgrade and
  uninstall protect modified files; global command/workspace modes, unrelated
  manifest paths, and unmanaged skill collisions are rejected.
- Self-upgrade checks, installer arguments, and rollback hints use the fork or
  `SPECIFY_UPGRADE_REPO` override.
- Preset/extension rendering translates core Bash, Python, and PowerShell helper
  invocations in bare mode. Bundled workflows resolve without project copies,
  with registered entries and project overlays retaining precedence.
- Agent-context and Git extensions support `docs/specs/` and legacy `specs/`.
  The Git extension's bundled resolvers support bare `SPECIFY_INIT_DIR` use.
- The skills catalog is generated from command templates and an umbrella skill
  template, with pytest checking for drift. Documentation describes the fork's
  installation, bare metadata, global skills, and command contracts.

## Automated Checks

Use the worktree's own virtualenv. This host does not expose a system Python on
PATH, so shell parity tests also need the virtualenv's interpreter on PATH:

```bash
uv sync --extra test
export PATH="$PWD/.venv/bin:$PATH"
.venv/bin/python -m pytest -n 0 -q
uvx ruff@0.15.0 check src tests
npx --yes markdownlint-cli2 README.md "docs/**/*.md" "skills/**/*.md"
.venv/bin/python -m specify_cli.sdd._skills_catalog --check
```

The complete serial suite passed: **13,728 passed, 442 skipped** (14,170 tests),
with the repository's expected legacy/simulated-failure warnings. The final
local-clock regression was also validated in the operations module: **20 passed**.

Focused SDD, global lifecycle, catalog, and CLI checks passed: **67 tests**.
The integration rerun covering Git, GitHub, agent-context, SDD, global skills,
and catalog generation passed: **353 passed, 93 skipped**. Version/self-upgrade
checks passed: **226 passed, 5 skipped**.

Ruff, all CI documentation globs plus generated skills and changed command
prompts, catalog synchronization, and ShellCheck error-level checks passed.
Bash syntax checks passed for all changed shell scripts.

## Regression Evidence

A temporary source copy restored both original SDD CLI adapters from `HEAD`.
With an existing feature spec and plan, `tasks setup --json` succeeded but the
regression assertion failed with:

```text
AssertionError: tasks setup wrote an unfilled tasks.md
```

The same behavior is covered by
`tests/specify_cli/sdd/test_operations_parity.py::test_tasks_are_template_only`,
which passes with the implementation and also rejects a missing spec.
Additional positive/negative tests cover state corruption, manifest corruption,
subdirectories, environment persistence, UTF-8 limits, numbering, path escapes,
symlinks, global file preservation, unsafe global modes, bundled workflow
precedence, and script translation. Plan, tasks, and prerequisite JSON fields
are compared directly with the Python helper scripts.

## End-to-End Bare Smoke Test

A temporary project was initialized with Claude skills in default bare mode,
using `--non-interactive --ignore-agent-tools`. The test listed and inspected
the bundled `speckit` workflow, installed the local constitution-sync preset
and Git/agent-context extensions, created a feature, and ran plan/tasks setup
from `src/pkg/`. Every command succeeded. It verified that no helper scripts or
template scaffolds were copied by initialization, no nested `.specify/` was
created, no raw `tasks.md` was written, and installed skills contained no
`.specify/scripts/` invocations.

## Platform Limits

Validation ran on Linux with Python 3.15. Windows PowerShell 5.1 and the
Python 3.11–3.13 OS matrix were not executed in this environment.
The copied PowerShell project override resolver uses the existing core 5.1
implementation verbatim; the new scans use existing 5.1 cmdlets and string-array
paths. A dedicated execution check requires Windows PowerShell 5.1 and exercises
both success and failure paths:

```powershell
.venv\Scripts\python -m pytest -n 0 tests/extensions/test_bare_powershell51.py
```

It is skipped on this Linux host. Live coding-agent slash-command execution was
not performed; the smoke test exercises the actual CLI and generated skills.
