"""
ChromaDB Semantic Memory for Schema Slices, Join Paths, and Business Glossary.
Performs top-k vector retrieval, 1-hop foreign key expansion, and context savings measurement.
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.memory.catalog import get_catalog_snapshot, CatalogSnapshot, TableMetadata

settings = get_settings()

CHROMA_DIR = Path(settings.chroma_path).resolve()
GLOSSARY_PATH = Path(__file__).resolve().parent / "glossary.yaml"


class RetrievedContext:
    def __init__(
        self,
        question: str,
        retrieved_tables: list[str],
        schema_slices: list[str],
        glossary_rules: list[str],
        full_schema_chars: int,
        context_chars: int,
        context_saved_pct: float,
        catalog: CatalogSnapshot,
    ):
        self.question = question
        self.retrieved_tables = retrieved_tables
        self.schema_slices = schema_slices
        self.glossary_rules = glossary_rules
        self.full_schema_chars = full_schema_chars
        self.context_chars = context_chars
        self.context_saved_pct = context_saved_pct
        self.catalog = catalog

    def to_prompt_context(self) -> str:
        parts = ["### RELEVANT DATABASE SCHEMA:"]
        for s in self.schema_slices:
            parts.append(s)
            parts.append("-" * 40)
        
        if self.glossary_rules:
            parts.append("\n### BUSINESS RULES & GLOSSARY:")
            for g in self.glossary_rules:
                parts.append(f"• {g}")

        return "\n".join(parts)


class SchemaMemoryStore:
    def __init__(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name="nexus_schema_slices",
            metadata={"description": "Schema slices, join paths, and business rules"}
        )
        self.catalog = get_catalog_snapshot()
        self._ensure_indexed()

    def _load_glossary(self) -> list[dict[str, Any]]:
        if not GLOSSARY_PATH.exists():
            return []
        with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("terms", [])

    def _calculate_full_schema_chars(self) -> int:
        total = 0
        for tbl in self.catalog.tables.values():
            total += len(tbl.to_slice_text())
        for g in self._load_glossary():
            total += len(str(g))
        return total

    def _ensure_indexed(self):
        """Index catalog and glossary if collection is empty or schema changed."""
        stored_hash = None
        hash_file = CHROMA_DIR / "catalog.hash"
        if hash_file.exists():
            stored_hash = hash_file.read_text(encoding="utf-8").strip()

        if self.collection.count() == 0 or stored_hash != self.catalog.catalog_hash:
            self.reindex()

    def reindex(self):
        """Builds documents of 3 kinds: per table, per FK join path, per glossary entry."""
        print("[*] Indexing schema slices into ChromaDB...")
        # Clear existing
        try:
            self.client.delete_collection("nexus_schema_slices")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection("nexus_schema_slices")

        documents = []
        metadatas = []
        ids = []

        # 1. Documents per table
        for tbl_name, tbl in self.catalog.tables.items():
            doc_text = tbl.to_slice_text()
            documents.append(doc_text)
            metadatas.append({"type": "table", "table_name": tbl_name})
            ids.append(f"table_{tbl_name}")

        # 2. Documents per foreign key join path
        for idx, fk in enumerate(self.catalog.foreign_keys):
            doc_text = f"Join Path between {fk.from_table} and {fk.to_table}: {fk.join_hint}"
            documents.append(doc_text)
            metadatas.append({"type": "join_path", "from_table": fk.from_table, "to_table": fk.to_table})
            ids.append(f"fk_{idx}_{fk.from_table}_{fk.to_table}")

        # 3. Documents per glossary entry
        for idx, item in enumerate(self._load_glossary()):
            term = item.get("term", "")
            defn = item.get("definition", "")
            hint = item.get("sql_hint", "")
            related = ",".join(item.get("related_tables", []))
            doc_text = f"Business Glossary Term '{term}': {defn}. SQL Hint: {hint}. Tables: {related}"
            documents.append(doc_text)
            metadatas.append({"type": "glossary", "term": term, "related_tables": related})
            ids.append(f"glossary_{idx}_{term.replace(' ', '_')}")

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

        hash_file = CHROMA_DIR / "catalog.hash"
        hash_file.write_text(self.catalog.catalog_hash, encoding="utf-8")
        print(f"[+] Successfully indexed {len(documents)} documents in ChromaDB.")

    def retrieve(self, question: str, top_k: int | None = None) -> RetrievedContext:
        k = top_k or settings.top_k_schema_slices
        results = self.collection.query(
            query_texts=[question],
            n_results=min(k, self.collection.count() or 1),
        )

        matched_tables: set[str] = set()
        matched_slices: list[str] = []
        glossary_entries: list[str] = []

        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []

            for doc, meta in zip(docs, metas):
                m_type = meta.get("type")
                if m_type == "table":
                    tbl_name = meta.get("table_name")
                    if tbl_name and tbl_name in self.catalog.tables:
                        matched_tables.add(tbl_name)
                elif m_type == "join_path":
                    f_tbl = meta.get("from_table")
                    t_tbl = meta.get("to_table")
                    if f_tbl in self.catalog.tables:
                        matched_tables.add(f_tbl)
                    if t_tbl in self.catalog.tables:
                        matched_tables.add(t_tbl)
                elif m_type == "glossary":
                    glossary_entries.append(doc)
                    related = meta.get("related_tables", "").split(",")
                    for r in related:
                        r_clean = r.strip().lower()
                        if r_clean in self.catalog.tables:
                            matched_tables.add(r_clean)

        # Keyword booster: check for obvious table mentions in question
        q_lower = question.lower()
        for tbl_name in self.catalog.tables:
            # Check singular/plural
            if re.search(r'\b' + re.escape(tbl_name) + r'\b', q_lower) or \
               re.search(r'\b' + re.escape(tbl_name.rstrip('s')) + r'\b', q_lower):
                matched_tables.add(tbl_name)

        # Always check glossary keywords
        for item in self._load_glossary():
            term = item.get("term", "").lower()
            if term in q_lower or any(word in q_lower for word in term.split()):
                entry_str = f"{item.get('term')}: {item.get('definition')} [SQL: {item.get('sql_hint')}]"
                if entry_str not in glossary_entries:
                    glossary_entries.append(entry_str)
                for r in item.get("related_tables", []):
                    if r.lower() in self.catalog.tables:
                        matched_tables.add(r.lower())

        # 1-Hop Foreign Key Expansion (capped at 4 extra neighbours)
        expanded: set[str] = set(matched_tables)
        hops_added = 0
        for fk in self.catalog.foreign_keys:
            if hops_added >= 4:
                break
            if fk.from_table.lower() in matched_tables and fk.to_table.lower() not in expanded:
                expanded.add(fk.to_table.lower())
                hops_added += 1
            elif fk.to_table.lower() in matched_tables and fk.from_table.lower() not in expanded:
                expanded.add(fk.from_table.lower())
                hops_added += 1

        # Format schema slices
        for tbl_name in sorted(expanded):
            tbl_meta = self.catalog.tables.get(tbl_name)
            if tbl_meta:
                matched_slices.append(tbl_meta.to_slice_text())

        # If nothing matched, include core tables (customers, accounts, transactions)
        if not matched_slices:
            for fallback in ["customers", "accounts", "transactions"]:
                if fallback in self.catalog.tables:
                    matched_slices.append(self.catalog.tables[fallback].to_slice_text())
                    expanded.add(fallback)

        full_schema_chars = self._calculate_full_schema_chars()
        context_str = "\n".join(matched_slices) + "\n".join(glossary_entries)
        context_chars = len(context_str)
        saved_pct = round(max(0.0, (full_schema_chars - context_chars) / full_schema_chars * 100), 1)

        return RetrievedContext(
            question=question,
            retrieved_tables=list(expanded),
            schema_slices=matched_slices,
            glossary_rules=glossary_entries,
            full_schema_chars=full_schema_chars,
            context_chars=context_chars,
            context_saved_pct=saved_pct,
            catalog=self.catalog,
        )

    async def refine(self, ctx: RetrievedContext, err: Any) -> RetrievedContext:
        """Re-retrieves context by appending error text (resolves missing column/table errors)."""
        error_summary = getattr(err, "summary", str(err))
        augmented_query = f"{ctx.question} {error_summary}"
        return self.retrieve(augmented_query)


_memory_instance: SchemaMemoryStore | None = None


def get_schema_memory() -> SchemaMemoryStore:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = SchemaMemoryStore()
    return _memory_instance
