# Feature Specification: Drop-In Parity, Bare-Mode Completeness & Documentation Alignment

**Feature Branch**: `docs/drop-in-parity-spec`

**Created**: 2026-11-04

**Status**: Draft

**Input**: Audit of `juftin/spec-kit` zero-clone/bare-mode fork (`0a0dc522`) against upstream `github/spec-kit` (`7370e592`) for drop-in replacement completeness, correctness, and documentation accuracy.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Reliable Zero-Footprint SDD Parity & Clean CI (Priority: P1)

A developer installs `specify-cli` from this fork, initializes a repository in default bare mode (`specify init . --integration copilot`), and runs the full Spec-Driven Development lifecycle (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `implement`) from the repository root or any subdirectory—using sequential or timestamp feature numbering, Unicode feature names, or environment overrides (`SPECIFY_FEATURE_DIRECTORY`, `SPECIFY_FEATURE_NO_PERSIST`, `SPECIFY_FEATURE`)—with exact behavioral parity to upstream's helper scripts and green repository CI gates.

**Why this priority**: Core SDD commands (`specify feature`, `specify plan`, `specify tasks`, `specify template`) are the heart of the fork's zero-clone architecture, and broken lint gates block merges immediately.

**Independent Test**: Run `ruff`, `markdownlint-cli2`, and a parity test suite exercising `specify feature init|current|check`, `specify plan setup`, `specify tasks setup`, and `specify template` from both repo root and nested subdirectories against upstream script contracts ([`create_new_feature.py`](../../../scripts/python/create_new_feature.py), [`setup_plan.py`](../../../scripts/python/setup_plan.py), [`setup_tasks.py`](../../../scripts/python/setup_tasks.py), [`check_prerequisites.py`](../../../scripts/python/check_prerequisites.py)).

**Acceptance Scenarios**:

1. **Given** an active feature with `spec.md` and `plan.md` (and no `tasks.md`), **When** `specify tasks setup --json` runs, **Then** it verifies both `spec.md` and `plan.md` exist, does **not** pre-write a raw unfilled template to `tasks.md`, and emits `TASKS_TEMPLATE_CONTENT` plus the resolved `TASKS_TEMPLATE` source identifier.
2. **Given** a project initialized in bare mode and a terminal working directory inside `src/pkg/`, **When** `specify feature check --json` or `specify plan setup --json` runs without `SPECIFY_INIT_DIR`, **Then** it walks upward to discover `.specify/` at the repository root rather than failing or creating `src/pkg/.specify/`.
3. **Given** `SPECIFY_FEATURE_DIRECTORY=docs/specs/002-auth` and `SPECIFY_FEATURE_NO_PERSIST=1`, **When** `specify feature check --json` or `specify plan setup --json` runs, **Then** it targets `docs/specs/002-auth` without mutating `.specify/feature.json`.
4. **Given** `.specify/init-options.json` has `"feature_numbering": "timestamp"` (or `--timestamp` is passed), **When** `specify feature init user-auth` runs, **Then** it allocates `docs/specs/YYYYMMDD-HHMMSS-user-auth/spec.md` instead of `001-user-auth`.
5. **Given** an existing `docs/specs/001-user-auth/spec.md`, **When** `specify feature init` resolves to the same target without `--allow-existing-branch`, **Then** it exits non-zero with a clear collision error instead of overwriting `spec.md`.

---

### User Story 2 — Safe Global Agent Installation & Fork-Safe Self-Upgrade (Priority: P1)

A developer installs global agent skills via `specify integration install <agent> --global` (or upgrades `specify` via `specify self upgrade`) so they can run Spec Kit across any repository on their machine without clobbering their `$HOME` directory, rendering broken `.specify/scripts/...` paths, or replacing the fork with upstream `github/spec-kit`.

**Why this priority**: Global skills and `uv tool` installs are headline capabilities of this fork; currently `--global` emits broken script paths and `specify self upgrade` silently overwrites the fork with upstream.

**Independent Test**: Install, upgrade, and uninstall an integration with `--global` using a temporary `$HOME` (`monkeypatch.setenv("HOME", ...)`), inspect generated `SKILL.md` contents for `specify ...` CLI commands, verify SHA-256 manifest tracking, and run `specify self check`/`upgrade` against stubbed GitHub API endpoints.

**Acceptance Scenarios**:

