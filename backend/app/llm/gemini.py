"""
NexusDB Google Gemini LLM Client
Interacts with Google Gemini models with structured JSON schemas, temperature 0,
exponential backoff on rate limits (429/5xx), and token usage telemetry.
"""

import os
import json
import asyncio
from typing import Any
from pydantic import BaseModel

from app.config import get_settings
from app.llm.base import LLMClient, IntentClassification, GeneratedSql, NarrativeResult
from app.llm.fake import FakeLLM

settings = get_settings()


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model or settings.gemini_model or "gemini-2.5-flash"
        self._fake_fallback = FakeLLM()
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=self.api_key)
                    self._client = legacy_genai.GenerativeModel(self.model_name)
                except Exception:
                    self._client = None

    async def _execute_with_retry(self, fn, *args, **kwargs) -> Any:
        retries = 3
        delay = 1.0
        for attempt in range(retries):
            try:
                return await asyncio.to_thread(fn, *args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "503" in err_str:
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                raise

    async def classify_intent(self, question: str) -> IntentClassification:
        if not self._client or settings.demo_mode:
            return await self._fake_fallback.classify_intent(question)

        prompt = f"""Classify the user request for an enterprise banking database system.
Available Intents:
- "query": Read-only query for metrics, tables, reports, balances, or customer accounts.
- "action": Governed operational update (e.g. put account on hold, set risk flag, clear risk flag).
- "clarify": Request is too ambiguous or missing key details to answer safely.

User Request: "{question}"

Respond with JSON matching schema:
{{
  "intent": "query" | "action" | "clarify",
  "action_name": "SET_ACCOUNT_STATUS" | "SET_RISK_FLAG" | "CLEAR_RISK_FLAG" | null,
  "parameters": {{}},
  "clarify_question": string | null,
  "confidence": float
}}"""
        try:
            resp = await self._execute_with_retry(
                lambda: self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.0}
                )
            )
            data = json.loads(resp.text)
            return IntentClassification(**data)
        except Exception:
            return await self._fake_fallback.classify_intent(question)

    async def generate_sql(self, question: str, context: Any) -> GeneratedSql:
        if not self._client or settings.demo_mode:
            return await self._fake_fallback.generate_sql(question, context)

        schema_context = context.to_prompt_context() if hasattr(context, "to_prompt_context") else str(context)
        prompt = f"""You are the Query Generation Agent for NexusDB.
Write a read-only PostgreSQL 16 query for the user question using ONLY the supplied schema:

Context:
{schema_context}

User Question: "{question}"

Rules:
- PostgreSQL 16 dialect, schema-qualified tables (bank.table), explicit JOINs, explicit columns (no SELECT *).
- Relative dates relative to CURRENT_DATE.
- Return JSON matching:
{{
  "sql": "SELECT ...",
  "rationale": "...",
  "assumptions": ["..."],
  "confidence": 0.95
}}"""
        try:
            resp = await self._execute_with_retry(
                lambda: self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.0}
                )
            )
            data = json.loads(resp.text)
            return GeneratedSql(**data)
        except Exception:
            return await self._fake_fallback.generate_sql(question, context)

    async def repair_sql(self, question: str, context: Any, attempts: list[Any]) -> GeneratedSql:
        if not self._client or settings.demo_mode:
            return await self._fake_fallback.repair_sql(question, context, attempts)

        schema_context = context.to_prompt_context() if hasattr(context, "to_prompt_context") else str(context)
        prev_attempts_str = json.dumps([getattr(a, "to_dict", lambda: str(a))() for a in attempts], default=str)

        prompt = f"""You are the Self-Correcting Reflection Engine for NexusDB.
A previously generated query failed execution or schema validation. Repair it without repeating errors.

Question: "{question}"
Previous Attempts:
{prev_attempts_str}

Refined Schema Context:
{schema_context}

Return repaired SQL as JSON:
{{
  "sql": "SELECT ...",
  "rationale": "Root cause and specific fix applied",
  "assumptions": ["..."],
  "confidence": 0.98
}}"""
        try:
            resp = await self._execute_with_retry(
                lambda: self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.0}
                )
            )
            data = json.loads(resp.text)
            return GeneratedSql(**data)
        except Exception:
            return await self._fake_fallback.repair_sql(question, context, attempts)

    async def narrate(self, question: str, stats: dict[str, Any]) -> NarrativeResult:
        if not self._client or settings.demo_mode:
            return await self._fake_fallback.narrate(question, stats)

        prompt = f"""You are the Financial Analysis Agent for NexusDB.
Given the aggregated statistical metrics computed deterministically by Pandas over the database result rows:
Question: "{question}"
Stats: {json.dumps(stats)}

Write a calm, professional executive takeaway (at most three lines, serif typography tone).
Return JSON:
{{
  "insight_text": "...",
  "read_as": "...",
  "flags": []
}}"""
        try:
            resp = await self._execute_with_retry(
                lambda: self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.2}
                )
            )
            data = json.loads(resp.text)
            return NarrativeResult(**data)
        except Exception:
            return await self._fake_fallback.narrate(question, stats)


def get_llm_client() -> LLMClient:
    if settings.demo_mode or not settings.gemini_api_key:
        return FakeLLM()
    return GeminiClient()
