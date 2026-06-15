# Query OSV.dev

A standalone tool that looks up known vulnerabilities for a single package
version in the [OSV.dev](https://osv.dev) database.

- **No auth** — OSV.dev is a public API.
- **Inputs:** `package_name`, `ecosystem` (npm, PyPI, Hex, Go, crates.io,
  RubyGems, …), and the exact `version`.
- **Returns:** the raw OSV query response — the list of vulnerabilities
  affecting that version, each with its IDs, severity, and fixed versions.

Install this tool standalone and attach it to any agent, or deploy the full
**OSV Vulnerability Checker** agent that uses it on a schedule.
