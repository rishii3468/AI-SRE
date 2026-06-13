"""Event aggregation helpers for parsed incident logs."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

import pandas as pd

from parser import extract_critical_events, normalize_severity


EVENT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
	"redis_timeout": (
		"redis timeout",
		"redis command",
		"connection pool",
		"no available connections",
		"connection acquisition timeout",
		"connection unavailable",
	),
	"authentication_failure": (
		"authentication failed",
		"auth failure",
		"session validation timeout",
		"login failed",
		"authentication failure rate",
	),
	"api_latency": (
		"latency",
		"slow response",
		"p95",
		"p99",
		"p50",
		"api availability",
	),
	"dns_failure": (
		"dns",
		"name resolution",
		"resolve host",
		"temporary failure in name resolution",
	),
	"oomkilled": (
		"oomkilled",
		"out of memory",
		"killed process",
		"memory cgroup",
	),
	"memory_leak": (
		"memory leak",
		"heap growth",
		"rss",
		"memory usage increased",
	),
	"disk_full": (
		"no space left on device",
		"disk full",
		"filesystem full",
	),
	"network_partition": (
		"network unreachable",
		"connection reset",
		"broken pipe",
		"network partition",
	),
	"load_balancer_failure": (
		"503",
		"502",
		"bad gateway",
		"load balancer",
	),
	"deployment_failure": (
		"deploy",
		"rollback",
		"release failed",
		"startup failed",
	),
	"dependency_outage": (
		"downstream",
		"dependency",
		"upstream",
		"service unavailable",
	),
	"message_queue_backlog": (
		"backlog",
		"queue depth",
		"consumer lag",
		"lagging",
	),
	"cache_stampede": (
		"cache miss",
		"stampede",
		"thundering herd",
	),
	"service_discovery_failure": (
		"service discovery",
		"discovery",
		"endpoint not found",
	),
	"rate_limit_exceeded": (
		"rate limit",
		"too many requests",
		"429",
	),
	"ssl_certificate_expired": (
		"certificate expired",
		"ssl",
		"tls handshake failed",
	),
	"mysql_lock_contention": (
		"lock wait timeout",
		"deadlock",
		"mysql lock",
	),
	"postgres_timeout": (
		"postgres",
		"query timeout",
		"statement timeout",
	),
	"high_cpu": (
		"high cpu",
		"cpu utilization",
		"cpu usage",
		"cpu exceeded",
	),
	"crashloopbackoff": (
		"crashloopbackoff",
		"crash loop",
		"restart loop",
		"container exited",
	),
}


@dataclass(frozen=True)
class EventSummary:
	total_events: int
	critical_events: int
	severity_counts: dict[str, int]
	category_counts: dict[str, int]
	top_services: list[tuple[str, int]]
	top_components: list[tuple[str, int]]


def categorize_message(message: str) -> str:
	"""Map a raw message to a coarse incident category."""

	lowered = message.lower()
	for category, keywords in EVENT_CATEGORY_KEYWORDS.items():
		if any(keyword in lowered for keyword in keywords):
			return category
	return "uncategorized"


def annotate_events(frame: pd.DataFrame) -> pd.DataFrame:
	"""Attach derived aggregation columns to a parsed log frame."""

	if frame.empty:
		return frame.copy()

	annotated = frame.copy()
	annotated["severity"] = annotated.get("severity", pd.Series(dtype=str)).astype(str).map(normalize_severity)
	annotated["category"] = annotated.get("message", pd.Series(dtype=str)).astype(str).map(categorize_message)
	annotated["is_critical"] = annotated["severity"].isin(["ERROR", "CRITICAL"])
	return annotated


def aggregate_events(frame: pd.DataFrame) -> pd.DataFrame:
	"""Return one row per derived category with counts and example evidence."""

	annotated = annotate_events(frame)
	if annotated.empty:
		return pd.DataFrame(columns=["category", "event_count", "critical_count", "first_seen", "last_seen", "sample_message"])

	grouped = annotated.groupby("category", dropna=False)
	aggregated = grouped.agg(
		event_count=("message", "size"),
		critical_count=("is_critical", "sum"),
		first_seen=("timestamp", "min"),
		last_seen=("timestamp", "max"),
		sample_message=("message", "first"),
	).reset_index()
	return aggregated.sort_values(by=["critical_count", "event_count"], ascending=False).reset_index(drop=True)


def summarize_events(frame: pd.DataFrame) -> EventSummary:
	"""Build a compact operational summary from the incident log frame."""

	annotated = annotate_events(frame)
	if annotated.empty:
		return EventSummary(0, 0, {}, {}, [], [])

	severity_counts = Counter(annotated["severity"].fillna("INFO"))
	category_counts = Counter(annotated["category"].fillna("uncategorized"))
	service_counts = Counter(annotated["service"].dropna().astype(str))
	component_counts = Counter(annotated["component"].dropna().astype(str))
	critical_events = int(annotated["is_critical"].sum())

	return EventSummary(
		total_events=int(len(annotated)),
		critical_events=critical_events,
		severity_counts=dict(severity_counts),
		category_counts=dict(category_counts),
		top_services=service_counts.most_common(5),
		top_components=component_counts.most_common(5),
	)


def build_operational_snapshot(frame: pd.DataFrame) -> dict[str, Any]:
	"""Create a JSON-friendly incident snapshot for later stages."""

	annotated = annotate_events(frame)
	summary = summarize_events(annotated)
	categories = aggregate_events(annotated)

	return {
		"summary": {
			"total_events": summary.total_events,
			"critical_events": summary.critical_events,
			"severity_counts": summary.severity_counts,
			"category_counts": summary.category_counts,
			"top_services": summary.top_services,
			"top_components": summary.top_components,
		},
		"category_table": categories.to_dict(orient="records"),
		"critical_events": extract_critical_events(annotated).to_dict(orient="records"),
	}


__all__ = [
	"EVENT_CATEGORY_KEYWORDS",
	"EventSummary",
	"aggregate_events",
	"annotate_events",
	"build_operational_snapshot",
	"categorize_message",
	"summarize_events",
]
