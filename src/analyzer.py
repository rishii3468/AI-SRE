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
	impact: str


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
	return os.getenv("OLLAMA_MODEL", "gemma3:1b")


# def _call_ollama(prompt: str, model: str | None = None) -> dict[str, Any] | None:
# 	"""Ask Ollama for a structured incident analysis response.

# 	The function returns a dictionary when the model responds with JSON.
# 	If Ollama is unavailable or returns unparseable text, the caller can fall
# 	back to the deterministic analysis already used by the app.
# 	"""

# 	if ollama is None:
# 		return None

# 	model_name = model or _default_ollama_model()
# 	system_message = (
# 		"You are a senior SRE incident commander. Return ONLY valid JSON with the keys "
# 		"root_cause, confidence, evidence, recommended_actions, suspected_category. "
# 		"confidence must be an integer between 0 and 100. evidence and recommended_actions must be arrays of strings."
# 	)
# 	response = ollama.chat(
# 		model=model_name,
# 		messages=[
# 			{"role": "system", "content": system_message},
# 			{"role": "user", "content": prompt},
# 		],
# 		format="json",
# 	)
# 	message = response.get("message", {}) if isinstance(response, dict) else {}
# 	content = message.get("content") if isinstance(message, dict) else None
# 	if not content:
# 		return None

# 	try:
# 		parsed = json.loads(content)
# 	except json.JSONDecodeError:
# 		return None

# 	if not isinstance(parsed, dict):
# 		return None
# 	return parsed

def _call_ollama(prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
    
    try:
        # Request generation from Ollama
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],

        )
        
        # FIX: Handle ChatResponse object properties safely instead of assuming a dict
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            content = response.message.content
        elif isinstance(response, dict):
            # Fallback if an older wrapper version or custom dict wrapper is active
            content = response.get("message", {}).get("content")
        else:
            return None

        if not content:
            return None

        # Parse the JSON string from the model response
        parsed = json.loads(content)
        
        if not isinstance(parsed, dict):
            return None
            
        return parsed

    except (json.JSONDecodeError, Exception) as e:
        # Catch connection errors, timeouts, or JSON parsing anomalies safely
        print(f"Ollama invocation or parsing failed: {e}")
        return None

def _select_candidate(summary: dict[str, Any]) -> str:
	category_counts = summary.get("category_counts", {}) or {}
	if category_counts:
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


def _calculate_impact(frame: pd.DataFrame, summary: dict[str, Any]) -> str:
	"""Calculate incident impact description based on event severity and volume."""
	if frame.empty:
		return "Minimal impact - insufficient data"
	
	critical_count = summary.get("critical_events", 0)
	total_count = summary.get("total_events", 0)
	
	# Calculate impact severity
	if critical_count == 0:
		return "Minimal impact - no critical events detected"
	elif critical_count >= 10:
		return f"Severe impact - {critical_count} critical events indicate widespread service degradation"
	elif critical_count >= 5:
		return f"High impact - {critical_count} critical events affecting multiple services"
	elif critical_count >= 2:
		return f"Moderate impact - {critical_count} critical events detected, localized to specific components"
	else:
		return f"Low impact - {critical_count} critical event(s) with limited scope"


def _confidence_from_frame(frame: pd.DataFrame, category: str, summary: dict[str, Any] | None = None) -> int:
	"""Calculate confidence based on evidence quality and category match.
	
	Factors:
	- Percentage of categorized events matching the suspected category
	- Presence of critical/error severity events
	- Event clustering (multiple events of same category)
	- Total event count (more events = higher confidence)
	"""
	if frame.empty:
		return 25

	# Get summary if not provided
	if summary is None:
		summary = build_operational_snapshot(frame).get("summary", {})
	
	total_events = len(frame)
	critical_events = summary.get("critical_events", 0)
	
	# Base confidence increases with event count (more data = more confidence)
	if total_events >= 20:
		base_confidence = 50
	elif total_events >= 10:
		base_confidence = 45
	elif total_events >= 5:
		base_confidence = 40
	else:
		base_confidence = 35
	
	# Severity multiplier
	severity_boost = 15 if any(str(value).upper() in {"ERROR", "CRITICAL"} for value in frame.get("severity", [])) else 5
	
	# Category match confidence
	if "category" not in frame.columns or "is_critical" not in frame.columns:
		category_boost = 5
	else:
		critical_frame = frame[frame["is_critical"]]
		if not critical_frame.empty:
			category_critical_count = int((critical_frame["category"] == category).sum())
			total_critical = len(critical_frame)
			category_percentage = (category_critical_count / total_critical * 100) if total_critical > 0 else 0
			
			if category_percentage >= 70:
				category_boost = 20
			elif category_percentage >= 50:
				category_boost = 15
			elif category_percentage >= 30:
				category_boost = 10
			else:
				category_boost = 5
			
			# Event clustering bonus
			if category_critical_count >= 3:
				category_boost += 10
			elif category_critical_count >= 2:
				category_boost += 5
		else:
			category_boost = 5
	
	confidence = base_confidence + severity_boost + category_boost
	return max(25, min(95, confidence))


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
	if category == "uncategorized":	
		
		all_sources = dict()
		for d in runbook_hits:
			# Use .get() to default to 0 if the source isn't in the dict yet
			all_sources[d["source"]] = all_sources.get(d["source"], 0) + d["score"]

		max_confidence_category = None
		confidence = 0

		for key, value in all_sources.items():
			if value > confidence:
				confidence = value  # <-- Critical: update the highest confidence tracker
				max_confidence_category = key

		category_mapping = {
			"runbooks/redis_timeout.md": "redis_timeout",
			"runbooks/authentication_failure.md": "authentication_failure",
			"runbooks/api_latency.md": "api_latency",
			"runbooks/dns_failure.md": "dns_failure",
			"runbooks/oomkilled.md": "oomkilled",
			"runbooks/memory_leak.md": "memory_leak",
			"runbooks/disk_full.md": "disk_full",
			"runbooks/network_partition.md": "network_partition",
			"runbooks/load_balancer_failure.md": "load_balancer_failure",
			"runbooks/deployment_failure.md": "deployment_failure",
			"runbooks/dependency_outage.md": "dependency_outage",
			"runbooks/message_queue_backlog.md": "message_queue_backlog",
			"runbooks/cache_stampede.md": "cache_stampede",
			"runbooks/service_discovery_failure.md": "service_discovery_failure",
			"runbooks/rate_limit_exceeded.md": "rate_limit_exceeded",
			"runbooks/ssl_certificate_expired.md": "ssl_certificate_expired",
			"runbooks/mysql_lock_contention.md": "mysql_lock_contention",
			"runbooks/postgres_timeout.md": "postgres_timeout",
			"runbooks/high_cpu.md": "high_cpu",
			"runbooks/crashloopbackoff.md": "crashloopbackoff",
		}
		max_confidence_category = max_confidence_category.replace("\\", "/")
		category = category_mapping[max_confidence_category]
	# Get top events for better root cause insight
	top_events = milestone_events(frame, limit=3)
	top_message = None
	
	# First, try to get message from category table
	category_table = snapshot.get("category_table", [])
	if category_table:
		top_message = category_table[0].get("sample_message")
	
	# If we don't have a good top message, use the first milestone event
	if not top_message and top_events:
		top_message = top_events[0].get("message", "")

	root_cause, remediation = _fallback_root_cause(category, top_message)
	confidence = _confidence_from_frame(frame, category, summary)
	impact = _calculate_impact(frame, summary)
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
		impact=impact,
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
