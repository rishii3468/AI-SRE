"""Postmortem report generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from analyzer import IncidentAnalysis, analysis_to_dict
from timeline import format_timeline_markdown

import ollama
import requests


import json




def _call_ollama_text(prompt: str, model: str | None = None) -> str | None:
    """Ask Ollama for a raw text response (Markdown) using a direct HTTP POST request."""
    # Use your target model variant verified by the test script
    model_name = model or "qwen2.5:7b" 
    ollama_url = "http://localhost:11434/api/generate"
    
    # Payload matching your test script configurations
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False  # Keeps response unified in one block instead of a stream chunk loop
    }
    
    try:
        # Send HTTP POST request directly to the Ollama backend engine
        response = requests.post(ollama_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            # Extract the raw markdown text string content directly
            return result.get("response", "")
        else:
            print(f"Ollama HTTP Error: Server responded with status code {response.status_code}")
            print(f"Error payload: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"Ollama Timeout: Model '{model_name}' timed out during postmortem generation.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ollama Connection Error: Failed to reach Ollama daemon. Exception: {e}")
        return None





def _call_ollama_text(prompt: str, model: str | None = None) -> str | None:
    """Ask Ollama for a free-form raw text response (Markdown)."""
    # Ensure ollama is available in scope
    global ollama
    if ollama is None:
        try:
            import ollama
        except ImportError:
            return None

    model_name = model or "gemma3:1b"
    
    try:
        # We drop format="json" and system_message to allow raw text/markdown generation
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        
        # Safely extract text content from the Ollama ChatResponse object
        if hasattr(response, 'message') and hasattr(response.message, 'content'):
            return response.message.content
        elif isinstance(response, dict):
            return response.get("message", {}).get("content")
        return None
        
    except Exception as e:
        print(f"Ollama text generation failed: {e}")
        return None


def build_postmortem_markdown(
    analysis: IncidentAnalysis | dict[str, Any],
    timeline_frame: pd.DataFrame,
    impact: str | None = None,
) -> str:
    data = (
        analysis_to_dict(analysis)
        if isinstance(analysis, IncidentAnalysis)
        else analysis
    )

    timeline_md = format_timeline_markdown(timeline_frame)

    runbooks = [
        {
            "title": hit.get("title"),
            "score": hit.get("score"),
            "source": hit.get("source"),
        }
        for hit in data.get("runbooks", []) or []
    ]

    prompt_payload = {
        "root_cause": data.get("root_cause"),
        "confidence": data.get("confidence"),
        "suspected_category": data.get("suspected_category"),
        "incident_window": data.get("incident_window"),
        "impact": impact or data.get("impact"),
        "evidence": data.get("evidence", []),
        "recommended_actions": data.get("recommended_actions", []),
        "runbooks": runbooks,
    }

    analysis_json = json.dumps(
        prompt_payload,
        indent=2,
        default=str,
        ensure_ascii=False,
    )

    prompt = f"""
You are a senior Site Reliability Engineer.

Generate a professional incident postmortem in markdown.

Requirements:
- Use markdown headings.
- Do not invent facts.
- Use only the provided information.
- If information is missing, state "Unknown".
- Be concise but thorough.
- Include all sections below.
- Do not respond in json format. Return raw Markdown.
- Do not make each line too long.

Required Sections:

# Incident Postmortem

## Summary

## Impact

## Timeline

## Root Cause Analysis

## Evidence

## Retrieved Runbooks

## Recommended Actions

## Prevention

Incident Analysis:
```json
{analysis_json}
```

Timeline:
{timeline_md}
"""

    # CHANGED: Now calling the text-based wrapper instead of the JSON parser
    report = _call_ollama_text(prompt)

    if not report or not str(report).strip():
        raise RuntimeError("Failed to generate postmortem report from Ollama")

    return str(report).strip() + "\n"


# def write_postmortem_report(
#     output_path: str | Path,
#     analysis: IncidentAnalysis | dict[str, Any],
#     timeline_frame: pd.DataFrame,
#     impact: str | None = None,
# ) -> Path:
#     path = Path(output_path)
#     path.parent.mkdir(parents=True, exist_ok=True)

#     report = build_postmortem_markdown(
#         analysis=analysis,
#         timeline_frame=timeline_frame,
#         impact=impact,
#     )

#     path.write_text(report, encoding="utf-8")

#     return path

def write_postmortem_report(
    output_path: str | Path,
    analysis: IncidentAnalysis | dict[str, Any],
    timeline_frame: pd.DataFrame,
    impact: str | None = None,
) -> Path:
    """Generate a Markdown postmortem report and save it to disk."""
    # Ensure the path ends with a .md markdown extension
    path = Path(output_path).with_suffix(".md")
    path.parent.mkdir(parents=True, exist_ok=True)

    # This calls our newly updated HTTP-requests text generator
    report = build_postmortem_markdown(
        analysis=analysis,
        timeline_frame=timeline_frame,
        impact=impact,
    )

    # Write the raw Markdown string directly to the file
    path.write_text(report, encoding="utf-8")

    return path


__all__ = [
    "build_postmortem_markdown",
    "write_postmortem_report",
]