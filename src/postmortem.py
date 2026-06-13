"""Postmortem report generation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from analyzer import IncidentAnalysis, analysis_to_dict
from timeline import format_timeline_markdown

import ollama
import requests
# def _format_list(items: list[str]) -> str:
# 	if not items:
# 		return "- None"
# 	return "\n".join(f"- {item}" for item in items)


# def build_postmortem_markdown(
# 	analysis: IncidentAnalysis | dict[str, Any],
# 	timeline_frame: pd.DataFrame,
# 	impact: str | None = None,
# ) -> str:
# 	"""Render a postmortem-ready markdown document."""

# 	data = analysis_to_dict(analysis) if isinstance(analysis, IncidentAnalysis) else analysis
# 	incident_window = data.get("incident_window", (None, None))
# 	if isinstance(incident_window, tuple):
# 		start, end = incident_window
# 	else:
# 		start, end = None, None

# 	runbooks = data.get("runbooks", []) or []
# 	runbook_lines = []
# 	for hit in runbooks:
# 		title = hit.get("title", "Unknown Runbook")
# 		score = hit.get("score", 0.0)
# 		runbook_lines.append(f"- {title} (score: {score:.4f})")

# 	report = [
# 		"# Incident Postmortem",
# 		"",
# 		"## Summary",
# 		f"Root cause: {data.get('root_cause', 'Unknown')}",
# 		f"Confidence: {data.get('confidence', 0)}%",
# 		f"Suspected category: {data.get('suspected_category', 'uncategorized')}",
# 		f"Incident window: {start or 'unknown'} to {end or 'unknown'}",
# 		"",
# 		"## Impact",
# 		impact or data.get('impact', 'Impact not provided.'),
# 		"",
# 		"## Timeline",
# 		format_timeline_markdown(timeline_frame),
# 		"",
# 		"## Evidence",
# 		_format_list(list(data.get('evidence', []))),
# 		"",
# 		"## Retrieved Runbooks",
# 		"\n".join(runbook_lines) if runbook_lines else "- None",
# 		"",
# 		"## Recommended Actions",
# 		_format_list(list(data.get('recommended_actions', []))),
# 		"",
# 		"## Prevention",
# 		"- Review alert thresholds and paging rules",
# 		"- Add or update runbooks for the identified failure mode",
# 		"- Capture follow-up actions and owners",
# 	]
# 	return "\n".join(report).strip() + "\n"


# def write_postmortem_report(
# 	output_path: str | Path,
# 	analysis: IncidentAnalysis | dict[str, Any],
# 	timeline_frame: pd.DataFrame,
# 	impact: str | None = None,
# ) -> Path:
# 	"""Write the generated postmortem markdown to disk."""

# 	path = Path(output_path)
# 	path.parent.mkdir(parents=True, exist_ok=True)
# 	path.write_text(build_postmortem_markdown(analysis, timeline_frame, impact=impact), encoding="utf-8")
# 	return path


# __all__ = ["build_postmortem_markdown", "write_postmortem_report"]


# """Postmortem report generation utilities."""

# from __future__ import annotations

import json
# from pathlib import Path
# from typing import Any

# import pandas as pd

# from analyzer import IncidentAnalysis, analysis_to_dict, _call_ollama
# from timeline import format_timeline_markdown


def _format_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)



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



# def _call_ollama_text(prompt: str, model: str | None = None) -> str | None:
#     """Ask Ollama for a raw text response (Markdown) without forcing JSON format."""
#     if ollama is None:
#         return None

#     model_name = model or "gemma3:1b"
    
#     try:
#         response = ollama.chat(
#             model=model_name,
#             messages=[
#                 {"role": "user", "content": prompt},
#             ],
#             # REMOVED: format="json" is omitted so the model can write free-form Markdown
#         )
        
#         # Handle ChatResponse object attributes or dictionary fallback safely
#         if hasattr(response, 'message') and hasattr(response.message, 'content'):
#             return response.message.content
#         elif isinstance(response, dict):
#             return response.get("message", {}).get("content")
#         return None
        
#     except Exception as e:
#         print(f"Ollama text generation failed: {e}")
#         return None




# def build_postmortem_markdown(
#     analysis: IncidentAnalysis | dict[str, Any],
#     timeline_frame: pd.DataFrame,
#     impact: str | None = None,
# ) -> str:
#     data = (
#         analysis_to_dict(analysis)
#         if isinstance(analysis, IncidentAnalysis)
#         else analysis
#     )

#     timeline_md = format_timeline_markdown(timeline_frame)

#     runbooks = [
#         {
#             "title": hit.get("title"),
#             "score": hit.get("score"),
#             "source": hit.get("source"),
#         }
#         for hit in data.get("runbooks", []) or []
#     ]

#     prompt_payload = {
#         "root_cause": data.get("root_cause"),
#         "confidence": data.get("confidence"),
#         "suspected_category": data.get("suspected_category"),
#         "incident_window": data.get("incident_window"),
#         "impact": impact or data.get("impact"),
#         "evidence": data.get("evidence", []),
#         "recommended_actions": data.get("recommended_actions", []),
#         "runbooks": runbooks,
#     }

#     analysis_json = json.dumps(
#         prompt_payload,
#         indent=2,
#         default=str,
#         ensure_ascii=False,
#     )

#     prompt = f"""
# You are a senior Site Reliability Engineer.

# Generate a professional incident postmortem in markdown.

# Requirements:
# - Use markdown headings.
# - Do not invent facts.
# - Use only the provided information.
# - If information is missing, state "Unknown".
# - Be concise but thorough.
# - Include all sections below.
# - Do not respond in json

# Required Sections:

# # Incident Postmortem

# ## Summary

# ## Impact

# ## Timeline

# ## Root Cause Analysis

# ## Evidence

# ## Retrieved Runbooks

# ## Recommended Actions

# ## Prevention

# Incident Analysis:
# ```json
# {analysis_json}
# ```

# Timeline:
# {timeline_md}
# """

#     report = _call_ollama(prompt)

#     if not report or not str(report).strip():
#         raise RuntimeError("Failed to generate postmortem report from Ollama")

#     return str(report).strip() + "\n"


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