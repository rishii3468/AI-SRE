"""Streamlit frontend for AI Incident Commander."""

# pyright: reportMissingImports=false, reportMissingModuleSource=false

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
	sys.path.insert(0, str(SRC_DIR))

from aggregate import aggregate_events, build_operational_snapshot
from analyzer import analyze_incident, analyze_with_runbooks
from embeddings import ensure_vector_store
from parser import parse_log_file, parse_log_text
from postmortem import build_postmortem_markdown
from retreiver import retrieve_runbooks
from timeline import build_timeline, format_timeline_markdown


st.set_page_config(
	page_title="AI Incident Commander",
	page_icon="🧭",
	layout="wide",
	initial_sidebar_state="expanded",
)


APP_CSS = """
<style>
:root {
	--bg: #08111f;
	--panel: rgba(13, 24, 42, 0.86);
	--panel-strong: #101c31;
	--text: #edf4ff;
	--muted: #9fb0c8;
	--accent: #7dd3fc;
	--accent-2: #f97316;
	--success: #34d399;
	--warning: #fbbf24;
	--danger: #fb7185;
	--border: rgba(148, 163, 184, 0.22);
}

html, body, [class*="css"] {
	background:
		radial-gradient(circle at top left, rgba(15, 118, 110, 0.28), transparent 30%),
		radial-gradient(circle at top right, rgba(249, 115, 22, 0.18), transparent 26%),
		linear-gradient(180deg, #06101d 0%, #08111f 42%, #0b1627 100%);
	color: var(--text);
}

.block-container {
	padding-top: 1.2rem;
	padding-bottom: 2rem;
}

.hero {
	padding: 1.6rem 1.4rem;
	border: 1px solid var(--border);
	border-radius: 22px;
	background: linear-gradient(135deg, rgba(16, 28, 49, 0.92), rgba(9, 18, 32, 0.88));
	box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
	margin-bottom: 1rem;
}

.hero h1 {
	color: var(--text);
	font-size: 3rem;
	margin-bottom: 0.35rem;
	letter-spacing: -0.04em;
}

.hero p {
	color: var(--muted);
	font-size: 1rem;
	margin-bottom: 0;
	max-width: 72ch;
}

.metric-card {
	background: rgba(16, 28, 49, 0.9);
	border: 1px solid var(--border);
	border-radius: 18px;
	padding: 1rem 1.05rem;
	box-shadow: 0 16px 50px rgba(0, 0, 0, 0.18);
}

.metric-label {
	color: var(--muted);
	font-size: 0.82rem;
	text-transform: uppercase;
	letter-spacing: 0.08em;
	margin-bottom: 0.4rem;
}

.metric-value {
	color: var(--text);
	font-size: 1.8rem;
	font-weight: 700;
	line-height: 1.1;
}

.metric-subtext {
	color: var(--muted);
	font-size: 0.85rem;
	margin-top: 0.25rem;
}

.panel {
	background: var(--panel);
	border: 1px solid var(--border);
	border-radius: 18px;
	padding: 1rem 1rem 0.85rem;
	box-shadow: 0 16px 50px rgba(0, 0, 0, 0.18);
	margin-bottom: 1rem;
}

.panel h2, .panel h3 {
	color: var(--text);
}

.stTabs [data-baseweb="tab-list"] {
	gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
	background: rgba(16, 28, 49, 0.86);
	border: 1px solid var(--border);
	border-radius: 999px;
	color: var(--muted);
	padding: 0.55rem 0.95rem;
}

.stTabs [aria-selected="true"] {
	color: var(--text) !important;
	border-color: rgba(125, 211, 252, 0.45) !important;
}

.stTextArea textarea, .stFileUploader section, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stButton button {
	border-radius: 14px !important;
}

.stButton button {
	background: linear-gradient(135deg, #22c55e 0%, #14b8a6 100%);
	color: #fff;
	border: none;
	font-weight: 700;
	box-shadow: 0 14px 30px rgba(20, 184, 166, 0.24);
}

.stDownloadButton button {
	border-radius: 14px !important;
}

.evidence-box {
	background: rgba(6, 16, 29, 0.72);
	border: 1px solid var(--border);
	border-radius: 16px;
	padding: 0.9rem 1rem;
	color: var(--text);
}

.small-muted {
	color: var(--muted);
	font-size: 0.92rem;
}
</style>
"""


SAMPLE_LOG = ROOT_DIR / "logs" / "sample_incident.log"


