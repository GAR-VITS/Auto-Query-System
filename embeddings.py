"""
ChromaDB vector embedding layer.
"""
from __future__ import annotations

from typing import Any

try:
    from config import get_settings
except ImportError:
    from app.core.config import get_settings

settings = get_settings()

_client = None


def get_client():
    global _client
    if _client is None:
        try:
            import chromadb
            _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        except Exception:
            _client = None
    return _client


def get_schema_collection():
    client = get_client()
    if client is None:
        return None
    try:
        from chromadb.utils import embedding_functions
        return client.get_or_create_collection(
            name=settings.chroma_collection_schema,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )
    except Exception:
        return None


def get_history_collection():
    client = get_client()
    if client is None:
        return None
    try:
        from chromadb.utils import embedding_functions
        return client.get_or_create_collection(
            name=settings.chroma_collection_history,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )
    except Exception:
        return None


def index_schema_documents(documents: list[dict[str, Any]]) -> int:
    if not documents:
        return 0
    collection = get_schema_collection()
    if collection is None:
        return 0
    try:
        collection.upsert(
            ids=[d["id"] for d in documents],
            documents=[d["text"] for d in documents],
            metadatas=[{"table_name": d["table_name"]} for d in documents],
        )
        return len(documents)
    except Exception:
        return 0


def retrieve_relevant_schema(question: str, top_k: int = 5) -> list[str]:
    collection = get_schema_collection()
    if collection is None:
        return []
    try:
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


def store_successful_query(question: str, sql: str) -> None:
    collection = get_history_collection()
    if collection is None:
        return
    try:
        doc_id = f"hist::{abs(hash(question))}"
        collection.upsert(
            ids=[doc_id],
            documents=[question],
            metadatas=[{"sql": sql}],
        )
    except Exception:
        pass


def retrieve_similar_past_queries(question: str, top_k: int = 3) -> list[dict[str, str]]:
    collection = get_history_collection()
    if collection is None:
        return []
    try:
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
        pairs = []
        if results["documents"]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                pairs.append({"question": doc, "sql": meta.get("sql", "")})
        return pairs
    except Exception:
        return []
