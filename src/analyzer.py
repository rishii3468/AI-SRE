"""Incident root-cause analysis helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd

from aggregate import build_operational_snapshot, categorize_message, summarize_events
from parser import detect_incident_window
from prompts import build_root_cause_prompt
from retreiver import format_retrieved_runbooks, retrieve_runbooks
from timeline import format_timeline_markdown, milestone_events

try:
	import ollama
except ImportError:  # pragma: no cover - handled at runtime with fallback
	ollama = None


CAUSE_HINTS: dict[str, dict[str, Any]] = {
	"redis_timeout": {
		"root_cause": "Redis connection pool exhaustion",
		"remediation": ["Restart or scale Redis", "Increase pool size", "Review retry and timeout settings"],
	},
	"authentication_failure": {
		"root_cause": "Authentication dependency latency or outage",
		"remediation": ["Check session store health", "Inspect auth service retries", "Validate token/session validation path"],
	},
	"api_latency": {
		"root_cause": "Downstream dependency slowdown causing elevated API latency",
		"remediation": ["Inspect slow dependencies", "Check saturation and retry amplification", "Scale the bottleneck service"],
	},
	"oomkilled": {
		"root_cause": "Container memory pressure caused process termination",
		"remediation": ["Increase memory limits", "Investigate memory growth", "Restart the workload after tuning"],
	},
	"disk_full": {
		"root_cause": "Disk exhaustion prevented normal writes",
		"remediation": ["Free disk space", "Rotate or purge logs", "Expand storage capacity"],
	},
	"dns_failure": {
		"root_cause": "DNS resolution failure disrupted service discovery",
		"remediation": ["Check DNS provider health", "Validate resolver configuration", "Retry failing lookups"],
	},
	"network_partition": {
		"root_cause": "Network partition or unstable connectivity between services",
		"remediation": ["Check network paths", "Inspect firewall and routing changes", "Fail over to healthy regions"],
	},
	"dependency_outage": {
		"root_cause": "Downstream dependency outage or severe degradation",
		"remediation": ["Confirm dependency status", "Apply graceful degradation", "Trigger fallback logic"],
	},
}


@dataclass(frozen=True)
class IncidentAnalysis:
	root_cause: str
	confidence: int
	evidence: list[str]
	recommended_actions: list[str]
	suspected_category: str
	runbooks: list[dict[str, Any]]
	incident_window: tuple[str | None, str | None]
	summary: dict[str, Any]
	timeline: list[dict[str, Any]]


def _build_llm_payload(
	frame: pd.DataFrame,
	summary: dict[str, Any],
	runbook_hits: list[dict[str, Any]],
	evidence: list[str],
) -> str:
	return build_root_cause_prompt(
		incident_summary=summary,
		timeline=format_timeline_markdown(frame),
		runbook_context=format_retrieved_runbooks(runbook_hits),
		evidence=evidence,
	)


def _default_ollama_model() -> str:
	return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def _call_ollama(prompt: str, model: str | None = None) -> dict[str, Any] | None:
	"""Ask Ollama for a structured incident analysis response.

	The function returns a dictionary when the model responds with JSON.
	If Ollama is unavailable or returns unparseable text, the caller can fall
	back to the deterministic analysis already used by the app.
	"""

	if ollama is None:
		return None

	model_name = model or _default_ollama_model()
	system_message = (
		"You are a senior SRE incident commander. Return ONLY valid JSON with the keys "
		"root_cause, confidence, evidence, recommended_actions, suspected_category. "
		"confidence must be an integer between 0 and 100. evidence and recommended_actions must be arrays of strings."
	)
	response = ollama.chat(
		model=model_name,
		messages=[
			{"role": "system", "content": system_message},
			{"role": "user", "content": prompt},
		],
		format="json",
	)
	message = response.get("message", {}) if isinstance(response, dict) else {}
	content = message.get("content") if isinstance(message, dict) else None
	if not content:
		return None

	try:
		parsed = json.loads(content)
	except json.JSONDecodeError:
		return None

	if not isinstance(parsed, dict):
		return None
	return parsed


def _select_candidate(summary: dict[str, Any]) -> str:
	category_counts = summary.get("category_counts", {}) or {}
	if not category_counts:
		return "uncategorized"
	return max(category_counts.items(), key=lambda item: item[1])[0]


def _fallback_root_cause(category: str, top_message: str | None = None) -> tuple[str, list[str]]:
	hint = CAUSE_HINTS.get(category)
	if hint:
		return hint["root_cause"], list(hint["remediation"])

	if top_message:
		return f"Primary signal: {top_message}", ["Inspect the matching runbook", "Review surrounding log context", "Confirm whether the issue is still active"]

	return "Insufficient evidence for a confident root cause", ["Collect more logs", "Check adjacent services", "Review monitoring dashboards"]


def _build_evidence(frame: pd.DataFrame, limit: int = 5) -> list[str]:
	if frame.empty:
		return []

	important = milestone_events(frame, limit=limit)
	evidence = []
	for row in important:
		timestamp = row.get("timestamp")
		timestamp_text = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
		evidence.append(f"{timestamp_text} {row.get('severity', 'INFO')} {row.get('message', '')}")
	return evidence


def _confidence_from_frame(frame: pd.DataFrame, category: str) -> int:
	if frame.empty:
		return 25

	severity_boost = 10 if any(str(value).upper() in {"ERROR", "CRITICAL"} for value in frame.get("severity", [])) else 0
	category_hits = int((frame.get("category") == category).sum()) if "category" in frame else 0
	confidence = 35 + min(25, category_hits * 5) + severity_boost
	return max(20, min(95, confidence))


def _get_meaningful_query_for_category(frame: pd.DataFrame, category: str) -> str:
	"""Generate a meaningful search query for runbook retrieval.
	
	For uncategorized events, extracts key phrases from actual messages.
	For known categories, returns the category name.
	"""
	
	if category != "uncategorized":
		return category
	
	# For uncategorized events, try to extract meaningful keywords from messages
	if "message" in frame.columns and not frame.empty:
		# Get critical messages if available, otherwise any message
		if "is_critical" in frame.columns:
			critical_mask = frame["is_critical"].fillna(False)
			messages = frame.loc[critical_mask, "message"].dropna().astype(str)
		else:
			messages = frame["message"].dropna().astype(str)
		
		if not messages.empty:
			# Get the first message and extract a meaningful query
			top_message = messages.iloc[0]
			# Extract first 50 characters or until first punctuation for a reasonable query
			query = top_message.split(".")[0].split(",")[0][:60].strip()
			return query if query else "incident troubleshooting"
	
	return "incident troubleshooting"


def analyze_incident(
	frame: pd.DataFrame,
	runbook_hits: list[dict[str, Any]] | None = None,
	use_llm: bool = False,
	ollama_model: str | None = None,
) -> IncidentAnalysis:
	"""Produce a deterministic analysis from the parsed incident frame."""

	runbook_hits = runbook_hits or []
	snapshot = build_operational_snapshot(frame)
	summary = snapshot["summary"]
	category = _select_candidate(summary)

	top_message = None
	category_table = snapshot.get("category_table", [])
	if category_table:
		top_message = category_table[0].get("sample_message")

	root_cause, remediation = _fallback_root_cause(category, top_message)
	confidence = _confidence_from_frame(frame, category)
	evidence = _build_evidence(frame)

	if runbook_hits:
		top_runbook = runbook_hits[0]
		title = top_runbook.get("title") or top_runbook.get("metadata", {}).get("title")
		if title:
			evidence.append(f"Retrieved runbook: {title}")
		remediation = remediation + [f"Review {title}" for title in [title] if title]
		confidence = min(98, confidence + 5)

	llm_result: dict[str, Any] | None = None
	if use_llm:
		# The project can plug an Ollama client here later; the deterministic
		# result remains the baseline so the app works offline.
		prompt = build_root_cause_prompt(
			incident_summary=summary,
			timeline=format_timeline_markdown(frame),
			runbook_context=format_retrieved_runbooks(runbook_hits),
			evidence=evidence,
		)
		evidence.append(prompt[:400])

	incident_window = detect_incident_window(frame)
	start, end = incident_window

	return IncidentAnalysis(
		root_cause=root_cause,
		confidence=confidence,
		evidence=evidence,
		recommended_actions=list(dict.fromkeys(remediation)),
		suspected_category=category,
		runbooks=runbook_hits,
		incident_window=(start.isoformat() if start is not None else None, end.isoformat() if end is not None else None),
		summary=summary,
		timeline=milestone_events(frame),
	)


def analyze_with_runbooks(frame: pd.DataFrame, query: str | None = None, top_k: int = 4) -> IncidentAnalysis:
	"""Run retrieval first, then produce an analysis.
	
	If query is not provided, automatically generates one from the incident data.
	For uncategorized events, extracts meaningful keywords from actual messages.
	"""

	# If no query provided, generate one based on the incident
	if query is None:
		snapshot = build_operational_snapshot(frame)
		summary = snapshot["summary"]
		category = _select_candidate(summary)
		query = _get_meaningful_query_for_category(frame, category)
	
	hits = retrieve_runbooks(query=query, k=top_k)
	return analyze_incident(frame, runbook_hits=hits)


def analysis_to_dict(analysis: IncidentAnalysis) -> dict[str, Any]:
	"""Serialize the analysis dataclass for JSON or markdown rendering."""

	return asdict(analysis)


__all__ = ["IncidentAnalysis", "analysis_to_dict", "analyze_incident", "analyze_with_runbooks"]
