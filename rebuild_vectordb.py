#!/usr/bin/env python3
"""Rebuild the vector store with all runbooks."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embeddings import load_runbook_chunks, runbook_chunks_to_documents, build_embeddings, discover_runbooks
from langchain_chroma import Chroma

# Discover runbooks
runbooks = discover_runbooks()
print(f"Found {len(runbooks)} runbooks:")
for rb in runbooks:
    print(f"  - {rb.name}")
print()

# Load chunks
chunks = load_runbook_chunks()
print(f"Loaded {len(chunks)} chunks from runbooks")

# Convert to documents
documents = runbook_chunks_to_documents(chunks)
print(f"Created {len(documents)} documents")

# Build embeddings
embeddings = build_embeddings()
print(f"Built embeddings model")

# Create vector store (will overwrite existing)
print("\nBuilding vector store...")
vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="vectordb",
    collection_name="runbooks",
)

# Verify
collection = vector_store.get()
print(f"✓ Vector store now contains {len(collection.get('ids', []))} documents")
