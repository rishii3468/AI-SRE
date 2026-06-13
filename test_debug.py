#!/usr/bin/env python3
"""Debug test for confidence and runbook matching."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parser import parse_log_file
from analyzer import analyze_incident
from retreiver import retrieve_runbooks

# Parse sample log
frame = parse_log_file('logs/sample_incident.log')

# Filter to ERROR/CRITICAL only (default minimum_severity)
severity_order = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
threshold_value = severity_order.get("ERROR", 2)
frame["severity_rank"] = frame["severity"].astype(str).str.upper().map(severity_order).fillna(0)
threshold_frame = frame.loc[frame["severity_rank"] >= threshold_value].drop(columns=["severity_rank"])

print(f"Filtered frame size: {len(threshold_frame)} events")
print()

# Retrieve runbooks with default query
query = "Redis timeout authentication failures"
print(f"Query: '{query}'")
runbook_hits = retrieve_runbooks(query, k=4)
print(f"Runbook hits: {len(runbook_hits)}")
for hit in runbook_hits:
    print(f"  - {hit.get('title')} (score: {hit.get('score'):.4f})")
print()

# Analyze
analysis = analyze_incident(threshold_frame, runbook_hits=runbook_hits)
print(f"Analysis:")
print(f"  Suspected category: {analysis.suspected_category}")
print(f"  Confidence: {analysis.confidence}")
print(f"  Root cause: {analysis.root_cause}")
print(f"  Recommended actions: {analysis.recommended_actions}")
print(f"  Runbooks: {len(analysis.runbooks)} hit(s)")
