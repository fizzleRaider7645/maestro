"""
Maestro CLI — entry point for the `maestro` command.

Commands:
  maestro agent <id>              Invoke a single agent
  maestro run <requirements.md>  Run the full pipeline
  maestro gate approve <gate-id> Approve a pending gate
  maestro gate reject <gate-id>  Reject a gate with feedback
  maestro status                 Show run/pipeline status
  maestro validate               Validate all agent.yaml files
  maestro export <agent-id>      Export agent as portable package
  maestro agent new <id>         Scaffold a new agent
  maestro skill new <id>         Scaffold a new skill
  maestro list agents            List all available agents
  maestro list skills            List all available skills
"""

from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Load .env if present
    _load_env()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maestro",
        description="Maestro — multi-agent workflow platform",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    sub = parser.add_subparsers(title="commands")

    # -- agent ----------------------------------------------------------------
    agent_p = sub.add_parser("agent", help="Agent commands")
    agent_sub = agent_p.add_subparsers(title="agent commands")

    # maestro agent <id>  (invoke)
    agent_invoke = sub.add_parser("agent", help="Invoke an agent or manage agents")
    agent_invoke.set_defaults(func=_noop)

    # Override: handle "maestro agent <id>" vs "maestro agent new <id>"
    agent_p2 = argparse.ArgumentParser(add_help=False)
    agent_p2.add_argument("agent_id")
    agent_p2.add_argument("--input", "-i", help="Path to input file (requirements, artifact, etc.)")
    agent_p2.add_argument("--project", "-p", default="default", help="Project ID")
    agent_p2.add_argument("--message", "-m", help="Direct message to send to the agent")

    # maestro agent new <id>
    new_agent_p = sub.add_parser("agent-new", help="Scaffold a new agent (alias: maestro agent new <id>)")
    new_agent_p.add_argument("agent_id")
    new_agent_p.set_defaults(func=_cmd_agent_new)

    # maestro skill new <id>
    new_skill_p = sub.add_parser("skill-new", help="Scaffold a new skill")
    new_skill_p.add_argument("skill_id")
    new_skill_p.set_defaults(func=_cmd_skill_new)

    # -- run ------------------------------------------------------------------
    run_p = sub.add_parser("run", help="Run the full pipeline from a requirements document")
    run_p.add_argument("requirements", help="Path to requirements.md or inline text")
    run_p.add_argument("--project", "-p", default="default", help="Project ID")
    run_p.add_argument("--resume", help="Resume an existing run by run_id")
    run_p.add_argument("--non-interactive", action="store_true", help="Disable interactive gate prompts")
    run_p.set_defaults(func=_cmd_run)

    # -- gate -----------------------------------------------------------------
    gate_p = sub.add_parser("gate", help="Manage pipeline gates")
    gate_sub = gate_p.add_subparsers(title="gate commands")

    gate_approve = gate_sub.add_parser("approve", help="Approve a pending gate")
    gate_approve.add_argument("gate_id")
    gate_approve.add_argument("--run", dest="run_id", required=True, help="Run ID")
    gate_approve.set_defaults(func=_cmd_gate_approve)

    gate_reject = gate_sub.add_parser("reject", help="Reject a gate with feedback")
    gate_reject.add_argument("gate_id")
    gate_reject.add_argument("--run", dest="run_id", required=True, help="Run ID")
    gate_reject.add_argument("--feedback", "-f", default="", help="Rejection feedback")
    gate_reject.set_defaults(func=_cmd_gate_reject)

    # -- status ---------------------------------------------------------------
    status_p = sub.add_parser("status", help="Show pipeline run status")
    status_p.add_argument("--run", dest="run_id", help="Specific run ID to inspect")
    status_p.add_argument("--project", "-p", default="default", help="Project ID")
    status_p.set_defaults(func=_cmd_status)

    # -- validate -------------------------------------------------------------
    validate_p = sub.add_parser("validate", help="Validate all agent.yaml files against schema")
    validate_p.set_defaults(func=_cmd_validate)

    # -- export ---------------------------------------------------------------
    export_p = sub.add_parser("export", help="Export an agent as a portable package")
    export_p.add_argument("agent_id", help="Agent ID to export")
    export_p.add_argument("--format", "-f", default="plaintext",
                          choices=["plaintext", "claude", "openai"],
                          help="Output format (default: plaintext)")
    export_p.add_argument("--output", "-o", help="Output file path (default: stdout)")
    export_p.set_defaults(func=_cmd_export)

    # -- list -----------------------------------------------------------------
    list_p = sub.add_parser("list", help="List available agents or skills")
    list_p.add_argument("what", choices=["agents", "skills"], help="What to list")
    list_p.add_argument("--project", "-p", default="default")
    list_p.set_defaults(func=_cmd_list)

    # -- invoke (top-level shorthand: maestro invoke <agent_id>) -------------
    invoke_p = sub.add_parser("invoke", help="Invoke an agent directly")
    invoke_p.add_argument("agent_id")
    invoke_p.add_argument("--input", "-i", help="Path to input file")
    invoke_p.add_argument("--project", "-p", default="default")
    invoke_p.add_argument("--message", "-m", help="Direct message to the agent")
    invoke_p.set_defaults(func=_cmd_invoke)

    return parser


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def _cmd_invoke(args: argparse.Namespace) -> None:
    """Invoke a single agent."""
    _require_api_key()
    from .agents.agent_registry import AgentRegistry
    from .agents.base_agent import AgentRunner
    from .memory.session_memory import SessionMemory
    from .memory.artifact_store import ArtifactStore
    from .skills.skill_registry import SkillRegistry

    registry = AgentRegistry()
    try:
        agent = registry.get(args.agent_id)
    except KeyError:
        print(f"Error: agent '{args.agent_id}' not found.")
        available = registry.list_ids()
        print(f"Available agents: {', '.join(available)}")
        sys.exit(1)

    # Build the input message
    if hasattr(args, "input") and args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: input file not found: {args.input}")
            sys.exit(1)
        message = input_path.read_text()
        print(f"Input: {args.input} ({len(message)} chars)")
    elif hasattr(args, "message") and args.message:
        message = args.message
    else:
        print("Enter your message (Ctrl+D when done):")
        try:
            message = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(0)

    project_id = getattr(args, "project", "default")
    session_id = f"cli_{args.agent_id}"
    verbose = getattr(args, "verbose", False)

    skill_registry = SkillRegistry(project_id=project_id)
    session = SessionMemory(session_id)
    artifact_store = ArtifactStore(project_id)

    print(f"\nInvoking: {agent.name} (v{agent.version})")
    print("-" * 50)

    runner = AgentRunner(
        agent=agent,
        skill_registry=skill_registry,
        session=session,
        artifact_store=artifact_store,
        verbose=verbose,
    )
    handoff = runner.run(message, stage_id="cli")
    print("\n" + "=" * 50)
    print(handoff.raw_output)

    # Show artifact location if stored
    if handoff.artifacts:
        print(f"\nArtifacts saved:")
        for name, ref in handoff.artifacts.items():
            print(f"  {name}: {ref.path}")