1. **Given** a clean `$HOME`, **When** `specify integration install claude --global` runs, **Then** every generated `~/.claude/skills/speckit-*/SKILL.md` invokes `specify ...` CLI commands (never `.specify/scripts/...`) and records hashes in `~/.specify/integrations/claude.manifest.json`.
2. **Given** a globally installed integration, **When** `specify integration uninstall claude --global` or `specify integration upgrade claude --global` runs, **Then** unmodified managed files are cleanly removed or updated while user-modified files are preserved unless `--force` is passed.
3. **Given** an integration mode that writes workspace-specific settings outside a dedicated global skills/commands directory (e.g., `copilot --integration-options --commands` merging `.vscode/settings.json`), **When** `--global` is requested, **Then** the CLI refuses with an actionable error explaining which skills-based modes support `--global`.
4. **Given** `specify-cli` installed from `juftin/spec-kit`, **When** `specify self check` or `specify self upgrade` runs, **Then** it queries and upgrades from `juftin/spec-kit` (or `SPECIFY_UPGRADE_REPO` override) rather than `github/spec-kit`.

---

### User Story 3 — Bare-Mode Ecosystem Compatibility Across Presets, Extensions & Workflows (Priority: P2)

A developer in a default bare-initialized project installs presets (`specify preset add`), extensions (`specify extension add git`, `agent-context`, `github`), switches integrations (`specify integration use`), or executes `specify workflow run speckit`, and everything works seamlessly with bare mode and `docs/specs/`.

**Why this priority**: Upstream Spec Kit's value compounds through its workflow engine, presets, and bundled extensions; breaking them in default bare mode prevents drop-in adoption.

**Independent Test**: Initialize a bare project, add bundled presets and extensions, run `specify workflow list` and `specify workflow info speckit`, and verify registered skills/commands and extension scripts resolve `specify ...` CLI invocations and `docs/specs/` feature paths.

**Acceptance Scenarios**:

1. **Given** a bare project (`.specify/init-options.json` has `"footprint": "bare"`), **When** `specify preset add` or `specify extension add` registers skill or command templates, **Then** `CommandRegistrar` selects `scripts.cli` (or translates known core scripts to `specify ...` CLI commands) rather than `.specify/scripts/bash/...`.
2. **Given** a bare project with no `.specify/workflows/` directory on disk, **When** `specify workflow list` or `specify workflow run speckit` executes, **Then** the bundled `speckit` workflow resolves in memory from packaged assets without copying files into `.specify/workflows/`.
3. **Given** features stored under `docs/specs/001-auth/` (and no legacy `specs/` directory), **When** bundled `agent-context` or `git` extensions validate or scan feature directories, **Then** they check `docs/specs/` as well as legacy `specs/`.
4. **Given** a bare project with `presets/constitution-sync` enabled, **When** `/speckit-constitution` runs, **Then** it treats missing `.specify/templates/*.md` files as expected bare-mode in-memory templates rather than reporting sync errors.

---

### User Story 4 — Drift-Free Pre-Rendered Skills Catalog & Accurate Documentation (Priority: P2)

A user reading [`README.md`](../../../README.md) or `docs/` or installing skills via `npx skills add juftin/spec-kit -g` gets accurate, non-contradictory instructions and pre-rendered [`skills/`](../../../skills/speckit/SKILL.md) that are deterministically generated from `templates/commands/*.md` and verified in CI.

**Why this priority**: Hand-edited `skills/` will silently drift on upstream merges, and contradictory install docs cause users to accidentally install upstream `specify-cli` from PyPI instead of this fork.

**Independent Test**: Run the skills generator in `--check` mode inside pytest, run `markdownlint-cli2` across `README.md`, `docs/**/*.md`, and `skills/**/*.md`, and verify zero stale `github/spec-kit` install commands in fork-facing install/reference docs.

**Acceptance Scenarios**:

1. **Given** any change to `templates/commands/*.md`, **When** pytest runs, **Then** a contract test fails if `skills/speckit-*/SKILL.md` does not match the deterministic output of the generator.
2. **Given** [`docs/installation.md`](../../installation.md), [`docs/reference/core.md`](../../reference/core.md), and [`README.md`](../../../README.md), **When** a user follows any documented install or init path, **Then** bare vs `--scaffold` behavior, interactive prompt rules, `.specify/` metadata files vs `npx skills -g`, and repository URLs are 100% consistent.

---

### User Story 5 — Shared Operations & MCP Server Parity (Priority: P3)

An MCP-capable coding agent connected to `specify mcp` can invoke `template`, `feature` (`init`, `current`, `check`), `plan setup`, and `tasks setup` directly as typed MCP tools backed by the same Typer-free operation functions as the CLI.

**Why this priority**: Aligns fork additions with [`design/shared.md`](../../../design/shared.md), [`design/cli.md`](../../../design/cli.md), and [`design/mcp.md`](../../../design/mcp.md), giving zero-clone agents structured tool execution without shell quoting issues.

