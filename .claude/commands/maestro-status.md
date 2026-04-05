# /maestro-status

Show current pipeline run state, stage progress, and artifact inventory.

## Usage

```
/maestro-status [--project <id>] [--run <run-id>]
```

## Instructions

The user has invoked `/maestro-status`. Show them the current state of their pipeline.

### Step 1 — Get Status

```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro status --project <project-id>
```

If `--run <run-id>` was specified:
```bash
cd /Users/douglasuretsky/Projects/maestro/runtime && maestro status --run <run-id>
```

### Step 2 — Format the Output

Present the status table clearly. For each stage highlight:
- `pending` — not yet started (gray)
- `running` — currently executing
- `awaiting_gate` — paused, needs human decision → call out clearly
- `approved` — gate passed, proceeding
- `completed` — done
- `failed` — error occurred

### Step 3 — Surface Actionable Items

For any stage in `awaiting_gate`:
> **Action needed:** Stage `<name>` is waiting for your approval.
> Run `/maestro-gate` to review and action it.

For any stage in `failed`:
> **Error:** Stage `<name>` failed. Check the error in the run state file:
> `~/.maestro/runs/<run-id>/run_state.json`

### Step 4 — Show Available Artifacts

List artifacts that have been produced:
```bash
ls -la ~/.maestro/projects/<project-id>/artifacts/
```

Offer to show any artifact:
> "Would you like me to read any of these artifacts?"

### Step 5 — Suggest Next Action

Based on the state, suggest what to do next:
- All stages complete → "Pipeline complete! Use `/maestro-export` to package outputs."
- Gate pending → "Use `/maestro-gate` to approve or reject the pending gate."
- Stage running → "Pipeline is in progress — check back shortly."
- Nothing started → "Start with `/maestro-run <requirements.md>`"
