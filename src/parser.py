"""Incident log parsing utilities.

The parser turns raw log text into a structured pandas DataFrame so downstream
modules can aggregate events, build timelines, and retrieve relevant runbooks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd


TIMESTAMP_PATTERNS = (
	"%Y-%m-%dT%H:%M:%S.%fZ",
	"%Y-%m-%dT%H:%M:%SZ",
	"%Y-%m-%d %H:%M:%S,%f",
	"%Y-%m-%d %H:%M:%S.%f",
	"%Y-%m-%d %H:%M:%S",
	"%b %d %H:%M:%S",
	"%b %d %H:%M:%S.%f",
)

SEVERITY_ALIASES = {
	"trace": "TRACE",
	"debug": "DEBUG",
	"info": "INFO",
	"information": "INFO",
	"warn": "WARNING",
	"warning": "WARNING",
	"error": "ERROR",
	"err": "ERROR",
	"critical": "CRITICAL",
	"crit": "CRITICAL",
	"fatal": "CRITICAL",
	"severe": "CRITICAL",
}

SEVERITY_RANK = {
	"TRACE": 10,
	"DEBUG": 20,
	"INFO": 30,
	"WARNING": 40,
	"ERROR": 50,
	"CRITICAL": 60,
}

ISO_TIMESTAMP_RE = re.compile(
	r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,6})?(?:Z|[+-]\d{2}:?\d{2})?)"
)
BRACKET_TIMESTAMP_RE = re.compile(r"\[(?P<timestamp>[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\]")
SYSLOG_TIMESTAMP_RE = re.compile(r"^(?P<timestamp>[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)\s+")
LEVEL_RE = re.compile(r"\b(?P<level>TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|ERR|CRITICAL|CRIT|FATAL)\b", re.IGNORECASE)
KEY_VALUE_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_\-]*)=(?P<value>\"[^\"]*\"|'[^']*'|[^\s]+)")
COMPONENT_RE = re.compile(r"(?:^|\s)(?:component|service|module|app|source)=([^\s]+)", re.IGNORECASE)


@dataclass(frozen=True)
class LogRecord:
	"""Structured representation of a single log line."""

	timestamp: Optional[datetime]
	severity: str
	service: Optional[str]
	component: Optional[str]
	message: str
	raw_line: str
	line_number: int
	metadata: dict[str, Any] = field(default_factory=dict)


def parse_timestamp(value: str) -> Optional[datetime]:
	"""Parse a timestamp string using a small set of common log formats."""

	cleaned = value.strip().rstrip(",")
	cleaned = cleaned.replace(",", ".", 1) if "," in cleaned and "." not in cleaned else cleaned
	if cleaned.endswith("Z"):
		cleaned = cleaned[:-1] + "+00:00"

	for pattern in TIMESTAMP_PATTERNS:
		try:
			parsed = datetime.strptime(cleaned, pattern)
			if pattern.startswith("%b "):
				parsed = parsed.replace(year=datetime.now(timezone.utc).year)
			return parsed
		except ValueError:
			continue

	try:
		return datetime.fromisoformat(cleaned)
	except ValueError:
		return None


def normalize_severity(value: Optional[str]) -> str:
	"""Normalize severity labels to a canonical uppercase form."""

	if not value:
		return "INFO"
	normalized = SEVERITY_ALIASES.get(value.strip().lower(), value.strip().upper())
	return normalized if normalized in SEVERITY_RANK else "INFO"


def _unquote(value: str) -> str:
	if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
		return value[1:-1]
	return value


def _parse_key_values(line: str) -> dict[str, str]:
	return {match.group("key"): _unquote(match.group("value")) for match in KEY_VALUE_RE.finditer(line)}


def _extract_timestamp(line: str, metadata: dict[str, Any]) -> tuple[Optional[datetime], str]:
	match = ISO_TIMESTAMP_RE.search(line) or BRACKET_TIMESTAMP_RE.search(line) or SYSLOG_TIMESTAMP_RE.search(line)
	if not match:
		return None, line.strip()

	timestamp = parse_timestamp(match.group("timestamp"))
	remaining = (line[: match.start()] + line[match.end() :]).strip()
	metadata["timestamp_raw"] = match.group("timestamp")
	return timestamp, remaining


def _extract_severity(line: str, metadata: dict[str, Any]) -> tuple[str, str]:
	match = LEVEL_RE.search(line)
	if not match:
		return "INFO", line

	severity = normalize_severity(match.group("level"))
	metadata["severity_raw"] = match.group("level")
	cleaned = (line[: match.start()] + line[match.end() :]).strip()
	return severity, cleaned


def _extract_component(line: str, metadata: dict[str, Any]) -> tuple[Optional[str], str]:
	key_values = _parse_key_values(line)
	for key in ("service", "component", "module", "app", "source"):
		if key in key_values:
			component = key_values[key]
			metadata.setdefault("fields", {}).update(key_values)
			return component, line

	match = COMPONENT_RE.search(line)
	if match:
		return match.group(1), line

	return None, line


def parse_log_line(line: str, line_number: int = 1) -> Optional[LogRecord]:
	"""Parse one log line into a structured record.

	The parser is deliberately permissive. If it cannot identify any useful
	structure, it still returns a record with the raw line so the caller can
	keep the evidence.
	"""

	raw_line = line.rstrip("\n")
	if not raw_line.strip():
		return None

	metadata: dict[str, Any] = {}
	timestamp, remaining = _extract_timestamp(raw_line, metadata)
	severity, remaining = _extract_severity(remaining, metadata)
	component, remaining = _extract_component(remaining, metadata)

	key_values = _parse_key_values(raw_line)
	if key_values:
		metadata.setdefault("fields", {}).update(key_values)

	service = key_values.get("service") or key_values.get("app") or key_values.get("module")
	message = remaining.strip() or raw_line.strip()

	return LogRecord(
		timestamp=timestamp,
		severity=severity,
		service=service,
		component=component,
		message=message,
		raw_line=raw_line,
		line_number=line_number,
		metadata=metadata,
	)


def parse_log_text(text: str) -> pd.DataFrame:
	"""Parse a block of incident logs into a pandas DataFrame."""

	records = [record for idx, line in enumerate(text.splitlines(), start=1) if (record := parse_log_line(line, idx))]
	return _records_to_frame(records)


def parse_log_file(file_path: str | Path, encoding: str = "utf-8") -> pd.DataFrame:
	"""Parse a log file from disk into a pandas DataFrame."""

	path = Path(file_path)
	text = path.read_text(encoding=encoding, errors="replace")
	frame = parse_log_text(text)
	if not frame.empty:
		frame.insert(0, "source_file", str(path))
	else:
		frame = pd.DataFrame(columns=["source_file", "timestamp", "severity", "service", "component", "message", "raw_line", "line_number", "metadata"])
	return frame


def parse_log_sources(sources: Iterable[str | Path]) -> pd.DataFrame:
	"""Parse multiple files and concatenate them into one DataFrame."""

	frames = [parse_log_file(source) for source in sources]
	if not frames:
		return _empty_frame()
	return pd.concat(frames, ignore_index=True)


def detect_incident_window(frame: pd.DataFrame) -> tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
	"""Return the first and last timestamps available in a parsed log frame."""

	if frame.empty or "timestamp" not in frame:
		return None, None

	timestamps = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
	valid = timestamps.dropna()
	if valid.empty:
		return None, None
	return valid.min(), valid.max()


def extract_critical_events(frame: pd.DataFrame, minimum_severity: str = "ERROR") -> pd.DataFrame:
	"""Filter records at or above the requested severity."""

	if frame.empty or "severity" not in frame:
		return frame.copy()

	threshold = SEVERITY_RANK.get(normalize_severity(minimum_severity), SEVERITY_RANK["ERROR"])
	normalized = frame.copy()
	normalized["severity"] = normalized["severity"].astype(str).map(normalize_severity)
	severity_rank = normalized["severity"].map(lambda value: SEVERITY_RANK.get(value, SEVERITY_RANK["INFO"]))
	return normalized.loc[severity_rank >= threshold].reset_index(drop=True)


def frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
	"""Convert a parsed DataFrame back to serializable dictionaries."""

	if frame.empty:
		return []
	return [
		{
			**row,
			"timestamp": row["timestamp"].isoformat() if pd.notna(row["timestamp"]) else None,
		}
		for row in frame.to_dict(orient="records")
	]


def _records_to_frame(records: list[LogRecord]) -> pd.DataFrame:
	if not records:
		return _empty_frame()

	frame = pd.DataFrame([asdict(record) for record in records])
	if not frame.empty:
		frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
		frame = frame.sort_values(by=["timestamp", "line_number"], na_position="last").reset_index(drop=True)
	return frame


def _empty_frame() -> pd.DataFrame:
	return pd.DataFrame(
		columns=["source_file", "timestamp", "severity", "service", "component", "message", "raw_line", "line_number", "metadata"]
	)


__all__ = [
	"LogRecord",
	"detect_incident_window",
	"extract_critical_events",
	"frame_to_records",
	"normalize_severity",
	"parse_log_file",
	"parse_log_line",
	"parse_log_sources",
	"parse_log_text",
	"parse_timestamp",
]
