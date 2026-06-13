#!/usr/bin/env python3
"""Test event categorization improvements."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parser import parse_log_file
from aggregate import annotate_events, aggregate_events
import pandas as pd

frame = parse_log_file('logs/sample_incident.log')
annotated = annotate_events(frame)

# Show the categorization results
print('=== Event Categorization Results ===')
critical_events = annotated[annotated['is_critical']]
print(f'Total events: {len(frame)}')
print(f'Critical events: {len(critical_events)}')
print()

aggregated = aggregate_events(frame)
print('Category distribution:')
print(aggregated[['category', 'event_count', 'critical_count']].to_string())
print()

print('Uncategorized critical events:')
uncategorized = critical_events[critical_events['category'] == 'uncategorized']
if not uncategorized.empty:
    for idx, row in uncategorized.iterrows():
        print(f'  - {row["message"][:80]}')
else:
    print('  No uncategorized critical events found!')

print()
print('All critical events by category:')
for category in sorted(critical_events['category'].unique()):
    events = critical_events[critical_events['category'] == category]
    print(f'\n{category} ({len(events)} events):')
    for idx, row in events.iterrows():
        print(f'  - {row["message"][:70]}')
