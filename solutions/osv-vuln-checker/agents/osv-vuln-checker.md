# OSV Vulnerability Checker

A starter agent that watches your dependencies for known vulnerabilities
using the public [OSV.dev](https://osv.dev) database and triages what it
finds.

## What it does

- Runs a **weekly scan** of the packages you list in `MONITORED_PACKAGES`.
- Looks each one up against OSV.dev with the `query_osv` tool (no API key).
- Triages every finding with the `osv-triage-playbook` skill into one of
  three outcomes: **noise**, **easy fix**, or **needs a human**.
- Remembers its decisions so it doesn't re-flag the same finding weekly.
- Answers ad-hoc questions ("is lodash 4.17.20 safe?") when you @-mention it
  in a thread.

## Setup

| Requirement | Why |
| --- | --- |
| `MONITORED_PACKAGES` (env var) | The `ecosystem:name@version` list the weekly scan walks. |
| `NOTIFY_CHANNEL` (env var, optional) | Slack channel for the weekly summary. |

The post-install checklist also runs a one-time `verify-osv-reachable`
check to confirm the agent's runtime can reach OSV.dev.

## Tailoring it

This is a starting point. Common next steps:

- Add a `create-pull-request` tool so the agent can open auto-fix PRs for
  Outcome B findings (see the `security-triage-agent-sample` in the
  ArchAgents catalog for a worked example).
- Point the scan at a real lockfile instead of a hand-maintained list.
- Index your internal security policy in `knowledge_search` and have the
  playbook cite it when setting severity.
