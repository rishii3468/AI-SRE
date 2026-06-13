#!/usr/bin/env python3
"""Test dynamic query generation with different incidents."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parser import parse_log_file, parse_log_text
from analyzer import analyze_with_runbooks

# Test 1: Original sample incident (redis/auth)
print("=" * 70)
print("TEST 1: Redis + Authentication Failure Incident")
print("=" * 70)
frame1 = parse_log_file('logs/sample_incident.log')
severity_order = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
frame1_filtered = frame1[frame1["severity"].astype(str).str.upper().map(severity_order).fillna(0) >= 2].copy()

analysis1 = analyze_with_runbooks(frame1_filtered, query=None, top_k=4)
print(f"Category: {analysis1.suspected_category}")
print(f"Confidence: {analysis1.confidence}%")
print(f"Runbooks matched: {len(analysis1.runbooks)}")
for rb in analysis1.runbooks[:2]:
    print(f"  - {rb.get('title')} (score: {rb.get('score'):.4f})")
print()

# Test 2: Hypothetical disk full incident
print("=" * 70)
print("TEST 2: Disk Full Incident")
print("=" * 70)
disk_log = """2026-06-13T11:00:00Z ERROR service1 no space left on device
2026-06-13T11:00:05Z ERROR service1 filesystem full
2026-06-13T11:00:10Z CRITICAL service1 disk full - write failed"""

frame2 = parse_log_text(disk_log)
analysis2 = analyze_with_runbooks(frame2, query=None, top_k=4)
print(f"Category: {analysis2.suspected_category}")
print(f"Confidence: {analysis2.confidence}%")
print(f"Runbooks matched: {len(analysis2.runbooks)}")
for rb in analysis2.runbooks[:2]:
    print(f"  - {rb.get('title')} (score: {rb.get('score'):.4f})")
print()

# Test 3: High CPU incident
print("=" * 70)
print("TEST 3: High CPU Incident")
print("=" * 70)
cpu_log = """2026-06-13T12:00:00Z WARNING cpu_monitor cpu utilization 85%
2026-06-13T12:00:10Z ERROR cpu_monitor cpu utilization 95%
2026-06-13T12:00:20Z CRITICAL cpu_monitor high cpu usage - process unresponsive"""

frame3 = parse_log_text(cpu_log)
analysis3 = analyze_with_runbooks(frame3, query=None, top_k=4)
print(f"Category: {analysis3.suspected_category}")
print(f"Confidence: {analysis3.confidence}%")
print(f"Runbooks matched: {len(analysis3.runbooks)}")
for rb in analysis3.runbooks[:2]:
    print(f"  - {rb.get('title')} (score: {rb.get('score'):.4f})")
