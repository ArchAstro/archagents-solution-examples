# AGENTS.md — authoring ArchAstro Solutions

Guidance for coding agents (Claude Code, etc.) working in this repository.
`CLAUDE.md` is a symlink to this file.

This repo builds **ArchAstro Solutions**: deployable bundles that ship an
agent plus its custom tools, routines, skills, scripts, and a post-install
setup checklist. Each solution lives in `solutions/<slug>/`. CI validates
every solution and cuts a versioned release tarball per `version:` bump.

**The golden rule:** drive everything through the `archagent` CLI and let
the validator be your guide. After any edit, run `validate` then `lint` —
the error messages point at the exact file + field to fix. Never hand-edit
generated tarballs.

## The CLI

```sh
archagent create   solution <slug> --target-dir solutions [--name ...] [--tagline ...]
archagent validate solution <path> [--schema-only] [--scripts-only]
archagent lint     solution <path> [--strict]
archagent package  solution <path> [--output-dir <dir>]
archagent import   solution <path-or-tarball-or-catalog-slug>
archagent upgrade  solution <id-or-lookup-key> <new-tarball> [--dry-run]
```

- `validate` runs the **strict gate**: sample.yaml + solution.yaml schema,
  every template body, `lookup_key` uniqueness, all refs, and (unless
  `--schema-only`) a semantic check of every `.aascript` against the
  platform. `--schema-only` is fully offline.
- `lint` is the **best-practice gate** (advisory; `--strict` to fail on any
  warning): catalog `category_keys` / `tag_keys` / `description`, README
  coverage, per-template descriptions.
- `package` validates, then writes `<slug>-<version>.tar.gz`.

## Authoring loop

```sh
# 1. Scaffold (once). Mints a stable solution_id for you.
archagent create solution my-solution --target-dir solutions \
  --name "My Solution" --tagline "One line for the catalog."

# 2. Edit files (see "Anatomy" below). Then, repeatedly:
archagent validate solution solutions/my-solution --schema-only   # offline, fast
archagent lint     solution solutions/my-solution --strict

# 3. When green, run the full validate (checks scripts against the platform):
archagent validate solution solutions/my-solution                 # needs `archagent auth login`

# 4. Package + smoke-test by importing:
archagent package solution solutions/my-solution
archagent import  solution ./my-solution-v0.1.0.tar.gz
```

## Anatomy of a solution

```
solutions/<slug>/
  sample.yaml                # deploy steps + bundle version
  solution.yaml              # catalog wrapper: templates list, tags, readme
  agents/
    <slug>.yaml              # the deployable AgentTemplate (NO agent_key)
    <slug>.md                # its Library-inspector body (readme_path target)
  tools/                     # OPTIONAL custom tools
    <tool>.yaml              # AgentToolTemplate (display_name REQUIRED)
    <tool>.md
  routines/                  # OPTIONAL cron/event routines
    <routine>.yaml           # AgentRoutineTemplate (display_name REQUIRED)
    <routine>.md
  skills/                    # OPTIONAL instruction packages
    <skill-slug>/SKILL.md
  scripts/                   # .aascript tool + verifier implementations
  diagrams/architecture.svg
  env.example                # mirror every env var from setup_actions
  README.md
```

### `sample.yaml` — the deploy sequence

```yaml
schema_version: 2
version: v0.1.0                 # bump to cut a release
name: "My Solution"
tagline: "One line shown in the catalog."
min_cli_version: "0.28.0"
steps:
  - type: upload_scripts        # uploads scripts/*.aascript as Script configs
    source_dir: scripts
  - type: upload_skills         # uploads skills/<slug>/SKILL.md packages
    source_dir: skills
  - type: deploy_solution       # imports the catalog Solution wrapper
    solution_file: solution.yaml
```

**Steps DSL** (every `upload_*` must come before the `deploy_*` that uses it):

| Verb | Required | Optional | Purpose |
| --- | --- | --- | --- |
| `upload_scripts` | `source_dir` | `glob` | `.aascript` files → Script configs. Default glob `*.aascript`. lookup_key = filename stem. |
| `upload_skills` | `source_dir` | — | `skills/<slug>/SKILL.md` → Skill configs. lookup_key = the subdir name. |
| `upload_configs` | `source_dir` | `glob` | YAML/JSON configs of any `kind:`. Default glob `*.{yaml,yml,json}`. |
| `deploy_solution` | `solution_file` | — | Import the catalog Solution. **Exactly one** `deploy_solution` per sample. |

(`deploy_agent` / `upload_files` exist for non-solution agent bundles — not
used in this repo, which is solution-only.)

### `solution.yaml` — the catalog wrapper

```yaml
kind: Solution
lookup_key: my-solution-solution
solution_id: <uuid4>            # minted by `create solution` — KEEP STABLE
solution_version: v0.1.0        # match sample.yaml version
name: "My Solution"
description: "One-line catalog tagline."
category_keys: [sample]         # shelves the bundle in the Library carousel
tag_keys: [example]             # feeds the tag-filter picker
readme: |
  # ... inline markdown shown in the catalog inspector ...
  ![diagram](diagrams/architecture.svg)
assets:
  - asset_path: diagrams/architecture.svg
templates:
  # First entry is the deployable agent. readme_path is its inspector body.
  - template_path: agents/my-solution.yaml
    readme_path: agents/my-solution.md
  # Atomic tool/routine library rows (installable standalone).
  - template_path: tools/<tool>.yaml
    readme_path: tools/<tool>.md
  - template_path: routines/<routine>.yaml
    readme_path: routines/<routine>.md
metadata:
  sample_slug: my-solution
```

