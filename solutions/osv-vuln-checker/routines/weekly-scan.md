# Weekly Dependency Scan

A cron routine that scans your monitored packages against OSV.dev once a
week and triages anything it finds.

- **Schedule:** every Monday at 08:00 (`0 8 * * 1`).
- **Walks:** the `ecosystem:name@version` entries in `MONITORED_PACKAGES`.
- **Triages** each finding with the `osv-triage-playbook` skill and posts a
  short summary (to `NOTIFY_CHANNEL` if set).

Install it standalone on any agent that has the `query_osv` tool and the
`osv-triage-playbook` skill, or deploy the full **OSV Vulnerability
Checker** agent that bundles all three.
