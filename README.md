# Maestro

> A multi-agent system for software engineering workflows, built on [Anthropic's agent best practices](https://www.anthropic.com/research/building-effective-agents).

Maestro is a structured framework for defining, composing, and operating specialized AI agents across the full software engineering lifecycle — from architecture through deployment. Agents are defined in **Markdown + YAML**, making them human-readable, version-controllable, and forkable as base templates for any team or domain.

---

## The Agent Pipeline

```
Requirements
     │
     ▼
┌─────────────────────────┐
│  System Design          │  Translates requirements into documented architecture:
│  Architect              │  ADRs, NFR baselines, component & data flow diagrams
└──────────┬──────────────┘
           │  approved design artifacts
     ┌─────┼──────────────┐
     ▼     ▼              ▼
┌─────────┐ ┌──────────┐ ┌────────────┐
│Software │ │QA        │ │DevOps      │
│Engineer │ │Engineer  │ │Engineer    │
└────┬────┘ └────┬─────┘ └─────┬──────┘
     │            │              │
     └────────────┴──────────────┘
                  │
                  ▼
            Production
```

| Agent | Discipline | Status |
|---|---|---|
| [System Design Architect](agent-builder/agents/system-design-architect/) | Architecture & System Design | ✅ Complete |
| [Software Engineer](agent-builder/agents/software-engineer/) | Implementation & Code Review | 🔧 In Progress |
| [QA Engineer](agent-builder/agents/qa-engineer/) | Testing & Quality | 🔧 In Progress |
| [DevOps Engineer](agent-builder/agents/devops-engineer/) | Infrastructure & Deployment | 🔧 In Progress |

---

## What's Inside

```
maestro/
└── agent-builder/
    ├── schema/
    │   └── agent.schema.yaml          # Master schema — all agents conform to this
    ├── core/
    │   └── base-agent.md              # Fork this to create a new agent
    ├── agents/
    │   ├── system-design-architect/   # Complete reference implementation
    │   │   ├── agent.yaml             # Capabilities, IO contracts, handoffs, evaluation
    │   │   └── persona.md             # Full agent persona (the actual system prompt)
    │   ├── software-engineer/         # Stub
    │   ├── qa-engineer/               # Stub
    │   └── devops-engineer/           # Stub
    └── orchestration/
        └── pipeline.yaml              # Stage order, gate conditions, feedback loops
```

---

## Design Philosophy

**Built on Anthropic's five agent patterns:**

| Pattern | Where it's used |
|---|---|
| Prompt Chaining | Design → Implement → Test → Deploy pipeline |
| Routing | Incoming requests classified and directed to the right agent |
| Parallelization | QA, Software, and DevOps agents work concurrently after design approval |
| Orchestrator-Workers | System Design Architect coordinates downstream agents |
| Evaluator-Optimizer | Review gates with feedback loops back to upstream agents |

**Format: Markdown + YAML** — every agent has two files:
- `agent.yaml` — structured config (capabilities, IO contracts, handoffs, tool allowlists, model selection, evaluation criteria)
- `persona.md` — the human-readable system prompt (reasoning protocol, communication style, examples, edge cases)

**Why this split?** The YAML is machine-parseable. The Markdown is editable as plain text by anyone. They stay in sync because they reference each other, but you can read or modify either without understanding the other.

---

## How to Use an Agent

Each agent is a self-contained prompt system. To use the System Design Architect:

1. Read `agent-builder/agents/system-design-architect/persona.md` — this is the system prompt
2. Provide the inputs from its **Input Contract** (a requirements doc is the only required one)
3. The agent produces the outputs in its **Output Contract** (architecture overview, diagrams, ADRs, NFR baseline, risk register)
4. When the gate condition is met (`design_approved`), pass the **Handoff Payload** to downstream agents

---

## How to Create a New Agent

1. Copy `agent-builder/core/base-agent.md` → `agent-builder/agents/<your-agent-id>/persona.md`
2. Fill in every `[REQUIRED]` section
3. Create `agent-builder/agents/<your-agent-id>/agent.yaml` following `agent-builder/schema/agent.schema.yaml`
4. Use `agents/system-design-architect/` as the complete reference implementation
5. Register the new agent in `agent-builder/orchestration/pipeline.yaml`

### New Agent Checklist
- [ ] `persona.md` complete (all `[REQUIRED]` sections)
- [ ] `agent.yaml` conforms to schema
- [ ] Tool allowlist defined (principle of least privilege)
- [ ] Model selected (`haiku` / `sonnet` / `opus`)
- [ ] Persistent memory scope defined
- [ ] Handoff payload structure defined
- [ ] Self-check prompts (min 5)
- [ ] Review checklist (min 5 items)
- [ ] Registered in `orchestration/pipeline.yaml`

---

## Roadmap

- [x] Base schema (`agent.schema.yaml`)
- [x] Core template (`base-agent.md`)
- [x] System Design Architect — complete reference implementation
- [ ] Software Engineer — full persona
- [ ] QA Engineer — full persona
- [ ] DevOps Engineer — full persona
- [ ] Evaluator Agent — automated review before human gates
- [ ] Tool allowlists + model selection per agent
- [ ] Persistent memory definitions
- [ ] PreToolUse hooks for high-risk operations
- [ ] Example inputs/outputs for each agent
- [ ] End-to-end integration example (requirements → production)

---

## Contributing

This is designed to be forked. Take an agent, adapt the persona for your stack and team norms, and run it. If you improve a pattern, open a PR.

---

*Built with [Anthropic's Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) best practices.*