### Template kinds

| Kind | `name:` is | `display_name:` | Lives at |
| --- | --- | --- | --- |
| `AgentTemplate` | the catalog display name | not used | `agents/<slug>.yaml` |
| `AgentToolTemplate` | the snake_case tool function id | **REQUIRED** | `tools/<slug>.yaml` |
| `AgentRoutineTemplate` | the kebab-case routine handle | **REQUIRED** | `routines/<slug>.yaml` |

The deployable `AgentTemplate` references atomic tools/routines inline via
`template_path:` (the same files listed in `solution.yaml` `templates:`),
and builtin tools as inline literals:

```yaml
tools:
  - tool_type: builtin
    builtin_tool_key: knowledge_search
    status: active
  - template_path: tools/query-osv.yaml      # custom tool, also a library row
routines:
  - template_path: routines/weekly-scan.yaml
skills:
  - config_ref: osv-triage-playbook          # a skill from upload_skills
    status: active
```

### Scripts (`.aascript`)

A custom tool's implementation. `handler_type: script` + `config_ref:
<stem>` on the `AgentToolTemplate` wires it to `scripts/<stem>.aascript`.
The aascript language uses C-style syntax — note **`if (cond) { … } else {
… }` requires parentheses**. Run `archagent validate solution <path>` (full,
not `--schema-only`) to semantically check every script against the
platform before you ship.

### `setup_actions:` — the post-install checklist

Multi-template solutions declare setup on each template body via inline
`setup_actions:` (the `action_type:` discriminator). Each entry becomes one
row in the user's "Finish setup" panel.

```yaml
setup_actions:
  - action_type: env_var
    title: Set GITHUB_TOKEN
    description: |
      What it's for and how to get one.
    params: { key: GITHUB_TOKEN, scope: agent_env_var, secret: true }
    verify_config: { type: secret_present }
    dedupe_key: GITHUB_TOKEN        # shared across templates that need the same thing
    required: true
    sort_order: 0
  - action_type: install
    title: "Install: integration/github"
    params: { installation_kind: integration/github }
    verify_config: { type: installation_active }
    dedupe_key: integration/github
  - action_type: custom
    title: Verify access
    params: { id: verify-access }
    verify_config: { type: script_ref, script_ref: verify-access }  # must match a shipped script
    dedupe_key: verify-access
```

Mirror every `env_var` into `env.example`. A custom action's `script_ref`
is cross-checked at validate time — it must match the stem of a script
under an `upload_scripts` `source_dir`.

### Skills (`SKILL.md`)

```
skills/<skill-slug>/SKILL.md
```

```markdown
---
name: <skill-slug>
description: One line with trigger phrases — this is how the agent decides when to use it.
---

# Title

Markdown body: the instructions / rubric the agent follows.
```

Reference an uploaded skill from the agent with `skills: [{ config_ref:
<skill-slug>, status: active }]`.

## Rules the validator enforces (and how to satisfy them)

| Error | Fix |
| --- | --- |
| `wrapped template … declares agent_key` | Remove `agent_key:` from solution-mode template bodies. |
| `… (AgentToolTemplate) must declare a non-empty display_name` | Add `display_name: "Human Label"`. |
| `lookup_key '<x>' is used by two bundle artifacts` | A script and a tool share a stem. Prefix the template body's `lookup_key:` (e.g. `<slug>-tool-<x>`). |
| `verify.script_ref '<x>' doesn't match any script` | Ship `scripts/<x>.aascript`, or fix the ref. |
| `config_ref '<x>' does not match any lookup_key shipped` | The tool/skill ref points at nothing in the bundle — fix the ref or ship the artifact. |
| `solution.yaml missing or empty lookup_key` | Add `lookup_key:` (e.g. `<slug>-solution`). |
| `templates[N].readme_path … does not point at a real file` | Fix the path or add the `.md`. |
| `markdown ref … does not point at a real file` | A `![]( )` / `[]( )` points at a missing local file. External URLs are exempt. |
| `expected '(' after 'if'` (from the script sweep) | aascript needs `if (cond) { … }`. |
| `version must be a string like "v1.2.3"` | Both `sample.yaml.version` and `solution.yaml.solution_version` need the `v` prefix + three segments. |
| `lint: category_keys / tag_keys is empty` | Add at least one to `solution.yaml`. |

## Repo conventions

- One solution per `solutions/<slug>/`. `<slug>` is lowercase kebab-case.
- Keep `sample.yaml.version` and `solution.yaml.solution_version` in sync;
  bump both to release.
- Never change a published `solution_id` — it anchors every prior install.
- Don't commit real secrets. `env.example` holds placeholders only.
- Before opening a PR: `archagent validate solution <path>` and
  `archagent lint solution <path> --strict` both pass.
