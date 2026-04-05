"""
Intent router — maps natural language input to pipeline/stage/agent.

Rules are applied first (deterministic, fast). If no rule matches,
a single LLM call (Claude Haiku) produces a structured routing decision.
If confidence < 0.75, the router asks for clarification.
"""

from __future__ import annotations
import json
import os

import anthropic

from ..core.types import IntentRequest, RoutingDecision
from ..core.constants import ROUTER_MODEL
from ..agents.agent_registry import AgentRegistry
from .rules import apply_rules


class IntentRouter:
    """
    Routes user intent to the appropriate pipeline/stage/agent.

    Usage:
        router = IntentRouter(agent_registry)
        decision = router.route(IntentRequest(text="run the design stage"))
    """

    CONFIDENCE_THRESHOLD = 0.75

    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def route(self, request: IntentRequest) -> RoutingDecision:
        """Route a user request. Returns a RoutingDecision."""
        known_ids = self.agent_registry.list_ids()

        # Try deterministic rules first
        decision = apply_rules(request.text, known_ids)
        if decision:
            return decision

        # Fall back to LLM routing
        decision = self._llm_route(request, known_ids)

        # If confidence is too low, ask for clarification
        if decision.confidence < self.CONFIDENCE_THRESHOLD:
            decision.requires_clarification = True
            decision.clarification_prompt = (
                f"I'm not sure how to route your request: '{request.text}'\n\n"
                f"Available agents: {', '.join(known_ids)}\n"
                f"Available stages: design, implementation, testing, deployment\n\n"
                f"Could you clarify what you'd like to do?"
            )
        return decision

    def _llm_route(self, request: IntentRequest, known_agent_ids: list[str]) -> RoutingDecision:
        """Use Claude Haiku to resolve the routing decision."""
        agents_list = "\n".join(f"- {aid}" for aid in known_agent_ids)
        prompt = (
            f"You are a routing assistant for a multi-agent software engineering pipeline.\n\n"
            f"Given a user request, determine which agent or pipeline stage to route to.\n\n"
            f"Available agents:\n{agents_list}\n\n"
            f"Available pipeline stages: design, implementation, testing, deployment\n\n"
            f"User request: {request.text}\n\n"
            f"Respond with ONLY valid JSON in this format:\n"
            f'{{"pipeline_id": null, "stage_id": null, "agent_id": null, '
            f'"confidence": 0.0, "reasoning": ""}}\n\n'
            f"Set the most specific match. confidence is 0.0-1.0. "
            f"If truly ambiguous, set confidence < 0.75."
        )

        try:
            response = self._client.messages.create(
                model=ROUTER_MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip() if response.content else "{}"
            # Extract JSON from response (may be wrapped in markdown code block)
            if "```" in text:
                text = text.split("```")[1].lstrip("json").strip()
            data = json.loads(text)
            return RoutingDecision(
                pipeline_id=data.get("pipeline_id"),
                stage_id=data.get("stage_id"),
                agent_id=data.get("agent_id"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
            )
        except Exception as e:
            return RoutingDecision(
                confidence=0.0,
                reasoning=f"Router error: {e}",
                requires_clarification=True,
                clarification_prompt=f"Could not determine routing for: '{request.text}'. Please specify an agent or stage.",
            )
