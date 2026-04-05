"""Maestro runtime constants and default configuration."""

from pathlib import Path
import os

# Root of the maestro repository (two levels up from this file)
REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Path to the agent-builder definitions directory
AGENT_BUILDER_DIR = Path(
    os.environ.get("MAESTRO_AGENT_BUILDER_DIR", REPO_ROOT / "agent-builder")
)

# Per-user data directory
MAESTRO_DATA_DIR = Path(
    os.environ.get("MAESTRO_DATA_DIR", Path.home() / ".maestro")
)

# Subdirectories within the data directory
PROJECTS_DIR = MAESTRO_DATA_DIR / "projects"
SESSIONS_DIR = MAESTRO_DATA_DIR / "sessions"
RUNS_DIR = MAESTRO_DATA_DIR / "runs"

# Model defaults
DEFAULT_MODEL = os.environ.get("MAESTRO_DEFAULT_MODEL", "claude-sonnet-4-6")
ROUTER_MODEL = "claude-haiku-4-5-20251001"  # fast + cheap for intent routing
ARCHITECT_MODEL = "claude-opus-4-6"  # thorough for complex design tasks

# Agent-specific model overrides (agent_id → model)
AGENT_MODEL_OVERRIDES: dict[str, str] = {
    "system_design_architect": ARCHITECT_MODEL,
}

# Agentic loop limits
DEFAULT_MAX_TURNS = 10

# Confidence threshold below which agents request clarification
DEFAULT_CONFIDENCE_THRESHOLD = 0.75

# Schema file paths
AGENT_SCHEMA_FILE = AGENT_BUILDER_DIR / "schema" / "agent.schema.yaml"
SKILL_SCHEMA_FILE = AGENT_BUILDER_DIR / "schema" / "skill.schema.yaml"
PIPELINE_FILE = AGENT_BUILDER_DIR / "orchestration" / "pipeline.yaml"
AGENTS_DIR = AGENT_BUILDER_DIR / "agents"
