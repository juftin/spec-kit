<div align="center">
    <img src="https://raw.githubusercontent.com/github/spec-kit/main/media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Build with a spec, fix a bug, or assess an idea — with your coding agent.</em></h3>
</div>

Spec Kit is an open source toolkit that gives AI coding agents structured
processes, reusable templates, and documented outcomes. Start with a ready-made
process, customize it, or bring your own.

## juftin/spec-kit

This is a fork of [github/spec-kit](https://github.com/github/spec-kit) with two
changes to the default workflow:

1. **Install skills globally, once.** Use the same Spec Kit skills across your
   projects without installing skill files in every repository or running
   `specify init` for each project.
2. **Keep specs with your documentation.** New features default to
   `docs/specs/<feature>/` instead of a root `specs/` directory. Existing projects
   with a root `specs/` directory continue to use it.

Global installation adds no files to your repositories. When you use the skills,
the workflow creates your constitution, feature artifacts, and lightweight
`.specify/` metadata in the project. Helper scripts and templates are resolved
from the installed CLI.

## Quick Start

You'll need [uv](https://docs.astral.sh/uv/), Python 3.11+, Node.js for `npx`,
and a coding agent that supports skills.

### 1. Install the CLI with `uv`

Install this fork's `specify` CLI globally:

```bash
uv tool install specify-cli --from git+https://github.com/juftin/spec-kit.git
```

### 2. Install the skills globally

Install the pre-rendered skills into your coding agent's global skills directory:

```bash
npx skills add juftin/spec-kit -g
```

### 3. Get started in your project

Open your project in your coding agent. Run these commands in the agent's chat,
one at a time, reviewing each result before continuing.

Create your constitution once per project:

```console
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
```

Then describe and implement a feature:

```console
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
/speckit-tasks
/speckit-implement
/speckit-converge
```

Repeat implement and converge until convergence reports `Converged`.

<details>
<summary>The full path</summary>

```console
/speckit-specify
/speckit-clarify
/speckit-plan
/speckit-checklist
/speckit-tasks
/speckit-analyze
/speckit-implement
/speckit-converge
```

</details>

## What else?

The rest of the toolkit generally follows upstream. See the
[upstream README](https://github.com/github/spec-kit/blob/main/README.md) for the
broader capabilities and workflows, or the [fork's installation guide](docs/installation.md)
for project-local setup and other installation options.
