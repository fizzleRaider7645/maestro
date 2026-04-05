# /maestro-scaffold

Scaffold a new agent or skill interactively.

## Usage

```
/maestro-scaffold agent <id>
/maestro-scaffold skill <id>
```

## Instructions

The user has invoked `/maestro-scaffold`. Their message specifies whether they want to create an agent or a skill.

### Scaffolding an Agent

1. **Extract the agent ID** (snake_case, e.g. `product_manager`)
2. **Run the scaffolder**:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro agent-new <agent-id>
   ```
3. **Open the generated files** for the user using the Read tool so they can see what was created
4. **Guide them** on what to fill in:
   - `agent.yaml`: discipline, tone, capabilities, I/O contract
   - `persona.md`: mission statement, 5 core principles, competency narratives, reasoning protocol
5. **Reference** `agents/system-design-architect/` as the gold-standard example

### Scaffolding a Skill

1. **Extract the skill ID** (snake_case, e.g. `github_create_pr`)
2. **Run the scaffolder**:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro skill-new <skill-id>
   ```
3. **Open the generated files** for the user
4. **Guide them** on what to implement in `skill.py`:
   - The `invoke()` method — return a string result for the agent
   - Update `parameters_schema` to match your `skill.yaml`
5. **Verify registration**:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro list skills
   ```

### After Scaffolding Either

- Run `maestro validate` to check the yaml is schema-valid
- Offer to help fill in the TODO sections
