# ArchAstro Solution Examples

A collection of ready-to-clone **ArchAstro Solutions** — deployable agent
bundles (agent + tools + routines + skills + scripts) you can install into
your app with one command. Each lives under `solutions/<slug>/`. Browse
them, copy the one closest to what you want, and tailor it.

CI validates every solution on each change and cuts a versioned release
tarball per `version:` bump, so anything that lands on `main` is installable
with `archagent import solution`.

> Working with Claude Code or another coding agent in this repo? It reads
> **`AGENTS.md`** (and the `CLAUDE.md` symlink) for the full authoring
> guide — point it there.

## Prerequisites

Install the ArchAstro CLI and sign in:

```sh
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/ArchAstro/archagents/main/install.sh | bash
# or, with Homebrew
brew install ArchAstro/tools/archagent

archagent auth login
```

This puts the `archagent` binary on your PATH.

## The examples

| Solution | What it shows |
| --- | --- |
| [`hello-agent`](solutions/hello-agent/) | The **minimal** solution — just an agent with builtin tools. Start here. |
| [`osv-vuln-checker`](solutions/osv-vuln-checker/) | The **full-featured** solution — a custom tool, a cron routine, a skill, scripts, and a post-install setup checklist. |

Install one straight from this repo to try it:

```sh
archagent package solution solutions/hello-agent
archagent import  solution ./hello-agent-v0.1.0.tar.gz
```

## Add your own solution

Each solution is an independent directory under `solutions/`. CI picks up
every one automatically — there's nothing to register.

```sh
# 1. Scaffold a new solution (mints a stable solution_id for you)
archagent create solution my-solution \
  --name "My Solution" \
  --tagline "One line shown in the catalog." \
  --target-dir solutions

# 2. Edit solutions/my-solution/ — see AGENTS.md for the full guide.

# 3. Verify (run from the repo root)
archagent validate solution solutions/my-solution    # schema + script check
archagent lint     solution solutions/my-solution --strict

# 4. Package + smoke-test
archagent package solution solutions/my-solution
archagent import  solution ./my-solution-v0.1.0.tar.gz
```

`validate --schema-only` and `lint` run fully offline; the full `validate`
and the import talk to the platform (sign in with `archagent auth login`).

## Repository layout

```
.
├── README.md                  # this file
├── AGENTS.md                  # authoring guide for coding agents
├── CLAUDE.md -> AGENTS.md      # symlink so Claude Code picks it up
├── .github/workflows/
│   ├── verify.yml             # PR + push: validate + lint + package EACH solution
│   └── release.yml            # push to main: package + GitHub Release per solution
└── solutions/
    ├── hello-agent/           # minimal example
    └── osv-vuln-checker/      # full-featured example
```

## CI

| Workflow | Trigger | What it does |
| --- | --- | --- |
| **verify** | PR + push to `main` | For **every** solution: `validate --schema-only` + `lint --strict` + `package`. No secrets required. |
| **release** | push to `main` | For every solution whose `version:` has no matching GitHub Release, packages it and cuts `<slug>-<version>.tar.gz`. Uses the default `GITHUB_TOKEN`. |

**To publish a new version of a solution:** bump `version:` in its
`sample.yaml` (and `solution_version:` in its `solution.yaml`) and merge to
`main`. `release.yml` cuts the release automatically — it's idempotent, so
versions already released are skipped and the other solutions are untouched.

### Optional: live script validation in CI

`verify.yml` includes an opt-in `validate-scripts` job that runs the
platform-backed `.aascript` check. It only runs if you set
`ARCHASTRO_CI_ACCESS_TOKEN`. To enable it, add these repository secrets
(from a service/CI account): `ARCHASTRO_CI_ACCESS_TOKEN`,
`ARCHASTRO_CI_REFRESH_TOKEN`, `ARCHASTRO_CI_APP_ID`, `ARCHASTRO_CI_ORG_ID`,
`ARCHASTRO_CI_ORG_NAME`, `ARCHASTRO_CI_USER_ID` — and optionally the
`ARCHASTRO_API_URL` variable.

## License

Provided as-is for building on ArchAstro. Replace this section with your own
license.
