import json
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

_api_key = "AQ.Ab8RN6KHrKSCSVWhIXVC8TefEy78Gw2ruW69c0ZmKJiNNoFgxw"
if _api_key:
    genai.configure(api_key=_api_key)


def _ensure_api_key() -> None:
    if not _api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to the project root .env file."
        )


async def generate_sql_and_analysis(user_query: str, schema_info: str) -> dict:
    _ensure_api_key()

    try:
        model = genai.GenerativeModel("gemini-3.1-flash-lite")

        prompt = f"""You are an expert PostgreSQL assistant. Generate a read-only SELECT query.

Database schema:
{schema_info}

User question: {user_query}

Rules:
- Return ONLY valid PostgreSQL SELECT statements (no INSERT, UPDATE, DELETE, DROP, etc.)
- Use table and column names exactly as defined in the schema
- Limit results to 100 rows when appropriate using LIMIT

Return ONLY a valid JSON object with:
- "sql": The raw PostgreSQL SELECT query
- "analysis": A brief 1-2 sentence explanation of what this query does
"""
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text)
        if "sql" not in data:
            raise ValueError("Gemini response missing 'sql' field.")
        return data

    except json.JSONDecodeError as exc:
        raise ValueError("Gemini failed to return valid JSON.") from exc
    except Exception as exc:
        raise RuntimeError(f"Error communicating with Gemini AI: {exc}") from exc
