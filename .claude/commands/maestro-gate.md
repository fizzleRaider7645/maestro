# /maestro-gate

Review and action a pending pipeline gate.

## Usage

```
/maestro-gate [approve|reject] <gate-id> --run <run-id> [--feedback "..."]
```

## Instructions

The user has invoked `/maestro-gate`. They want to approve or reject a pending gate.

### Step 1 — Find the Active Gate

If no gate ID is given, find pending gates:
```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro status --project <project-id>
```

Look for stages with status `awaiting_gate`. The gate ID is in the stage's gate field.

You can also inspect the gate file directly:
```bash
ls ~/.maestro/runs/<run-id>/gates/
cat ~/.maestro/runs/<run-id>/gates/<gate-id>.json
```

### Step 2 — Show the Gate Payload

Read the gate file and present its contents clearly to the user:
- Gate type (human_approval, peer_review, automated_plus_human)
- Approval criteria
- Evaluator report (if present)
- Artifacts produced

Read the relevant artifacts so the user can review them:
```bash
ls ~/.maestro/projects/<project-id>/artifacts/<stage-id>/
```

### Step 3 — Get User Decision

Ask: **"Approve or reject this gate?"**
- If approving: proceed to Step 4
- If rejecting: ask for feedback: "What should be revised?"

### Step 4 — Action the Decision

**To approve:**
```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro gate approve <gate-id> --run <run-id>
```

**To reject:**
```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro gate reject <gate-id> --run <run-id> --feedback "<feedback>"
```

### Step 5 — Confirm

Show the updated gate status:
```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro status --run <run-id>
```
