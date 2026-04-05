# /maestro-agent

Invoke a single Maestro agent directly, outside of the pipeline.

## Usage

```
/maestro-agent <agent-id> [--input <file>] [--project <id>] [--message "..."]
```

## Available Agents

- `system_design_architect` — Translates requirements into documented architecture
- `software_engineer` — Implements approved designs into production code
- `qa_engineer` — Tests implementation against design and NFRs
- `devops_engineer` — Builds infrastructure, CI/CD, and deployment runbooks

## Instructions

The user has invoked `/maestro-agent`. Their message contains an agent ID and optionally an input.

1. **Extract the agent ID** from the user's message.
   - If no agent ID is given, list available agents:
     ```bash
     cd /Users/douglasuretsky/Projects/maestro/runtime && maestro list agents
     ```
     Then ask which agent they want.

2. **Extract the input**:
   - File path: use `--input <path>`
   - Inline message: use `--message "..."`
   - If neither, ask the user to provide input

3. **Show the agent's input contract** before running:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro export <agent-id> --format plaintext | head -60
   ```

4. **Invoke the agent**:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro invoke <agent-id> --input <file> --project <project-id> --verbose
   ```

5. **Display the output** to the user in a clean format.

6. **Show artifact location** if artifacts were saved.

## Notes

- Use this for iterating on a single stage without running the full pipeline
- The agent's session is saved and can be resumed
- Artifacts are stored in `~/.maestro/projects/<project-id>/artifacts/`
