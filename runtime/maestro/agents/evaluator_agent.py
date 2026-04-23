"""
EvaluatorAgent — automated pre-gate quality checker.

Runs the stage agent's review_checklist and the gate's approval_criteria
against the stage outputs before surfacing the gate to a human reviewer.
"""

from __future__ import annotations
import os
import re

import anthropic

from ..core.types import AgentConfig, GateConfig
from ..core.constants import DEFAULT_MODEL


def _parse_verdict(report: str) -> bool:
    """
    Extract PASS/FAIL from the Overall Verdict section of an evaluator report.

    Handles LLM formatting variations:
    - Blank line between heading and verdict
    - Bold markdown (**PASS**)
    - Trailing text after the verdict word
    """
    match = re.search(
        r'###\s*Overall\s+Verdict\s*\n+\s*\**\s*(PASS|FAIL)\s*\**',
        report,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).upper() == "PASS"
    # Fallback: compare PASS/FAIL frequency in the last 300 characters
    tail = report[-300:].upper()
    pass_count = tail.count("PASS")
    fail_count = tail.count("FAIL")
    return pass_count > 0 and pass_count >= fail_count


class EvaluatorAgent:
    """
    Automated quality gate that runs before every human gate.

    Reads:
    - The producing agent's evaluation.review_checklist
    - The gate's approval_criteria

    Produces a structured PASS/FAIL report with checklist results.
    """

    def __init__(self, model: str | None = None):
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self._model = model or os.environ.get("MAESTRO_DEFAULT_MODEL", DEFAULT_MODEL)

    def evaluate(
        self,
        agent: AgentConfig,
        gate_config: GateConfig,
        output_content: str,
        stage_name: str = "",
    ) -> tuple[bool, str]:
        """
        Evaluate stage output against review_checklist and approval_criteria.

        Returns:
            (passed: bool, report: str)
        """
        checklist_items = agent.evaluation.review_checklist
        approval_criteria = gate_config.approval_criteria

        if not checklist_items and not approval_criteria:
            return True, "No evaluation criteria defined — gate skipped."

        # Build the evaluation prompt
        checklist_section = ""
        if checklist_items:
            items = "\n".join(f"- {item}" for item in checklist_items)
            checklist_section = f"\n## Agent Review Checklist\n{items}"

        criteria_section = ""
        if approval_criteria:
            criteria = "\n".join(f"- {c}" for c in approval_criteria)
            criteria_section = f"\n## Gate Approval Criteria\n{criteria}"

        # Truncate output for cost efficiency
        output_preview = output_content[:4000] + "\n...[truncated]" if len(output_content) > 4000 else output_content

        prompt = (
            f"You are an automated quality evaluator for the '{stage_name}' pipeline stage.\n\n"
            f"Evaluate the following output against each checklist item and approval criterion.\n"
            f"For each item, respond: PASS or FAIL with a one-line reason.\n"
            f"At the end, give an overall verdict: PASS (all items pass) or FAIL (any item fails).\n"
            f"{checklist_section}"
            f"{criteria_section}"
            f"\n\n## Output to Evaluate\n{output_preview}\n\n"
            f"Respond in this format:\n"
            f"### Checklist Results\n"
            f"- [item]: PASS/FAIL — reason\n\n"
            f"### Overall Verdict\n"
            f"PASS or FAIL\n"
            f"[Brief summary of any failures]"
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            report = response.content[0].text if response.content else "No evaluation produced."
            passed = _parse_verdict(report)
            return passed, report
        except Exception as e:
            return True, f"Evaluator error (defaulting to pass): {e}"
