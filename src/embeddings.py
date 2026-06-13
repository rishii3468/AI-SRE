"""Runbook embedding and ChromaDB helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_COLLECTION_NAME = "runbooks"
DEFAULT_CHROMA_DIR = Path("vectordb")
DEFAULT_RUNBOOKS_DIR = Path("runbooks")


@dataclass(frozen=True)
class RunbookChunk:
	content: str
	source: str
	title: str
	chunk_index: int


def discover_runbooks(runbooks_dir: str | Path = DEFAULT_RUNBOOKS_DIR) -> list[Path]:
	"""Return all markdown runbooks sorted by name."""

	directory = Path(runbooks_dir)
	if not directory.exists():
		return []
	return sorted(path for path in directory.glob("*.md") if path.is_file())


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
	if not text.strip():
		return []

	if chunk_size <= 0:
		raise ValueError("chunk_size must be greater than zero")

	chunks: list[str] = []
	start = 0
	text_length = len(text)
	while start < text_length:
		end = min(text_length, start + chunk_size)
		chunks.append(text[start:end].strip())
		if end >= text_length:
			break
		start = max(end - overlap, start + 1)
	return [chunk for chunk in chunks if chunk]


def load_runbook_chunks(runbooks_dir: str | Path = DEFAULT_RUNBOOKS_DIR, chunk_size: int = 1200, overlap: int = 180) -> list[RunbookChunk]:
	"""Read runbook markdown files and split them into retrievable chunks."""

	chunks: list[RunbookChunk] = []
	for path in discover_runbooks(runbooks_dir):
		text = path.read_text(encoding="utf-8", errors="replace")
		for index, chunk in enumerate(_chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
			chunks.append(RunbookChunk(content=chunk, source=str(path), title=path.stem, chunk_index=index))
	return chunks


def runbook_chunks_to_documents(chunks: Iterable[RunbookChunk]) -> list[Document]:
	"""Convert chunk records into LangChain documents."""

	documents: list[Document] = []
	for chunk in chunks:
		documents.append(
			Document(
				page_content=chunk.content,
				metadata={"source": chunk.source, "title": chunk.title, "chunk_index": chunk.chunk_index},
			)
		)
	return documents


def build_embeddings(model_name: str = DEFAULT_EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
	"""Create the embedding model used for the runbook vector store.
	
	Uses CPU device explicitly to avoid PyTorch meta tensor issues.
	"""

	return HuggingFaceEmbeddings(
		model_name=model_name,
		model_kwargs={"device": "cpu"},
		encode_kwargs={"normalize_embeddings": True},
	)


def build_vector_store(
	runbooks_dir: str | Path = DEFAULT_RUNBOOKS_DIR,
	persist_directory: str | Path = DEFAULT_CHROMA_DIR,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Chroma:
	"""Embed the runbooks and persist them to ChromaDB."""

	chunks = load_runbook_chunks(runbooks_dir=runbooks_dir)
	documents = runbook_chunks_to_documents(chunks)
	embeddings = build_embeddings(model_name=model_name)
	persist_path = Path(persist_directory)
	persist_path.mkdir(parents=True, exist_ok=True)
	return Chroma.from_documents(
		documents=documents,
		embedding=embeddings,
		persist_directory=str(persist_path),
		collection_name=collection_name,
	)


def load_vector_store(
	persist_directory: str | Path = DEFAULT_CHROMA_DIR,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Chroma:
	"""Load an existing ChromaDB store from disk."""

	embeddings = build_embeddings(model_name=model_name)
	return Chroma(
		collection_name=collection_name,
		persist_directory=str(Path(persist_directory)),
		embedding_function=embeddings,
	)


def ensure_vector_store(
	runbooks_dir: str | Path = DEFAULT_RUNBOOKS_DIR,
	persist_directory: str | Path = DEFAULT_CHROMA_DIR,
	collection_name: str = DEFAULT_COLLECTION_NAME,
	model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> Chroma:
	"""Load the vector store, building it first if needed."""

	persist_path = Path(persist_directory)
	if not persist_path.exists() or not any(persist_path.iterdir()):
		return build_vector_store(
			runbooks_dir=runbooks_dir,
			persist_directory=persist_directory,
			collection_name=collection_name,
			model_name=model_name,
		)
	return load_vector_store(persist_directory=persist_directory, collection_name=collection_name, model_name=model_name)


__all__ = [
	"DEFAULT_CHROMA_DIR",
	"DEFAULT_COLLECTION_NAME",
	"DEFAULT_EMBEDDING_MODEL",
	"DEFAULT_RUNBOOKS_DIR",
	"RunbookChunk",
	"build_embeddings",
	"build_vector_store",
	"discover_runbooks",
	"ensure_vector_store",
	"load_runbook_chunks",
	"load_vector_store",
	"runbook_chunks_to_documents",
]
