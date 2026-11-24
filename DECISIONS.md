# NexusDB Architectural & Design Decisions

This document records architectural, safety, and implementation decisions made in accordance with the NexusDB Master Build Prompt.

1. **Dual Database Adapter Support (PostgreSQL 16 Primary + SQLite Local Development Engine)**
   - *Context:* The production system targets PostgreSQL 16 with schemas (`bank`, `app`, `audit`) and roles (`nexus_owner`, `nexus_reader`, `nexus_writer`). In environments where Docker or PostgreSQL service is not active, a SQLite adapter simulates identical schema namespacing, constraints, and read-only transaction execution.
   - *Decision:* Build unified execution semantics in `executor.py` that connects to PostgreSQL 16 when `DATABASE_URL_READER` / `DATABASE_URL_OWNER` are reachable, and smoothly falls back to SQLite for local standalone development and CI without requiring a live Postgres instance.

2. **Deterministic FakeLLM in DEMO_MODE**
   - *Context:* System must run completely offline without an API key (`DEMO_MODE=true`).
   - *Decision:* FakeLLM provides pre-scripted high-precision SQL queries for representative banking questions. To showcase the self-correcting reflection loop, a deliberate fault injection triggers on attempt 1 (e.g. querying a non-existent column `c.credit_score`), PostgreSQL/SQLite rejects it, and attempt 2 repairs it to `credit_scores cs JOIN ... ON cs.customer_id = c.customer_id`.

3. **Deterministic Fast Embeddings for ChromaDB**
   - *Context:* Embeddings must work offline without external dependencies or heavy model downloads when needed.
   - *Decision:* Semantic memory supports configurable embedding backend (`EMBEDDING_BACKEND=local | gemini`). Local mode uses ChromaDB's default or TF-IDF/mini-embedding representation for instant startup and zero network latency.

4. **Sequential Multi-Agent Architecture with Strict Pydantic Contracts**
   - *Context:* Orchestrator -> Query Agent -> Analysis Agent -> Visualization Agent.
   - *Decision:* Agents communicate purely through serialized Pydantic contracts (`QueryRequest`, `QueryResult`, `AnalysisResult`, `VizSpec`) with zero shared mutable state ("zero state leakage").

5. **Tamper-Evident SHA-256 Audit Chain with Advisory Locking**
   - *Context:* Audit trail must be mathematically provable and detect tampering.
   - *Decision:* Every row stores `row_hash = SHA256(prev_hash + canonical_json(seq, ts, request_id, user_id, event_type, status, payload))` with genesis hash of 64 zeros. Append operations are strictly serialized, and `verify_chain()` walks the chain to confirm cryptographic integrity.