def load_default_log_text() -> str:
	if SAMPLE_LOG.exists():
		return SAMPLE_LOG.read_text(encoding="utf-8", errors="replace")
	return ""


@st.cache_resource(show_spinner=False)
def warm_vector_store() -> Optional[object]:
	try:
		return ensure_vector_store()
	except Exception:
		return None


def make_metric(label: str, value: str, subtext: str) -> str:
	return f"""
	<div class="metric-card">
		<div class="metric-label">{label}</div>
		<div class="metric-value">{value}</div>
		<div class="metric-subtext">{subtext}</div>
	</div>
	"""


def render_metrics(frame: pd.DataFrame, analysis: Optional[dict] = None) -> None:
	snapshot = build_operational_snapshot(frame) if not frame.empty else {"summary": {}}
	summary = snapshot.get("summary", {})
	col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.markdown(make_metric("Events", str(summary.get("total_events", 0)), "Parsed from the incident log"), unsafe_allow_html=True)
	with col2:
		st.markdown(make_metric("Critical", str(summary.get("critical_events", 0)), "Errors and critical alerts"), unsafe_allow_html=True)
	with col3:
		root_cause = (analysis or {}).get("root_cause", "Pending analysis")
		st.markdown(make_metric("Root Cause", root_cause[:34] + ("..." if len(root_cause) > 34 else ""), "Best current hypothesis"), unsafe_allow_html=True)
	with col4:
		confidence = f"{(analysis or {}).get('confidence', 0)}%"
		st.markdown(make_metric("Confidence", confidence, "Evidence-backed confidence"), unsafe_allow_html=True)


def render_category_chart(frame: pd.DataFrame) -> None:
	categories = aggregate_events(frame)
	if categories.empty:
		st.info("No categorical signals found yet.")
		return

	chart_frame = categories.head(10).sort_values(by="event_count", ascending=True)
	fig = px.bar(
		chart_frame,
		x="event_count",
		y="category",
		orientation="h",
		color="critical_count",
		color_continuous_scale=["#0f172a", "#7dd3fc", "#f97316"],
		title="Top incident categories",
	)
	fig.update_layout(
		template="plotly_dark",
		height=420,
		margin=dict(l=10, r=10, t=50, b=10),
		paper_bgcolor="rgba(0,0,0,0)",
		plot_bgcolor="rgba(0,0,0,0)",
		font=dict(color="#edf4ff"),
	)
	st.plotly_chart(fig, use_container_width=True)


def load_incident_frame(uploaded_file: Optional[object], raw_text: str) -> pd.DataFrame:
	if uploaded_file is not None:
		text = uploaded_file.read().decode("utf-8", errors="replace")
		return parse_log_text(text)
	return parse_log_text(raw_text)


def build_app_sidebar() -> dict[str, object]:
	st.sidebar.markdown("## Controls")
	source_mode = st.sidebar.radio("Log source", ["Use sample log", "Upload a file", "Paste text"], index=0)
	uploaded_file = None
	pasted_text = ""

	if source_mode == "Upload a file":
		uploaded_file = st.sidebar.file_uploader("Upload incident log", type=["log", "txt", "out", "json"])
	elif source_mode == "Paste text":
		pasted_text = st.sidebar.text_area("Paste incident log", value=load_default_log_text(), height=320)
	else:
		st.sidebar.caption("Using the bundled sample incident log.")

	query = st.sidebar.text_input(
		"Runbook search query",
		value="Redis timeout authentication failures",
		help="Used for retrieval and optional root-cause enrichment.",
	)
	top_k = st.sidebar.slider("Retrieved runbooks", 1, 8, 4)
	minimum_severity = st.sidebar.selectbox("Focus on severity", ["INFO", "WARNING", "ERROR", "CRITICAL"], index=2)
	use_llm = st.sidebar.toggle("Enable LLM prompt generation", value=False)
	build_store = st.sidebar.button("Build / refresh vector store")

	return {
		"source_mode": source_mode,
		"uploaded_file": uploaded_file,
		"pasted_text": pasted_text,
		"query": query,
		"top_k": top_k,
		"minimum_severity": minimum_severity,
		"use_llm": use_llm,
		"build_store": build_store,
	}


