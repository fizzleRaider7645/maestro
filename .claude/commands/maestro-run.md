# /maestro-run

Start a Maestro pipeline run from a requirements document.

## Usage

```
/maestro-run [requirements file or inline text] [--project <id>]
```

## What This Does

1. Takes a requirements document (file path or inline text from your message)
2. Starts the full SE pipeline: Design → Implementation → Testing → Deployment
3. Pauses at each human approval gate for your review
4. Stores all artifacts at `~/.maestro/projects/<project-id>/artifacts/`

## Instructions

The user has invoked `/maestro-run`. Their message may contain:
- A file path to a requirements document
- Inline requirements text
- A project name (`--project <name>`)

Do the following:

1. **Extract the requirements** from the user's message:
   - If a file path is given (e.g. `requirements.md`), confirm it exists with the Read tool
   - If inline text is given, use it directly
   - If neither is clear, ask: "Please provide your requirements — either a file path or paste the text directly."

2. **Determine the project ID**:
   - Use `--project <name>` if specified, otherwise use `default`

3. **Run the pipeline** using the Bash tool:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro run "<requirements-path-or-text>" --project <project-id> --verbose
   ```
   If the requirements are inline text, write them to a temp file first:
   ```bash
   cat > /tmp/maestro_requirements.md << 'EOF'
   <requirements text>
   EOF
   maestro run /tmp/maestro_requirements.md --project <project-id> --verbose
   ```

4. **Monitor the output** and surface gate prompts to the user as they appear.

5. When a gate appears, present the gate criteria clearly and ask the user: "Approve or reject? (provide feedback if rejecting)"

6. Use `/maestro-gate` to action the gate decision.

## Prerequisites

- `ANTHROPIC_API_KEY` must be set in your environment or `runtime/.env`
- Install dependencies first if needed: `cd runtime && pip install -e .`
