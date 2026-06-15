# Adding Solutions

This repo is intentionally simple: every solution is a self-contained
directory under `solutions/<slug>/`. CI discovers any directory with a
`sample.yaml`, validates it, lints it, packages it, and releases a tarball
when its version changes.

Use this guide when adding another solution. Use `AGENTS.md` when you need
the full field-by-field reference.

## Start From The Right Example

| Starting point | Use it when |
| --- | --- |
| `solutions/hello-agent/` | You need the smallest valid solution: one agent, builtin tools, no custom scripts. |
| `solutions/osv-vuln-checker/` | You need custom tools, scripts, routines, skills, setup actions, assets, or env vars. |

Prefer scaffolding with the CLI instead of copying by hand. The CLI mints
a stable `solution_id`, which should not change after the solution ships.

```sh
archagent create solution my-solution \
  --name "My Solution" \
  --tagline "One line shown in the catalog." \
  --target-dir solutions
```

## Authoring Checklist

1. Pick a lowercase kebab-case slug, for example `dependency-auditor`.
2. Scaffold with `archagent create solution <slug> --target-dir solutions`.
3. Edit `sample.yaml`: confirm `version`, `name`, `tagline`,
   `min_cli_version`, and deploy `steps`.
4. Edit `solution.yaml`: keep `solution_id` stable, match
   `solution_version` to `sample.yaml`, set catalog tags, and list every
   template in `templates:`.
5. Edit `agents/<slug>.yaml`: define the agent identity, builtin tools,
   custom template references, skills, routines, installations, and any
   setup actions.
6. Add optional building blocks only when needed:
   - `tools/<tool>.yaml` and `.md` for custom tool library rows.
   - `routines/<routine>.yaml` and `.md` for standalone routines.
   - `skills/<skill-slug>/SKILL.md` for uploaded instruction packages.
   - `scripts/<script>.aascript` for tool handlers or setup verifiers.
   - `diagrams/` and `assets:` entries for catalog images.
   - `env.example` entries for every setup env var.
7. Run the validation commands below from the repo root.

## Wiring Rules

- `sample.yaml` must contain exactly one `deploy_solution` step.
- Every `upload_*` step must come before the `deploy_solution` step that
  depends on it.
- `sample.yaml.version` and `solution.yaml.solution_version` must match.
- Do not put `agent_key:` in solution-mode `AgentTemplate` files.
- The first `solution.yaml.templates` entry should be the deployable agent.
- If a tool or routine should be installable standalone, list it in
  `solution.yaml.templates` and reference the same file from the agent with
  `template_path:`.
- `AgentToolTemplate.name` is the snake_case LLM function id.
  `AgentToolTemplate.display_name` is required for the human label.
- `AgentRoutineTemplate.name` is the kebab-case routine handle.
  `AgentRoutineTemplate.display_name` is required for the human label.
- A script-backed tool uses `handler_type: script` and `config_ref:
  <script-stem>`, which must match `scripts/<script-stem>.aascript`.
- Avoid lookup key collisions. If a tool and script share a logical name,
  prefix the template `lookup_key`, for example `my-solution-tool-query`.
- Every setup `env_var` must also appear in `env.example` with a placeholder
  value, never a real secret.
- Every local Markdown link and image reference must point at a file that
  exists in the solution directory.

## Validate Before Opening A PR

Run the fast offline gate while iterating:

```sh
archagent validate solution solutions/my-solution --schema-only
archagent lint     solution solutions/my-solution --strict
```

When those pass, run the full checks and packaging smoke test:

```sh
archagent validate solution solutions/my-solution
archagent package  solution solutions/my-solution --output-dir dist
archagent import   solution dist/my-solution-v0.1.0.tar.gz
```

The full `validate` and `import` commands require platform credentials. If
you are not signed in yet, run:

```sh
archagent auth login
```

## Check Every Solution

Before a larger PR, run the same loop CI uses across the whole repo:

```sh
for sample in solutions/*/sample.yaml; do
  dir="$(dirname "$sample")"
  archagent validate solution "$dir" --schema-only
  archagent lint solution "$dir" --strict
  archagent package solution "$dir" --output-dir dist
done
```

CI also discovers solutions this way. There is no central registry file to
edit when you add `solutions/<slug>/`.

## Release A New Version

To publish a new tarball for an existing solution:

1. Bump `sample.yaml.version`, for example `v0.1.0` to `v0.1.1`.
2. Bump `solution.yaml.solution_version` to the exact same value.
3. Validate, lint, and package locally.
4. Merge to `main`.

The release workflow creates `<slug>-<version>.tar.gz` only when that
solution version has not already been released.

PR CI enforces this for existing solutions: if anything under
`solutions/<slug>/` changes and `sample.yaml.version` is unchanged compared
to the PR base branch, `check-solution-version-bumps` fails. New solutions
are skipped by that check because they have no previous version.