def _cmd_run(args: argparse.Namespace) -> None:
    """Run the full pipeline."""
    _require_api_key()
    from .orchestration.orchestrator import Orchestrator

    req_path = Path(args.requirements)
    if req_path.exists():
        requirements = req_path.read_text()
        print(f"Requirements: {req_path} ({len(requirements)} chars)")
    else:
        requirements = args.requirements

    orch = Orchestrator(
        project_id=args.project,
        resume_run_id=getattr(args, "resume", None),
        interactive=not getattr(args, "non_interactive", False),
        verbose=getattr(args, "verbose", False),
    )
    run_id = asyncio.run(orch.run(requirements))
    print(f"\nDone. Run ID: {run_id}")


def _cmd_gate_approve(args: argparse.Namespace) -> None:
    """Approve a gate by updating its persisted state."""
    from .core.constants import RUNS_DIR
    gate_file = RUNS_DIR / args.run_id / "gates" / f"{args.gate_id}.json"
    if not gate_file.exists():
        print(f"Error: gate not found: {args.gate_id} in run {args.run_id}")
        sys.exit(1)
    import json
    with open(gate_file) as f:
        data = json.load(f)
    data["status"] = "approved"
    with open(gate_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Gate {args.gate_id} approved.")


def _cmd_gate_reject(args: argparse.Namespace) -> None:
    """Reject a gate with feedback."""
    from .core.constants import RUNS_DIR
    gate_file = RUNS_DIR / args.run_id / "gates" / f"{args.gate_id}.json"
    if not gate_file.exists():
        print(f"Error: gate not found: {args.gate_id} in run {args.run_id}")
        sys.exit(1)
    import json
    with open(gate_file) as f:
        data = json.load(f)
    data["status"] = "rejected"
    data["rejection_feedback"] = args.feedback
    with open(gate_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Gate {args.gate_id} rejected.")
    if args.feedback:
        print(f"Feedback: {args.feedback}")


def _cmd_status(args: argparse.Namespace) -> None:
    """Show pipeline status."""
    from .core.constants import RUNS_DIR, PROJECTS_DIR
    from .memory.project_memory import ProjectMemory

    project_id = getattr(args, "project", "default")
    run_id = getattr(args, "run_id", None)

    if not run_id:
        # Get active run from project memory
        mem = ProjectMemory(project_id)
        run_id = mem.active_run_id
        if not run_id:
            print(f"No active run for project '{project_id}'.")
            print(f"Start one with: maestro run <requirements.md> --project {project_id}")
            return

    state_file = RUNS_DIR / run_id / "run_state.json"
    if not state_file.exists():
        print(f"Run not found: {run_id}")
        sys.exit(1)

    import json
    with open(state_file) as f:
        state = json.load(f)

    print(f"\nRun:     {state['run_id']}")
    print(f"Project: {state['project_id']}")
    print(f"Pipeline:{state['pipeline_name']}")
    print(f"Status:  {'COMPLETE' if state.get('completed') else 'IN PROGRESS'}")
    print(f"\nStages:")
    print(f"  {'STAGE':<20} {'STATUS':<18} {'REVISIONS':<10} {'GATE'}")
    print(f"  {'-'*20} {'-'*18} {'-'*10} {'-'*10}")
    for sid, ss in state.get("stages", {}).items():
        gate_status = ss["gate"]["status"] if ss.get("gate") else "—"
        print(f"  {sid:<20} {ss['status']:<18} {ss.get('revision_count', 0):<10} {gate_status}")

    # Show artifact locations
    from .memory.artifact_store import ArtifactStore
    store = ArtifactStore(project_id)
    all_artifacts = store.list_all()
    if any(refs for refs in all_artifacts.values()):
        print(f"\nArtifacts ({PROJECTS_DIR / project_id / 'artifacts'}):")
        for sid, refs in all_artifacts.items():
            if refs:
                print(f"  {sid}/")
                for ref in refs:
                    print(f"    {ref.artifact_type}.{ref.format}")


def _cmd_validate(args: argparse.Namespace) -> None:
    """Validate all agent.yaml files."""
    from .core.schema_validator import validate_all_agents

    results = validate_all_agents()
    all_valid = True
    for agent_id, errors in results.items():
        if errors:
            all_valid = False
            print(f"FAIL  {agent_id}")
            for e in errors:
                print(f"      • {e}")
        else:
            print(f"PASS  {agent_id}")

    print()
    if all_valid:
        print(f"All {len(results)} agent(s) valid.")
    else:
        failed = sum(1 for e in results.values() if e)
        print(f"{failed}/{len(results)} agent(s) have errors.")
        sys.exit(1)


def _cmd_export(args: argparse.Namespace) -> None:
    """Export an agent as a portable package."""
    from .export.exporter import export_agent

    try:
        output = export_agent(args.agent_id, format=args.format)
    except KeyError:
        print(f"Error: agent '{args.agent_id}' not found.")
        sys.exit(1)

    if hasattr(args, "output") and args.output:
        Path(args.output).write_text(output)
        print(f"Exported to: {args.output}")
    else:
        print(output)


def _cmd_list(args: argparse.Namespace) -> None:
    """List agents or skills."""
    if args.what == "agents":
        from .agents.agent_registry import AgentRegistry
        registry = AgentRegistry()
        summaries = registry.summary()
        print(f"\n{'ID':<30} {'NAME':<28} {'VERSION':<10} {'DISCIPLINE'}")
        print(f"{'-'*30} {'-'*28} {'-'*10} {'-'*20}")
        for s in summaries:
            print(f"{s['id']:<30} {s['name']:<28} {s['version']:<10} {s['discipline']}")
    else:
        project_id = getattr(args, "project", "default")
        from .skills.skill_registry import SkillRegistry
        registry = SkillRegistry(project_id=project_id)
        skills = registry.list_skills()
        print(f"\n{'ID':<25} DESCRIPTION")
        print(f"{'-'*25} {'-'*40}")
        for s in skills:
            print(f"{s['id']:<25} {s['description']}")


def _cmd_agent_new(args: argparse.Namespace) -> None:
    """Scaffold a new agent."""
    from .builder.agent_scaffolder import scaffold_agent
    scaffold_agent(args.agent_id)


def _cmd_skill_new(args: argparse.Namespace) -> None:
    """Scaffold a new skill."""
    from .builder.skill_scaffolder import scaffold_skill
    scaffold_skill(args.skill_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it in your shell or in a .env file in the runtime/ directory.")
        sys.exit(1)


def _load_env() -> None:
    """Load .env file from runtime/ directory if present."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # dotenv not installed — parse manually
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


def _noop(args: argparse.Namespace) -> None:
    print("Specify a subcommand. Use --help for options.")


if __name__ == "__main__":
    main()
