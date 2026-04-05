<br>
<div align="center">

```
███╗   ███╗ █████╗ ███████╗███████╗████████╗██████╗  ██████╗
████╗ ████║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗
██╔████╔██║███████║█████╗  ███████╗   ██║   ██████╔╝██║   ██║
██║╚██╔╝██║██╔══██║██╔══╝  ╚════██║   ██║   ██╔══██╗██║   ██║
██║ ╚═╝ ██║██║  ██║███████╗███████║   ██║   ██║  ██║╚██████╔╝
╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝
```

**An out-of-the-box multi-agent workflow platform**
*Agent Builder · Skill Builder · Orchestration · Intent Routing · Human-in-the-Loop Gates*

---

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Anthropic](https://img.shields.io/badge/powered%20by-Claude-orange.svg)](https://www.anthropic.com/)
[![LLM Agnostic](https://img.shields.io/badge/LLM-agnostic-green.svg)](#multi-platform)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

</div>

---

## What is Maestro?

Maestro turns a requirements document into a production-ready system by routing work through a team of specialized AI agents — Architect, Engineer, QA, DevOps — each with structured input/output contracts, human approval gates, and feedback loops.

It works in any LLM platform. Agent personas are pure Markdown — paste them into Claude, ChatGPT, Cursor, or use the Python CLI against the Anthropic API.

```
Requirements ──► Architecture ──► Code ──► Tests ──► Production
                  [gate]           [gate]   [gate]     [gate]
                     ▲               │        │
                     └───────────────┘        │  feedback loops
                     ▲────────────────────────┘
```

---

## Architecture

```
maestro/
│
├── agent-builder/               # Source of truth — never modified at runtime
│   ├── schema/
│   │   ├── agent.schema.yaml    # Master schema: all agents conform to this
│   │   └── skill.schema.yaml    # Schema for skill definitions
│   ├── core/
│   │   └── base-agent.md        # Template: fork this to create a new agent
│   ├── agents/
│   │   ├── system-design-architect/   ✅ Complete (reference implementation)
│   │   ├── software-engineer/         ✅ Complete
│   │   ├── qa-engineer/               ✅ Complete
│   │   └── devops-engineer/           ✅ Complete
│   └── orchestration/
│       └── pipeline.yaml        # Stage order, gates, feedback loops
│
├── runtime/                     # Python CLI + execution engine
│   └── maestro/
│       ├── cli.py               # `maestro` command entry point
│       ├── core/                # Loaders, types, schema validator
│       ├── agents/              # AgentRunner, AgentRegistry, EvaluatorAgent
│       ├── skills/              # SkillRegistry + builtin skills
│       ├── orchestration/       # Orchestrator, StageRunner, GateManager
│       ├── intent/              # Rules-based + LLM intent router
│       ├── memory/              # ArtifactStore, SessionMemory, ProjectMemory
│       ├── export/              # Multi-platform agent exporter
│       └── builder/             # Agent + skill scaffolders
│
├── skills/                      # Your custom skills (populated by `maestro skill-new`)
│
└── .claude/commands/            # Claude Code slash command integrations
    ├── maestro-run.md           # /maestro-run
    ├── maestro-agent.md         # /maestro-agent
    ├── maestro-scaffold.md      # /maestro-scaffold
    ├── maestro-gate.md          # /maestro-gate
    ├── maestro-status.md        # /maestro-status
    └── maestro-review.md        # /maestro-review
```

---

## The Agent Pipeline

Each agent owns a stage. Agents run concurrently where dependencies allow (Engineer, QA, and DevOps all start after design approval). Every stage ends with a gate.

```
                    ┌─────────────────────────────────┐
                    │      System Design Architect     │
                    │   ADRs · NFRs · Components ·     │
                    │   Data flows · Risk register     │
                    └─────────────┬───────────────────┘
                                  │
                         [ Human Approval Gate ]
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐
  │ Software Engineer│  │  QA Engineer   │  │  DevOps Engineer   │
  │ Source code      │  │ Test strategy  │  │ Infrastructure     │
  │ API contracts    │  │ NFR validation │  │ CI/CD pipeline     │
  │ Migrations       │  │ Defect reports │  │ Runbook + Rollback │
  └────────┬─────────┘  └───────┬────────┘  └────────┬───────────┘
           │  [ Peer Review ]   │  [ Quality Gate ]  │  [ Go/No-Go ]
           └───────────────────►└────────────────────►
                                                      │
                                               Production
```

### Feedback Loops

Gates are not dead ends. Rejected work routes back automatically:

| Trigger | From | To |
|---|---|---|
| Design ambiguity found | Software Engineer | System Design Architect |
| Architectural defect found | QA Engineer | System Design Architect |
| Code defects found | QA Engineer | Software Engineer |
| Infrastructure constraint found | DevOps Engineer | System Design Architect |

---

## Quick Start

### Install

```bash
git clone https://github.com/you/maestro
cd maestro/runtime
pip install -e .
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

### Verify

```bash
maestro validate            # all 4 agents pass schema validation
maestro list agents         # see the agent registry
```

### Run a Pipeline

```bash
maestro run requirements.md --project my-project
```

The pipeline runs until it hits the first human approval gate, then pauses and prompts you.

### Invoke a Single Agent

```bash
maestro invoke system_design_architect --input requirements.md --project my-project
```

### Export an Agent for Any Platform

```bash
# Paste into ChatGPT, Perplexity, Cursor, or any LLM chat
maestro export system_design_architect --format plaintext

# Get a Python snippet for the Claude API
maestro export system_design_architect --format claude

# Get a Python snippet for the OpenAI API
maestro export system_design_architect --format openai
```

---

## CLI Reference

```
maestro invoke  <agent-id>          Invoke a single agent
maestro run     <requirements.md>   Run the full pipeline
maestro gate    approve <gate-id>   Approve a pending gate
maestro gate    reject  <gate-id>   Reject a gate with feedback
maestro status                      Show run state and artifacts
maestro validate                    Validate all agent.yaml files
maestro export  <agent-id>          Export agent as portable package
maestro list    agents              List all available agents
maestro list    skills              List all available skills
maestro agent-new <id>              Scaffold a new agent
maestro skill-new <id>              Scaffold a new skill
```

**Global flags:** `--project <id>`, `--verbose`, `--run <run-id>`

---

## Claude Code Skills

Six slash commands are pre-built for use inside Claude Code:

| Command | What it does |
|---|---|
| `/maestro-run` | Start a pipeline run from a requirements doc |
| `/maestro-agent` | Invoke a single agent interactively |
| `/maestro-scaffold` | Scaffold a new agent or skill with guided setup |
| `/maestro-gate` | Review artifacts and approve or reject a pending gate |
| `/maestro-status` | Show pipeline state, stage progress, and artifact inventory |
| `/maestro-review` | Run the evaluator agent on any artifact before a gate fires |

---

## Multi-Platform

Agent personas are pure Markdown system prompts. No Python required to use them.

| Platform | How to use |
|---|---|
| **Claude (claude.ai)** | Paste `persona.md` as the system prompt |
| **Claude API** | `maestro export <id> --format claude` → ready-to-run snippet |
| **ChatGPT (Custom GPT)** | Paste `persona.md` into the Instructions field |
| **OpenAI API** | `maestro export <id> --format openai` → ready-to-run snippet |
| **Cursor / VS Code Copilot** | Paste into `.cursorrules` or Copilot instructions |
| **Perplexity** | Use as context in your first message |
| **CLI (any model)** | `maestro invoke <id>` — uses Anthropic by default, swap via `MAESTRO_DEFAULT_MODEL` |

---

## The Agent Spec

Every agent is defined by two files that work together:

### `agent.yaml` — structured machine-readable config

```yaml
identity:
  id: system_design_architect
  version: "1.0.0"
  discipline: system_design

behavior:
  tone: analytical
  verbosity: thorough
  reasoning_style: trade_off_analysis

capabilities:
  primary:
    - "Distributed systems design"
    - "Architecture Decision Records (ADRs)"
  anti_patterns:
    - "Missing observability (no logging, metrics, or tracing)"

io:
  accepts:
    - type: requirements_doc
      format: markdown
      required: true
  produces:
    - type: architecture_overview
      format: markdown

constraints:
  confidence_threshold: 0.75

evaluation:
  self_check_prompts:
    - "Can the QA Engineer derive a full test strategy from this design without asking me?"
  review_checklist:
    - "[ ] All NFR targets are specific and measurable"
```

### `persona.md` — the system prompt

```markdown
## Identity
You are the System Design Architect...

## Core Principles
1. **Clarity over cleverness.**...

## Reasoning Protocol
Step 1 — Intake & Clarification
Step 2 — Context Gathering
...

## Input Contract
| requirements_doc | Markdown | Required |

## Output Contract
| architecture_overview | Markdown | Prose description... |
```

---

## Creating a New Agent

```bash
maestro agent-new product_manager
```

This scaffolds `agent-builder/agents/product-manager/agent.yaml` and `persona.md` with all required sections marked as TODO. Fill them in, then:

```bash
maestro validate              # check the yaml is schema-valid
maestro invoke product_manager --message "Define requirements for X"
```

**New agent checklist:**
- [ ] `persona.md` — mission statement, 5 core principles, competency narratives, reasoning protocol
- [ ] `agent.yaml` — discipline, tone, I/O contract, handoffs, evaluation criteria
- [ ] Self-check prompts (minimum 5)
- [ ] Review checklist (minimum 5 items)
- [ ] Added to `orchestration/pipeline.yaml` agent registry

---

## Creating a New Skill

Skills are tools agents can invoke during execution (filesystem access, API calls, code execution, etc.).

```bash
maestro skill-new github_create_pr
```

This scaffolds `skills/github_create_pr/skill.yaml` and `skill.py`. Implement `invoke()`, then:

```bash
maestro list skills           # confirm it's auto-discovered
```

Agents use skills via Claude's native `tool_use` protocol. The skill registry enforces which agents can invoke which skills.

---

## Data Layout

All runtime state is stored in `~/.maestro/`:

```
~/.maestro/
├── projects/<project-id>/
│   ├── context.json                    # Run history, active run, decisions
│   └── artifacts/
│       ├── design/
│       │   ├── architecture_overview.md
│       │   ├── component_diagram.mmd
│       │   ├── nfr_baseline.yaml
│       │   └── adrs/
│       ├── implementation/
│       ├── testing/
│       └── deployment/
├── sessions/<session-id>.json          # Conversation history per agent invocation
└── runs/<run-id>/
    ├── run_state.json                  # Full pipeline run state
    └── gates/<gate-id>.json            # Individual gate states
```

Human-readable, git-committable, zero database dependencies.

---

## Design Philosophy

**Built on Anthropic's five agent patterns:**

| Pattern | Where Maestro uses it |
|---|---|
| **Prompt Chaining** | Requirements → Design → Implement → Test → Deploy |
| **Routing** | Intent router maps natural language to agent/stage/pipeline |
| **Parallelization** | Engineer, QA, and DevOps run concurrently after design approval |
| **Orchestrator-Workers** | System Design Architect coordinates all downstream agents |
| **Evaluator-Optimizer** | Automated evaluator runs before every human gate; rejections feed back |

**Key decisions:**

- **Definitions are the source of truth.** The runtime reads `agent-builder/` — it never writes to it. Agents are portable to any platform.
- **Gates block by default.** Human approval gates never auto-approve. The evaluator filters noise so reviewers only see gate-ready output.
- **No framework lock-in.** Raw `anthropic` SDK + `asyncio`. The pipeline is defined in YAML — no graph framework needed.
- **Zero mandatory dependencies beyond Python + anthropic.** Memory is JSON files. No database, no Redis, no Docker required to start.

---

## Roadmap

- [x] Base schema (`agent.schema.yaml`, `skill.schema.yaml`)
- [x] Core template (`base-agent.md`)
- [x] All four agents — production-quality personas
- [x] Python runtime + `maestro` CLI
- [x] Orchestration layer — concurrent stages, gates, feedback loops
- [x] Evaluator agent — automated pre-gate quality review
- [x] Intent router — rules-based + LLM fallback
- [x] Multi-platform export (`--format plaintext|claude|openai`)
- [x] Skill registry + builtin skills
- [x] Agent + skill scaffolders
- [x] Claude Code slash command skills
- [ ] Web search skill (Brave/Tavily)
- [ ] Code execution skill (sandboxed subprocess)
- [ ] GitHub integration skill
- [ ] FastAPI server mode (`maestro api`)
- [ ] Example end-to-end pipeline run (requirements → production artifacts)
- [ ] VS Code extension

---

## Contributing

Fork it. Adapt the agent personas for your domain or stack. Add skills for your tools. Open a PR if you improve a pattern.

The agent personas are the most valuable part — thoughtful authorship of the reasoning protocol and anti-patterns is what makes the difference between an agent that produces useful output and one that produces plausible noise.

---

<div align="center">

*Built on [Anthropic's agent best practices](https://www.anthropic.com/research/building-effective-agents)*

</div>
