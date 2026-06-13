"""Prompt templates for incident analysis and reporting."""

from __future__ import annotations

from typing import Iterable


INCIDENT_SUMMARY_PROMPT = """You are an SRE assistant. Summarize the incident using the logs, then extract the top failure signals, likely service impacted, and a concise operational summary.

Logs:
{logs}

Return:
1. Summary
2. Key signals
3. Impacted services
4. Confidence hints
"""

ROOT_CAUSE_PROMPT = """You are an SRE investigating a production incident.

Incident summary:
{incident_summary}

Timeline:
{timeline}

Retrieved runbooks:
{runbook_context}

Evidence:
{evidence}

Provide:
1. Root cause
2. Confidence score from 0 to 100
3. Evidence-backed reasoning
4. Remediation steps
5. Preventive actions
"""

POSTMORTEM_PROMPT = """You are drafting a production incident postmortem.

Incident analysis:
{analysis}

Timeline:
{timeline}

Runbooks:
{runbook_context}

Write a concise, evidence-backed postmortem with the sections Summary, Impact, Timeline, Root Cause, Remediation, and Prevention.
"""


def _join_bullets(items: Iterable[str]) -> str:
	lines = [f"- {item}" for item in items]
	return "\n".join(lines) if lines else "- None"


def build_summary_prompt(logs: str) -> str:
	return INCIDENT_SUMMARY_PROMPT.format(logs=logs.strip())


def build_root_cause_prompt(
	incident_summary: dict | str,
	timeline: str,
	runbook_context: str,
	evidence: Iterable[str],
) -> str:
	return ROOT_CAUSE_PROMPT.format(
		incident_summary=incident_summary,
		timeline=timeline.strip(),
		runbook_context=runbook_context.strip() or "No runbooks retrieved.",
		evidence=_join_bullets(evidence),
	)


def build_postmortem_prompt(analysis: dict | str, timeline: str, runbook_context: str) -> str:
	return POSTMORTEM_PROMPT.format(
		analysis=analysis,
		timeline=timeline.strip(),
		runbook_context=runbook_context.strip() or "No runbooks retrieved.",
	)


__all__ = [
	"INCIDENT_SUMMARY_PROMPT",
	"POSTMORTEM_PROMPT",
	"ROOT_CAUSE_PROMPT",
	"build_postmortem_prompt",
	"build_root_cause_prompt",
	"build_summary_prompt",
]
