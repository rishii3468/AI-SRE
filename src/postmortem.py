"""Postmortem report generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from analyzer import IncidentAnalysis, analysis_to_dict
from timeline import format_timeline_markdown


def _format_list(items: list[str]) -> str:
	if not items:
		return "- None"
	return "\n".join(f"- {item}" for item in items)


def build_postmortem_markdown(
	analysis: IncidentAnalysis | dict[str, Any],
	timeline_frame: pd.DataFrame,
	impact: str | None = None,
) -> str:
	"""Render a postmortem-ready markdown document."""

	data = analysis_to_dict(analysis) if isinstance(analysis, IncidentAnalysis) else analysis
	incident_window = data.get("incident_window", (None, None))
	if isinstance(incident_window, tuple):
		start, end = incident_window
	else:
		start, end = None, None

	runbooks = data.get("runbooks", []) or []
	runbook_lines = []
	for hit in runbooks:
		title = hit.get("title", "Unknown Runbook")
		score = hit.get("score", 0.0)
		runbook_lines.append(f"- {title} (score: {score:.4f})")

	report = [
		"# Incident Postmortem",
		"",
		"## Summary",
		f"Root cause: {data.get('root_cause', 'Unknown')}",
		f"Confidence: {data.get('confidence', 0)}%",
		f"Suspected category: {data.get('suspected_category', 'uncategorized')}",
		f"Incident window: {start or 'unknown'} to {end or 'unknown'}",
		"",
		"## Impact",
		impact or "Impact not provided.",
		"",
		"## Timeline",
		format_timeline_markdown(timeline_frame),
		"",
		"## Evidence",
		_format_list(list(data.get('evidence', []))),
		"",
		"## Retrieved Runbooks",
		"\n".join(runbook_lines) if runbook_lines else "- None",
		"",
		"## Recommended Actions",
		_format_list(list(data.get('recommended_actions', []))),
		"",
		"## Prevention",
		"- Review alert thresholds and paging rules",
		"- Add or update runbooks for the identified failure mode",
		"- Capture follow-up actions and owners",
	]
	return "\n".join(report).strip() + "\n"


def write_postmortem_report(
	output_path: str | Path,
	analysis: IncidentAnalysis | dict[str, Any],
	timeline_frame: pd.DataFrame,
	impact: str | None = None,
) -> Path:
	"""Write the generated postmortem markdown to disk."""

	path = Path(output_path)
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(build_postmortem_markdown(analysis, timeline_frame, impact=impact), encoding="utf-8")
	return path


__all__ = ["build_postmortem_markdown", "write_postmortem_report"]
