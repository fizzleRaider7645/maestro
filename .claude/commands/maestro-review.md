# /maestro-review

Trigger the evaluator agent on any artifact or the current stage's outputs.

## Usage

```
/maestro-review [--stage <stage-id>] [--artifact <type>] [--project <id>]
```

## Instructions

The user has invoked `/maestro-review`. They want to run the automated evaluator on an artifact before a gate fires, or to get a quality assessment of current outputs.

### Step 1 — Identify What to Review

If `--stage` is given, review all artifacts from that stage.
If `--artifact` is given, review that specific artifact.
If neither is given, ask: "Which stage or artifact would you like reviewed?"

List available artifacts:
```bash
ls ~/.maestro/projects/<project-id>/artifacts/
```

### Step 2 — Read the Artifact(s)

Use the Read tool to load the artifact content:
```
~/.maestro/projects/<project-id>/artifacts/<stage-id>/<artifact-type>.md
```

### Step 3 — Read the Relevant Agent's Review Checklist

Find the agent for this stage by checking `agent-builder/orchestration/pipeline.yaml`, then read their `agent.yaml`:
```
agent-builder/agents/<agent-dir>/agent.yaml  → evaluation.review_checklist
```

### Step 4 — Run the Evaluation

With the artifact content and checklist loaded, evaluate each checklist item:

For each item in `evaluation.review_checklist`:
- Read the item
- Check whether the artifact satisfies it (PASS / FAIL / PARTIAL)
- Give a one-line reason

Then check each gate `approval_criteria` from `pipeline.yaml` for this stage.

### Step 5 — Present the Report

Format the report as:

```
## Review Report: <Stage Name>

### Checklist Results
- [item]: PASS/FAIL — reason

### Approval Criteria
- [criterion]: PASS/FAIL — reason

### Overall Verdict
PASS / FAIL

### Recommendations (if FAIL)
[What needs to change before this gate should be approved]
```

### Step 6 — Suggest Next Action

- If PASS: "This looks gate-ready. Use `/maestro-gate` to approve."
- If FAIL: "The following items need attention before approving: [list]"
