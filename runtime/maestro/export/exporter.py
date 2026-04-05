"""
Multi-platform agent exporter.

Generates self-contained, pasteable agent packages for:
- claude: Claude API system prompt format
- openai: OpenAI ChatGPT system message format
- plaintext: Universal markdown format (works anywhere)
"""

from __future__ import annotations
import json

from ..core.types import AgentConfig
from ..core.agent_loader import load_agent
from ..agents.agent_registry import AgentRegistry


FORMATS = ("claude", "openai", "plaintext")


def export_agent(agent_id: str, format: str = "plaintext") -> str:
    """
    Export an agent as a self-contained package.

    Args:
        agent_id: The agent to export.
        format: One of 'claude', 'openai', 'plaintext'.

    Returns:
        A string containing the exportable agent package.
    """
    if format not in FORMATS:
        raise ValueError(f"Unknown format '{format}'. Choose from: {FORMATS}")

    registry = AgentRegistry()
    agent = registry.get(agent_id)

    if format == "claude":
        return _export_claude(agent)
    elif format == "openai":
        return _export_openai(agent)
    else:
        return _export_plaintext(agent)


def _export_plaintext(agent: AgentConfig) -> str:
    """Universal markdown export — works in any LLM chat."""
    io_table = _build_io_table(agent)
    lines = [
        f"# {agent.name}",
        f"*Role: {agent.role} | Discipline: {agent.discipline.value} | Version: {agent.version}*",
        "",
        "---",
        "",
        "## How to Use This Agent",
        "",
        "Paste the content below the horizontal rule into the **system prompt** (or equivalent)",
        "of your LLM platform (Claude, ChatGPT, Perplexity, Cursor, VS Code Copilot, etc.).",
        "Then provide your task as the first user message, following the Input Contract.",
        "",
        "---",
        "",
        "## System Prompt",
        "",
        agent.system_prompt,
        "",
        "---",
        "",
        "## Quick Reference",
        "",
        io_table,
        "",
        "## Platform-Specific Notes",
        "",
        "- **Claude (claude.ai or API):** Paste into System prompt field.",
        "- **ChatGPT (Custom GPT):** Paste into Instructions field.",
        "- **Cursor / VS Code Copilot:** Paste into `.cursorrules` or Copilot instructions file.",
        "- **Perplexity:** Use as context in your first message prefixed with 'Act as:'.",
        "- **API (any provider):** Use as the `system` parameter in your messages.create() call.",
    ]
    return "\n".join(lines)


def _export_claude(agent: AgentConfig) -> str:
    """Export as a Claude API messages.create() snippet."""
    system_prompt_escaped = agent.system_prompt.replace('"""', '\\"\\"\\"')
    lines = [
        f"# {agent.name} — Claude API Snippet",
        f"# Agent: {agent.id} v{agent.version}",
        "",
        "```python",
        "import anthropic",
        "",
        "client = anthropic.Anthropic()",
        "",
        f'SYSTEM_PROMPT = """{system_prompt_escaped}"""',
        "",
        "response = client.messages.create(",
        '    model="claude-sonnet-4-6",',
        "    max_tokens=8096,",
        "    system=SYSTEM_PROMPT,",
        "    messages=[",
        '        {"role": "user", "content": "YOUR_INPUT_HERE"}',
        "    ],",
        ")",
        "print(response.content[0].text)",
        "```",
        "",
        "## Input Contract",
        _build_io_table(agent),
    ]
    return "\n".join(lines)


def _export_openai(agent: AgentConfig) -> str:
    """Export as an OpenAI chat completions snippet."""
    lines = [
        f"# {agent.name} — OpenAI API Snippet",
        f"# Agent: {agent.id} v{agent.version}",
        "",
        "```python",
        "from openai import OpenAI",
        "",
        "client = OpenAI()",
        "",
        "SYSTEM_PROMPT = '''",
        agent.system_prompt,
        "'''",
        "",
        "response = client.chat.completions.create(",
        '    model="gpt-4o",',
        "    messages=[",
        '        {"role": "system", "content": SYSTEM_PROMPT},',
        '        {"role": "user", "content": "YOUR_INPUT_HERE"},',
        "    ],",
        ")",
        "print(response.choices[0].message.content)",
        "```",
        "",
        "## Input Contract",
        _build_io_table(agent),
    ]
    return "\n".join(lines)


def _build_io_table(agent: AgentConfig) -> str:
    lines = ["### Inputs", "| Type | Format | Required |", "|---|---|---|"]
    for inp in agent.accepts:
        req = "Yes" if inp.required else "No"
        lines.append(f"| {inp.type} | {inp.format} | {req} |")
    lines.append("")
    lines.append("### Outputs")
    lines.append("| Type | Format |")
    lines.append("|---|---|")
    for out in agent.produces:
        lines.append(f"| {out.type} | {out.format} |")
    return "\n".join(lines)