def main() -> None:
	st.markdown(APP_CSS, unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="hero">
			<h1>AI Incident Commander</h1>
			<p>Upload incident logs and turn them into timelines, runbook matches, root-cause hypotheses, and postmortem-ready reports.</p>
		</div>
		""",
		unsafe_allow_html=True,
	)

	sidebar_state = build_app_sidebar()

	if sidebar_state["build_store"]:
		with st.spinner("Building vector store from runbooks..."):
			warm_vector_store()
		st.success("Vector store refreshed.")

	with st.spinner("Parsing incident log..."):
		if sidebar_state["source_mode"] == "Upload a file" and sidebar_state["uploaded_file"] is not None:
			incident_frame = load_incident_frame(sidebar_state["uploaded_file"], "")
		elif sidebar_state["source_mode"] == "Paste text":
			incident_frame = load_incident_frame(None, sidebar_state["pasted_text"])
		else:
			incident_frame = parse_log_file(SAMPLE_LOG) if SAMPLE_LOG.exists() else parse_log_text(load_default_log_text())

	if incident_frame.empty:
		st.warning("No log lines were parsed. Provide a log file or paste an incident trace.")
		st.stop()

	render_metrics(incident_frame)

	threshold_frame = incident_frame.copy()
	if "severity" in threshold_frame.columns:
		severity_order = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
		threshold_value = severity_order.get(sidebar_state["minimum_severity"], 2)
		threshold_frame["severity_rank"] = threshold_frame["severity"].astype(str).str.upper().map(severity_order).fillna(0)
		threshold_frame = threshold_frame.loc[threshold_frame["severity_rank"] >= threshold_value].drop(columns=["severity_rank"])

	runbook_hits = retrieve_runbooks(sidebar_state["query"], k=sidebar_state["top_k"])
	analysis = analyze_incident(threshold_frame, runbook_hits=runbook_hits, use_llm=bool(sidebar_state["use_llm"]))
	analysis_dict = analysis.__dict__ if hasattr(analysis, "__dict__") else analysis

	left, right = st.columns([1.15, 0.85], gap="large")
	with left:
		st.markdown('<div class="panel"><h2>Incident Timeline</h2></div>', unsafe_allow_html=True)
		timeline_frame = build_timeline(threshold_frame)
		if timeline_frame.empty:
			st.info("Timeline is empty.")
		else:
			st.dataframe(
				timeline_frame,
				use_container_width=True,
				hide_index=True,
			)

		st.markdown('<div class="panel"><h2>Signal Distribution</h2></div>', unsafe_allow_html=True)
		render_category_chart(threshold_frame)

	with right:
		st.markdown('<div class="panel"><h2>Analysis</h2></div>', unsafe_allow_html=True)
		st.metric("Suspected category", analysis_dict.get("suspected_category", "uncategorized"))
		st.metric("Confidence", f"{analysis_dict.get('confidence', 0)}%")
		st.write(analysis_dict.get("root_cause", "No root cause available."))
		st.markdown("#### Recommended actions")
		for action in analysis_dict.get("recommended_actions", []):
			st.write(f"- {action}")

		st.markdown("#### Evidence")
		for item in analysis_dict.get("evidence", []):
			st.markdown(f'<div class="evidence-box">{item}</div>', unsafe_allow_html=True)

	tabs = st.tabs(["Runbooks", "Postmortem", "Raw Data"])

	with tabs[0]:
		st.markdown('<div class="panel"><h2>Retrieved Runbooks</h2></div>', unsafe_allow_html=True)
		if runbook_hits:
			for hit in runbook_hits:
				title = hit.get("title", "Unknown Runbook")
				score = hit.get("score", 0.0)
				source = hit.get("source", "")
				with st.expander(f"{title}  •  score {score:.4f}", expanded=False):
					if source:
						st.caption(source)
					st.write(hit.get("content", ""))
		else:
			st.info("No runbooks matched the current query.")

	with tabs[1]:
		st.markdown('<div class="panel"><h2>Postmortem Draft</h2></div>', unsafe_allow_html=True)
		postmortem_md = build_postmortem_markdown(analysis, timeline_frame)
		st.download_button(
			"Download postmortem markdown",
			data=postmortem_md,
			file_name="incident_postmortem.md",
			mime="text/markdown",
		)
		st.markdown(postmortem_md)

	with tabs[2]:
		st.markdown('<div class="panel"><h2>Parsed Records</h2></div>', unsafe_allow_html=True)
		st.dataframe(incident_frame, use_container_width=True, hide_index=True)
		st.markdown("#### Timeline Markdown")
		st.code(format_timeline_markdown(incident_frame), language="markdown")


if __name__ == "__main__":
	main()
