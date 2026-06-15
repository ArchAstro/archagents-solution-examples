# ArchAgents Solution Examples

An open-source starter repo for managing **ArchAgents Solutions** —
deployable agent bundles (agent + tools + routines + skills + scripts) you
can install into your app with one command.

The intended workflow is to clone this repo into your organization's own
private GitHub repo, then use that private clone as the source of truth for
your proprietary solutions, collaborators, CI, and release tarballs. Keep
this public repo as the clean reference: copy patterns from the examples,
but put customer-specific agents, private integrations, and internal
workflow logic in your private clone.

Each solution lives under `solutions/<slug>/`. Browse the examples here,
copy the one closest to what you want, and tailor it in your private repo.

CI validates every solution on each change and cuts a versioned release
tarball per `version:` bump, so anything that lands on `main` is installable
with `archagent import solution`.
PR CI also requires existing solutions to bump `sample.yaml` `version:` when
their files change, so release automation cannot silently skip edited bytes.

> Working with Claude Code or another coding agent in this repo? It reads
> **`AGENTS.md`** (and the `CLAUDE.md` symlink) for the full authoring
> guide — point it there.
>
> Adding a solution yourself? Start with **[`ADDING_SOLUTIONS.md`](ADDING_SOLUTIONS.md)**.

## Prerequisites

Install the ArchAgents CLI and sign in:

```sh
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/ArchAstro/archagents/main/install.sh | bash
# or, with Homebrew
brew install ArchAstro/tools/archagent

archagent auth login
```

This puts the `archagent` binary on your PATH.

## Start a private solutions repo

Create a private repo for your organization, then push a clone of this
starter into it:

```sh
git clone https://github.com/ArchAstro/archagents-solution-examples.git my-org-solutions
cd my-org-solutions
git remote set-url origin https://github.com/<YourOrg>/<your-private-solutions-repo>.git
git push -u origin main --tags
```

After that, add your real solutions under `solutions/`, invite only the
people who should see those bundles, and let the included CI validate and
package releases for that private repo.

## The examples

| Solution | What it shows |
| --- | --- |
| [`hello-agent`](solutions/hello-agent/) | The **minimal** solution — just an agent with builtin tools. Start here. |
| [`osv-vuln-checker`](solutions/osv-vuln-checker/) | The **full-featured** solution — a custom tool, a cron routine, a skill, scripts, and a post-install setup checklist. |

Install one straight from this repo to try it:

```sh
archagent package solution solutions/hello-agent
archagent import  solution ./hello-agent-v0.1.1.tar.gz
```

## Add your own solution

In your private clone, each solution is an independent directory under
`solutions/`. CI picks up every one automatically — there's no central
registry to edit.

```sh
# 1. Scaffold a new solution (mints a stable solution_id for you)
archagent create solution my-solution \
  --name "My Solution" \
  --tagline "One line shown in the catalog." \
  --target-dir solutions

# 2. Edit solutions/my-solution/
#    - start from hello-agent for a minimal agent
#    - compare osv-vuln-checker for tools, scripts, routines, skills, and setup

# 3. Verify while iterating (run from the repo root)
archagent validate solution solutions/my-solution --schema-only
archagent lint     solution solutions/my-solution --strict

# 4. Run the full check, package, and smoke-test
archagent validate solution solutions/my-solution
archagent package  solution solutions/my-solution --output-dir dist
archagent import   solution dist/my-solution-v0.1.0.tar.gz
```

`validate --schema-only` and `lint` run fully offline; the full `validate`
and the import talk to the platform (sign in with `archagent auth login`).
See [`ADDING_SOLUTIONS.md`](ADDING_SOLUTIONS.md) for the checklist, wiring
rules, and release steps.

## Repository layout

```
.
├── README.md                  # this file
├── ADDING_SOLUTIONS.md        # human-facing checklist for new solutions
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
| **check-solution-version-bumps** | PRs touching `solutions/**` | Fails if an existing solution changed without a `sample.yaml` `version:` bump. |
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

MIT. See [`LICENSE`](LICENSE).
