# Hello Agent

The smallest valid ArchAgents Solution — a single agent with builtin tools,
no custom scripts or setup. The best starting point for a new solution.

```
hello-agent/
  sample.yaml         # one deploy_solution step
  solution.yaml       # catalog wrapper, one template
  agents/
    hello-agent.yaml   # the AgentTemplate (builtin tools only)
    hello-agent.md
```

## Try it

```sh
archagent validate solution solutions/hello-agent
archagent package  solution solutions/hello-agent
archagent import   solution ./hello-agent-v0.1.1.tar.gz
```

## Grow it

Add `tools/`, `routines/`, `skills/`, and `scripts/` directories, then wire
them into `solution.yaml` (`templates:`) and `sample.yaml` (`steps:`). The
`osv-vuln-checker` example in this repo shows every piece.
