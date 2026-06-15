---
name: osv-triage-playbook
description: The rubric for triaging a dependency vulnerability finding. Use whenever you get results back from query_osv or a dependency scan and need to decide whether a finding is noise, an easy fix, or something that needs a human. Trigger phrases include "triage this finding", "is this CVE a real risk", "what should I do about this vulnerability".
---

# OSV triage playbook

When you get a vulnerability finding back from `query_osv`, classify it into
exactly one of three outcomes. Don't leave findings in limbo.

## 1. Gather context first

For each finding, establish:

- **Direct or transitive?** Direct dependencies are higher priority.
- **Is the vulnerable function actually reachable** in how the package is
  used here? Many CVEs only affect code paths you don't touch.
- **Severity** — read the CVSS score and the advisory summary, not just
  the label.
- **Is a fixed version available?** Check the OSV `affected[].ranges` for
  the first patched version.
- **Has it already been handled?** `memory_recall` past decisions for this
  package + CVE before acting.

## 2. Pick exactly one outcome

### A — Noise (no action)

The finding does not represent real exposure: already patched, the
vulnerable function is unused, or it's a dev-only dependency with no
runtime reach. `memory_store` the decision and the reasoning so future
scans don't re-litigate it. Move on.

### B — Easy fix

A small, obvious, low-risk fix exists — almost always a patch-level bump to
an already-released fixed version, with no API changes. State the exact
upgrade (`name: from → to`) and the CVE it closes. (This starter doesn't
ship auto-PR tools; add a `create-pull-request` tool to wire that up — see
the template repo's README.)

### C — Needs a human

Anything that needs judgment: a major-version bump, a multi-file change, an
unclear blast radius, a package that must be replaced, or any case where
you're not confident. Write a concise escalation: the CVE, the package and
versions, why it matters here, and the recommended action. `memory_store`
that you've escalated it so you don't raise it again next week.

## Voice

Be specific and calm. Name the CVE and the package@version. Explain *why*
something is or isn't a real risk for this codebase. If a whole scan is
noise, say that in one sentence — don't manufacture work.
