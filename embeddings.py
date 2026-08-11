"""
ChromaDB layer — the "Any Vector Database" step in the pipeline.

Two collections:
- schema_context: embedded table/column docs, used for nearest-context
  retrieval when generating SQL.
- query_history: past (question -> working SQL) pairs, so the agent
  can retrieve similar solved queries instead of starting cold every time.
"""
from __future__ import annotations

from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from app.config import get_settings

settings = get_settings()

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def _embedding_fn():
    # Uses a local sentence-transformers model by default (no extra API
    # cost/latency for embeddings — only Gemini calls are for generation).
    return embedding_functions.DefaultEmbeddingFunction()


def get_schema_collection():
    return get_client().get_or_create_collection(
        name=settings.chroma_collection_schema,
        embedding_function=_embedding_fn(),
    )


def get_history_collection():
    return get_client().get_or_create_collection(
        name=settings.chroma_collection_history,
        embedding_function=_embedding_fn(),
    )


def index_schema_documents(documents: list[dict[str, Any]]) -> int:
    """Upserts table-level schema docs. Call this once at startup / on schema change."""
    if not documents:
        return 0
    collection = get_schema_collection()
    collection.upsert(
        ids=[d["id"] for d in documents],
        documents=[d["text"] for d in documents],
        metadatas=[{"table_name": d["table_name"]} for d in documents],
    )
    return len(documents)


def retrieve_relevant_schema(question: str, top_k: int = 5) -> list[str]:
    """Semantic search: nearest table docs to the user's question."""
    collection = get_schema_collection()
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
    return results["documents"][0] if results["documents"] else []


def store_successful_query(question: str, sql: str) -> None:
    """Remembers a (question, working SQL) pair for future few-shot retrieval."""
    collection = get_history_collection()
    doc_id = f"hist::{abs(hash(question))}"
    collection.upsert(
        ids=[doc_id],
        documents=[question],
        metadatas=[{"sql": sql}],
    )


def retrieve_similar_past_queries(question: str, top_k: int = 3) -> list[dict[str, str]]:
    collection = get_history_collection()
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
    pairs = []
    if results["documents"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            pairs.append({"question": doc, "sql": meta.get("sql", "")})
    return pairs
