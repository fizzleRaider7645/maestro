"""Scaffolds a new agent directory with agent.yaml + persona.md stubs."""

from __future__ import annotations
import sys
from pathlib import Path

from ..core.constants import AGENTS_DIR


def scaffold_agent(agent_id: str, agents_dir: Path = AGENTS_DIR) -> None:
    """
    Create a new agent directory with agent.yaml and persona.md stubs.
    Prints instructions on what to fill in.
    """
    dir_name = agent_id.replace("_", "-")
    agent_dir = agents_dir / dir_name

    if agent_dir.exists():
        print(f"Error: agent directory already exists: {agent_dir}")
        sys.exit(1)

    agent_dir.mkdir(parents=True)

    # Write agent.yaml
    yaml_content = f"""\
# =============================================================================
# agent.yaml — {agent_id}
# Schema: agent-builder/v1
# =============================================================================

$schema: "agent-builder/v1"

identity:
  id: {agent_id}
  name: "{agent_id.replace('_', ' ').title()}"
  version: "0.1.0"
  discipline: software_engineering   # Change to: system_design | software_engineering | testing_qa | devops_infra
  role: "TODO: Short role descriptor"
  persona_file: "./persona.md"

behavior:
  tone: pragmatic                    # analytical | collaborative | pragmatic | critical
  verbosity: balanced                # concise | balanced | thorough
  reasoning_style: pattern_matching  # first_principles | pattern_matching | trade_off_analysis | hypothesis_driven

capabilities:
  primary:
    - "TODO: Primary capability 1"
    - "TODO: Primary capability 2"
  secondary:
    - "TODO: Secondary capability (defers to X for Y)"
  anti_patterns:
    - "TODO: Anti-pattern to flag or block"

io:
  accepts:
    - type: requirements_doc
      format: markdown
      required: true
  produces:
    - type: output_artifact
      format: markdown

handoffs:
  upstream:
    - human_stakeholder
  downstream:
    - TODO_downstream_agent

  trigger_conditions:
    - condition: work_complete
      to: TODO_downstream_agent
      payload:
        - output_artifact

constraints:
  scope_limits:
    - "TODO: What this agent must NOT do"
  escalation_triggers:
    - "TODO: Condition that requires human review"
  confidence_threshold: 0.75

evaluation:
  success_criteria:
    - "TODO: Measurable outcome of a successful run"
  self_check_prompts:
    - "TODO: Question the agent asks itself before finalizing output"
  review_checklist:
    - "[ ] TODO: Item for downstream agent or human reviewer"
"""

    (agent_dir / "agent.yaml").write_text(yaml_content)

    # Write persona.md stub
    display_name = agent_id.replace("_", " ").title()
    persona_content = f"""\
# {display_name} — Agent Persona
---
agent_id: {agent_id}
schema_version: "agent-builder/v1"
version: "0.1.0"
---

## Identity

**Name:** {display_name}
**Role:** TODO: Short role descriptor
**Discipline:** TODO

You are the {display_name}. [2-sentence mission statement: what you do and why it matters in the pipeline.]

---

## Core Principles

1. **TODO: Principle name.** TODO: Explanation — the non-negotiable directive.
2. **TODO: Principle name.** TODO: Explanation.
3. **TODO: Principle name.** TODO: Explanation.
4. **TODO: Principle name.** TODO: Explanation.
5. **TODO: Principle name.** TODO: Explanation.

---

## Competencies

### Primary (Owned)

- **TODO: Capability name:** TODO: Detailed description of what you own and how you exercise it.

### Secondary (Consulted)

- **TODO: Capability name:** TODO: What you contribute and who you defer to for decisions.

### Anti-Patterns (Flagged and Blocked)

- **TODO: Anti-pattern name:** TODO: What it is and why it's blocked or flagged.

---

## Reasoning Protocol

**Step 1 — Intake & Clarification**

TODO: What you confirm before starting work. What blocking questions do you ask?

**Step 2 — Context Gathering**

TODO: What you assemble. What do you state explicitly as assumptions?

**Step 3 — Analysis**

TODO: How you analyze the problem. What framework or checklist do you apply?

**Step 4 — Draft / Implement**

TODO: What you produce and in what order.

**Step 5 — Self-Review**

Ask every question in `evaluation.self_check_prompts`. Any "no" blocks handoff.

**Step 6 — Handoff**

TODO: How you package and route your output.

---

## Communication Style

**Tone:** TODO
**Verbosity:** TODO
**Reasoning style:** TODO

### Response Format

```
## TODO: Section 1
[Description]

## TODO: Section 2
[Description]
```

### Language Rules
- TODO: Language rule 1
- TODO: Language rule 2

---

## Input Contract

| Input Type | Format | Required | Description |
|---|---|---|---|
| TODO | markdown | Yes | TODO description |

---

## Output Contract

| Output Type | Format | Description |
|---|---|---|
| TODO | markdown | TODO description |

---

## Handoff Protocol

### Upstream (receives from)
- **TODO upstream agent:** Sends TODO on TODO condition.

### Downstream (sends to)
- **TODO downstream agent:** TODO artifacts — on TODO condition.

### Handoff Payload

```yaml
handoff:
  from: {agent_id}
  to: TODO_downstream_agent
  trigger: work_complete
  artifacts:
    - output_artifact: "agents/{dir_name}/outputs/output.md"
  context:
    version: "[semver]"
  open_questions:
    - "[Any unresolved item]"
```

---

## Constraints

### Scope Limits
This agent must NOT:
- TODO: Scope limit 1

### Escalation Triggers
This agent pauses and requests human review when:
- TODO: Escalation condition

### Confidence Threshold
If confidence falls below **75%**, state confidence and required validation action.

---

## Evaluation

### Success Criteria
- [ ] TODO: Measurable outcome

### Self-Check Prompts
1. TODO: Self-check question 1?
2. TODO: Self-check question 2?

### Review Checklist
- [ ] TODO: Review item

---

## Examples

### Example Input
```
TODO: Sample input
```

### Example Output
```
TODO: Sample output
```

---

## Notes & Edge Cases

- TODO: Edge case or special behavior note.
"""

    (agent_dir / "persona.md").write_text(persona_content)

    print(f"Scaffolded agent: {agent_dir}")
    print(f"\nNext steps:")
    print(f"  1. Edit {agent_dir}/agent.yaml — fill in all TODO fields")
    print(f"  2. Edit {agent_dir}/persona.md — write the full persona")
    print(f"  3. Run: maestro validate — to check the agent.yaml is valid")
    print(f"  4. Run: maestro invoke {agent_id} --message 'test' — to test it")
