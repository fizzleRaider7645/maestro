# Agent Builder

A structured system for creating, composing, and operating specialized AI agents for software engineering workflows. Agents are defined in **Markdown + YAML** — version-controllable, forkable, and ready to use as base templates.

---

## The Four Agents

```
Requirements
     │
     ▼
┌─────────────────────────┐
│  System Design          │  ← Architecture, ADRs, NFR baselines,
│  Architect              │    component + data flow diagrams
└──────────┬──────────────┘
           │ approved design artifacts
     ┌─────┴──────┬──────────────┐
     ▼            ▼              ▼
┌──────────┐ ┌─────────┐ ┌────────────┐
│Software  │ │QA       │ │DevOps      │
│Engineer  │ │Engineer │ │Engineer    │
└────┬─────┘ └────┬────┘ └─────┬──────┘
     │             │             │
     └─────────────┴─────────────┘
                   │
                   ▼
             Production
```

| Agent | Discipline | Status |
|---|---|---|
| [System Design Architect](agents/system-design-architect/) | Architecture & System Design | ✅ Complete |
| [Software Engineer](agents/software-engineer/) | Implementation & Code Review | 🔧 Stub |
| [QA Engineer](agents/qa-engineer/) | Testing & Quality | 🔧 Stub |
| [DevOps Engineer](agents/devops-engineer/) | Infrastructure & Deployment | 🔧 Stub |

---

## File Structure

```
agent-builder/
├── README.md
├── schema/
│   └── agent.schema.yaml              ← Master schema all agents conform to
├── core/
│   └── base-agent.md                  ← Fork this to create a new agent persona
├── agents/
│   ├── system-design-architect/       ← COMPLETE reference implementation
│   │   ├── agent.yaml                 ← Capabilities, IO contracts, handoffs, evaluation
│   │   └── persona.md                 ← Full agent persona (system prompt)
│   ├── software-engineer/             ← Stub: agent.yaml complete, persona.md needs work
│   ├── qa-engineer/                   ← Stub: agent.yaml complete, persona.md needs work
│   └── devops-engineer/               ← Stub: agent.yaml complete, persona.md needs work
├── orchestration/
│   └── pipeline.yaml                  ← Stage order, gates, feedback loops, agent registry
└── examples/
    └── (coming — reference I/O per agent)
```

---

## How to Use

### Single Agent
1. Read the agent's `persona.md` — this is the system prompt.
2. Provide the inputs from its **Input Contract**.
3. Receive the outputs from its **Output Contract**.
4. When the gate condition is met, pass the **Handoff Payload** to the next agent.

### Full Pipeline
1. Start with `orchestration/pipeline.yaml` for stage order and gate conditions.
2. Each stage maps to one agent — provide that agent its required inputs.
3. Check gate criteria before advancing.
4. Use feedback loop definitions to route issues back to the correct upstream agent.

---

## How to Create a New Agent

1. Copy `core/base-agent.md` → `agents/<your-agent-id>/persona.md`
2. Fill in all `[REQUIRED]` sections
3. Create `agents/<your-agent-id>/agent.yaml` following `schema/agent.schema.yaml`
4. Reference `agents/system-design-architect/` as the complete working example
5. Add the agent to `agent_registry` in `orchestration/pipeline.yaml`
6. Define the agent's stage with gate conditions and handoff payloads

### New Agent Checklist
- [ ] `persona.md` — all `[REQUIRED]` sections complete
- [ ] `agent.yaml` — conforms to `schema/agent.schema.yaml`
- [ ] Competencies: primary, secondary, anti-patterns defined
- [ ] Input and output contracts defined with types and formats
- [ ] Handoff payload structure defined
- [ ] Self-check prompts (minimum 5)
- [ ] Review checklist (minimum 5 items)
- [ ] Added to `orchestration/pipeline.yaml` agent registry
- [ ] Stage definition added with gate conditions

---

## Design Decisions

**Why Markdown + YAML?** Human-readable, version-controllable, diff-friendly, LLM-native. Agents can read their own configuration as part of their context.

**Why separate `agent.yaml` and `persona.md`?** YAML is machine-readable structured data. Markdown is the human-readable instruction set. Keeping them separate lets you parse the structure programmatically while keeping the prose editable as plain text.

**Why explicit handoff payloads?** Implicit handoffs are the #1 source of context loss in multi-agent systems. Every handoff here is a typed, structured object with versioned artifact references.

**Why human approval gates?** Automated checks are necessary but not sufficient for novel engineering work. Gates exist at points of highest ambiguity (design approval) and highest risk (production deployment).

---

## Next Steps

1. Complete `persona.md` for the Software Engineer, QA Engineer, and DevOps Engineer — use `system-design-architect/persona.md` as the reference.
2. Add example inputs and outputs to `examples/` for each agent.
3. Add a system-level integration example — a sample requirements doc flowing all the way through the pipeline.

---

*System Design Architect v1.0.0 is the canonical reference implementation for all other agents.*
