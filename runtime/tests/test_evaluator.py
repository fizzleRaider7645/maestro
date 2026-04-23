"""Tests for EvaluatorAgent._parse_verdict and verdict parsing edge cases."""

from __future__ import annotations

import pytest

from maestro.agents.evaluator_agent import _parse_verdict


class TestParseVerdict:
    def test_standard_pass(self) -> None:
        report = "### Checklist Results\n- item: PASS\n\n### Overall Verdict\nPASS"
        assert _parse_verdict(report) is True

    def test_standard_fail(self) -> None:
        report = "### Checklist Results\n- item: FAIL\n\n### Overall Verdict\nFAIL"
        assert _parse_verdict(report) is False

    def test_blank_line_between_heading_and_verdict_pass(self) -> None:
        """LLMs commonly insert a blank line before the verdict word."""
        report = "### Checklist Results\n- item: PASS\n\n### Overall Verdict\n\nPASS"
        assert _parse_verdict(report) is True

    def test_blank_line_between_heading_and_verdict_fail(self) -> None:
        report = "### Checklist Results\n- item: FAIL\n\n### Overall Verdict\n\nFAIL"
        assert _parse_verdict(report) is False

    def test_bold_markdown_pass(self) -> None:
        """LLMs sometimes bold the verdict: **PASS**"""
        report = "### Overall Verdict\n**PASS**"
        assert _parse_verdict(report) is True

    def test_bold_markdown_fail(self) -> None:
        report = "### Overall Verdict\n**FAIL**"
        assert _parse_verdict(report) is False

    def test_trailing_text_after_verdict(self) -> None:
        """Verdict with trailing explanation should still parse correctly."""
        report = "### Overall Verdict\nPASS — all checklist items met"
        assert _parse_verdict(report) is True

    def test_fail_with_trailing_summary(self) -> None:
        report = "### Overall Verdict\nFAIL — 2 items did not meet criteria"
        assert _parse_verdict(report) is False

    def test_case_insensitive(self) -> None:
        report = "### Overall Verdict\npass"
        assert _parse_verdict(report) is True

    def test_fallback_pass_count_wins(self) -> None:
        """No Overall Verdict heading — fallback counts PASS/FAIL in last 300 chars."""
        report = "item1: PASS\nitem2: PASS\nitem3: PASS\nConclusion: PASS"
        assert _parse_verdict(report) is True

    def test_fallback_fail_count_wins(self) -> None:
        report = "item1: FAIL\nitem2: FAIL\nSummary: FAIL"
        assert _parse_verdict(report) is False

    def test_no_verdict_no_pass_no_fail_returns_false(self) -> None:
        """Completely ambiguous report (no PASS/FAIL) — defaults to False."""
        report = "The evaluation is inconclusive."
        assert _parse_verdict(report) is False

    def test_pass_earlier_in_report_does_not_override_fail_verdict(self) -> None:
        """An item labeled PASS earlier should not override a FAIL Overall Verdict."""
        report = (
            "### Checklist Results\n"
            "- All components are implemented: PASS\n\n"
            "### Overall Verdict\nFAIL\nOne critical criterion was not met."
        )
        assert _parse_verdict(report) is False