**Independent Test**: Exercise each shared operation directly in unit tests and over the stdio MCP server in `tests/specify_cli/mcp_server/`.

**Acceptance Scenarios**:

1. **Given** `specify mcp` running over stdio, **When** an MCP client lists tools and calls `specify_template` or `specify_feature_check`, **Then** it receives typed JSON matching the CLI contract with accurate read-only/mutating tool annotations.

---

### Edge Cases

- **Legacy vs Bare coexistence**: Repository already has `specs/001-legacy/` and user runs bare `specify feature init new-thing` — must continue allocating under `specs/002-new-thing` to preserve single-tree consistency.
- **Subdirectory invocation when uninitialized**: Running `specify feature init` inside a subdirectory when *no* ancestor has `.specify/` — `feature init` initializes at `SPECIFY_INIT_DIR` or `cwd` only if explicitly intended, while `feature check` / `plan setup` / `tasks setup` fail cleanly with `Not a Spec Kit project` rather than creating stray `.specify/` directories.
- **Corrupt `.specify/feature.json` or `preset.yml` / `extension.yml`**: Commands must fail closed with clean human stderr (or `{"error": ...}` on stderr when `--json` is active) and exit code `1`, never raw Python tracebacks.
- **Windows paths & PowerShell 5.1**: Preset/extension templates with `ps:`-only `check-prerequisites.ps1 -Json` variants must translate cleanly in bare mode, and JSON output must survive non-UTF-8 Windows codepages (`cp1252`).
- **244-byte Git/directory name limit & Unicode slugs**: Long or non-ASCII feature descriptions (e.g., CJK/accented characters) must preserve Unicode word characters and truncate cleanly on word/UTF-8 byte boundaries matching `create_new_feature.py`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All Python and Markdown files in the fork MUST pass CI lint gates (`uvx ruff@0.15.0 check src tests` and `markdownlint-cli2`).
- **FR-002**: `specify tasks setup` MUST verify that both `plan.md` and `spec.md` exist in the active feature directory, MUST NOT write raw template content to `tasks.md`, and MUST emit `TASKS_TEMPLATE_CONTENT` plus the resolved template source identifier in `TASKS_TEMPLATE`.
- **FR-003**: `specify plan setup` MUST reject empty resolved `plan-template` content and emit `FEATURE_SPEC`, `IMPL_PLAN`, `FEATURE_DIR`, and `BRANCH` in both `--json` and plain-text modes matching `setup_plan.py`.
- **FR-004**: Project-scoped SDD commands (`specify feature`, `specify plan`, `specify tasks`, `specify template`) MUST honor `SPECIFY_INIT_DIR` first and otherwise walk upward from `Path.cwd()` to locate `.specify/` (matching `common.py:find_specify_root`), enforcing symlink/file-policy checks via `_project.py`.
- **FR-005**: `specify feature` and `specify plan`/`tasks` MUST honor `SPECIFY_FEATURE_DIRECTORY`, `SPECIFY_FEATURE_NO_PERSIST`, and `SPECIFY_FEATURE` with the same precedence as `scripts/python/common.py`.
- **FR-006**: `specify feature init` MUST support sequential (`NNN-`) and timestamp (`YYYYMMDD-HHMMSS-`) numbering (via `.specify/init-options.json` `feature_numbering` and CLI flags `--timestamp`, `--number`, `--short-name`, `--dry-run`, `--allow-existing-branch`), preserve Unicode letters/digits in slugs, enforce the 244-byte name limit, and refuse to overwrite an existing `spec.md`.
- **FR-007**: `specify template` and SDD commands MUST catch `PresetError` / manifest validation errors and exit `1` with actionable error output (structured JSON on stderr when `--json` is passed).
- **FR-008**: `specify integration install --global` (`-g`) MUST pass `bare=True`, persist an `IntegrationManifest` under `~/.specify/integrations/<key>.manifest.json`, and reject integrations/modes whose writes escape dedicated agent skill/command folders in `$HOME`.
- **FR-009**: `specify integration uninstall` and `specify integration upgrade` MUST support `--global` (`-g`) using the global manifest with SHA-256 modification protection (`--force` to override).
- **FR-010**: `specify self check` and `specify self upgrade` MUST default to this fork's GitHub repository (`juftin/spec-kit`) with an environment override (`SPECIFY_UPGRADE_REPO`) for downstream forks/mirrors, and clearly indicate that PyPI `specify-cli` tracks upstream unless installed from Git.
- **FR-011**: `CommandRegistrar.resolve_skill_placeholders` (and command registration in `agents.py`) MUST detect `footprint == "bare"` in `.specify/init-options.json` and resolve `scripts.cli` (or bare script-to-CLI translation) when registering preset/extension commands and skills.
- **FR-012**: All `IntegrationBase` concrete subclasses (`MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, `SkillsIntegration`, `CopilotIntegration`) MUST forward `bare` to `process_template()`, and `process_template()` MUST handle `check-prerequisites.ps1` alongside `.sh` and `.py`.
- **FR-013**: `specify workflow` (`list`, `info`, `run`, `resolve`) MUST fall back to bundled workflows (e.g., `speckit`) in bare mode without requiring `.specify/workflows/speckit/workflow.yml` to be copied during `specify init`.
- **FR-014**: Bundled presets (`constitution-sync`) and extensions (`agent-context`, `git`) MUST support `docs/specs/` alongside legacy `specs/` and degrade cleanly when `.specify/scripts/` or `.specify/templates/` are absent in bare mode.
- **FR-015**: `skills/speckit-*/SKILL.md` (and `skills/speckit/SKILL.md`) MUST be generated deterministically from `templates/commands/*.md` via an internal generator module/script and verified by a pytest contract test so `npx skills` and `SkillsIntegration` never drift.
- **FR-016**: Fork documentation (`README.md`, `docs/installation.md`, `docs/reference/core.md`, `docs/quickstart.md`, `docs/integrations/cli.md`, `docs/upgrade.md`) MUST accurately document fork installation, bare vs `--scaffold` footprint, `.specify/` state files vs `npx skills -g`, interactive prompt behavior, and CLI flags without contradictory PyPI/upstream instructions.
- **FR-017**: Core SDD business logic MUST live in Typer-free operation modules (`_operation_*.py` / domain helpers) shared by CLI handlers and (if enabled) MCP server tools, while keeping edits to existing upstream files minimal to preserve low-conflict upstream merges.

### Key Entities

- **Project Footprint (`bare` | `scaffold`)**: Stored in `.specify/init-options.json` (`footprint: "bare"` when helper scripts/templates/workflows are resolved in memory rather than copied to `.specify/`).
- **Active Feature Context**: Resolved from `SPECIFY_FEATURE_DIRECTORY` env var -> `.specify/feature.json` (`feature_directory`), pointing to either `docs/specs/<id>/` (default) or `specs/<id>/` (legacy fallback).
- **Global Integration Manifest**: `~/.specify/integrations/<agent>.manifest.json` tracking SHA-256 hashes of globally installed skill/command files relative to `$HOME`.
- **Bundled Asset Resolver**: Unified resolution chain (`PresetResolver` + `WorkflowEngine` bundled fallback) serving templates and workflows from project overrides -> presets -> extensions -> packaged wheel assets.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `uvx ruff@0.15.0 check src tests` and `npx markdownlint-cli2` exit `0` with zero warnings/errors across all modified and added files.
- **SC-002**: 100% of existing upstream pytest suites plus new parity tests pass under `.venv/bin/python -m pytest -n 0` on Linux, macOS, and Windows (Python 3.11–3.13).
- **SC-003**: Behavioral parity tests confirm identical JSON keys, exit codes, and filesystem side effects between `specify feature|plan|tasks|template` and upstream `scripts/python/{create_new_feature,check_prerequisites,setup_plan,setup_tasks,resolve_template}.py` across root, subdirectory, env-override, and timestamp-numbering scenarios.
- **SC-004**: Globally installed skills (`specify integration install <agent> --global` and `npx skills add juftin/spec-kit -g`) contain zero references to `.specify/scripts/` and pass round-trip install -> upgrade -> uninstall verification without touching unrelated `$HOME` dotfiles.
- **SC-005**: `specify workflow list` and `specify preset add` / `specify extension add` succeed in a freshly `specify init` (bare) project without manual `--scaffold` fallback.
- **SC-006**: Upstream merge footprint on existing upstream Python modules remains surgical (isolated new modules + small guard hooks in upstream files).

---

## Assumptions

- Minimizing line churn in existing upstream files remains a first-class constraint so `git merge upstream/main` stays nearly conflict-free.
- This fork is distributed via Git (`git+https://github.com/juftin/spec-kit.git`) and `npx skills add juftin/spec-kit -g`, **not** published under the upstream `specify-cli` name on PyPI.
- `.specify/` continues to hold lightweight JSON state (`init-options.json`, `integration.json`, `feature.json`, `integrations/*.manifest.json`, and `memory/constitution.md`) during project-local `specify init`; truly zero-repo-file usage is provided by `npx skills add -g` / `specify integration install --global` (and `SPECIFY_FEATURE_DIRECTORY` + `SPECIFY_FEATURE_NO_PERSIST=1`).
