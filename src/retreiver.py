"""Retrieval helpers for incident runbooks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_chroma import Chroma

from embeddings import DEFAULT_CHROMA_DIR, DEFAULT_COLLECTION_NAME, DEFAULT_EMBEDDING_MODEL, ensure_vector_store, load_vector_store


def get_retriever(
	persist_directory: str | Path = DEFAULT_CHROMA_DIR,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Chroma:
	"""Return a ready-to-query Chroma vector store."""

	return ensure_vector_store(
		persist_directory=persist_directory,
		collection_name=collection_name,
		model_name=model_name,
	)


def retrieve_runbooks(
	query: str,
	k: int = 4,
	persist_directory: str | Path = DEFAULT_CHROMA_DIR,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict[str, Any]]:
	"""Return the closest matching runbooks for a query string."""

	vector_store = load_vector_store(persist_directory=persist_directory, collection_name=collection_name, model_name=model_name)
	results = vector_store.similarity_search_with_score(query, k=k)
	hits: list[dict[str, Any]] = []
	for document, score in results:
		metadata = dict(document.metadata or {})
		hits.append(
			{
				"content": document.page_content,
				"metadata": metadata,
				"score": float(score),
				"title": metadata.get("title") or Path(metadata.get("source", "unknown")).stem,
				"source": metadata.get("source"),
			}
		)
	return hits


def format_retrieved_runbooks(hits: list[dict[str, Any]]) -> str:
	"""Format retrieval hits into a markdown context block."""

	if not hits:
		return "No relevant runbooks found."

	lines = []
	for hit in hits:
		title = hit.get("title", "Unknown Runbook")
		source = hit.get("source", "")
		score = hit.get("score", 0.0)
		content = hit.get("content", "").strip()
		lines.append(f"## {title}")
		if source:
			lines.append(f"Source: {source}")
		lines.append(f"Score: {score:.4f}")
		lines.append(content)
		lines.append("")
	return "\n".join(lines).strip()


__all__ = ["format_retrieved_runbooks", "get_retriever", "retrieve_runbooks"]
