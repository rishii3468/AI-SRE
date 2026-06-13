"""Timeline construction utilities for incidents."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from aggregate import annotate_events


@dataclass(frozen=True)
class TimelineEvent:
	timestamp: Any
	severity: str
	service: str | None
	component: str | None
	category: str
	message: str
	line_number: int | None = None
	source_file: str | None = None


def build_timeline(frame: pd.DataFrame, max_events: int | None = None) -> pd.DataFrame:
	"""Create a chronologically ordered incident timeline."""

	annotated = annotate_events(frame)
	if annotated.empty:
		return pd.DataFrame(columns=["timestamp", "severity", "service", "component", "category", "message", "line_number", "source_file"])

	timeline = annotated.copy()
	if "timestamp" in timeline:
		timeline = timeline.sort_values(by=["timestamp", "line_number"], na_position="last")
	columns = [col for col in ["timestamp", "severity", "service", "component", "category", "message", "line_number", "source_file"] if col in timeline.columns]
	timeline = timeline.loc[:, columns].reset_index(drop=True)
	if max_events is not None:
		timeline = timeline.head(max_events).reset_index(drop=True)
	return timeline


def to_timeline_events(frame: pd.DataFrame, max_events: int | None = None) -> list[TimelineEvent]:
	"""Convert a timeline frame into dataclass records."""

	timeline = build_timeline(frame, max_events=max_events)
	events: list[TimelineEvent] = []
	for row in timeline.to_dict(orient="records"):
		events.append(
			TimelineEvent(
				timestamp=row.get("timestamp"),
				severity=str(row.get("severity", "INFO")),
				service=row.get("service"),
				component=row.get("component"),
				category=str(row.get("category", "uncategorized")),
				message=str(row.get("message", "")),
				line_number=row.get("line_number"),
				source_file=row.get("source_file"),
			)
		)
	return events


def format_timeline_markdown(frame: pd.DataFrame, max_events: int | None = 20) -> str:
	"""Render a timeline frame as markdown for the incident report."""

	timeline = build_timeline(frame, max_events=max_events)
	if timeline.empty:
		return "No timeline events available."

	lines = []
	for row in timeline.to_dict(orient="records"):
		timestamp = row.get("timestamp")
		timestamp_text = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
		service = row.get("service") or row.get("component") or "unknown"
		lines.append(f"- {timestamp_text} [{row.get('severity', 'INFO')}] {service}: {row.get('message', '')}")
	return "\n".join(lines)


def milestone_events(frame: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
	"""Return the most important events, prioritizing critical signals."""

	annotated = annotate_events(frame)
	if annotated.empty:
		return []

	priority = annotated.copy()
	priority["priority"] = priority["severity"].map({"CRITICAL": 3, "ERROR": 2, "WARNING": 1}).fillna(0)
	priority = priority.sort_values(by=["priority", "timestamp", "line_number"], ascending=[False, True, True], na_position="last")
	priority = priority.head(limit)
	return priority.drop(columns=["priority"]).to_dict(orient="records")


def timeline_to_records(frame: pd.DataFrame, max_events: int | None = None) -> list[dict[str, Any]]:
	"""Return serializable timeline dictionaries."""

	return [asdict(event) for event in to_timeline_events(frame, max_events=max_events)]


__all__ = [
	"TimelineEvent",
	"build_timeline",
	"format_timeline_markdown",
	"milestone_events",
	"timeline_to_records",
	"to_timeline_events",
]
