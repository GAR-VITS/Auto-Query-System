import json
import logging
import re
from typing import Any, Dict, Optional

import google.generativeai as genai

try:
    from app.core.config import get_settings
except ImportError:
    from backend.app.core.config import get_settings

logger = logging.getLogger("gemini_service")

# Candidate models in order of priority
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
]


def _get_configured_model(model_name: Optional[str] = None) -> genai.GenerativeModel:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    genai.configure(api_key=settings.gemini_api_key)
    chosen_model = model_name or settings.gemini_model
    return genai.GenerativeModel(chosen_model)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON object from model output even if surrounded by text or fences."""
    text = text.strip()

    # Remove markdown ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        clean_text = match.group(1).strip()
    else:
        clean_text = text

    # Try direct parse
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # Try finding outer braces
    brace_match = re.search(r"(\{[\s\S]*\})", clean_text)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from AI response: {text[:200]}")


async def generate_sql_and_analysis(
    user_query: str,
    schema_info: str,
    previous_error: Optional[str] = None,
    previous_sql: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates SQL and a plain-English explanation for a user query.
    If previous_error and previous_sql are provided, it initiates self-correction.
    """
    settings = get_settings()

    correction_prompt = ""
    if previous_error and previous_sql:
        correction_prompt = f"""
IMPORTANT: Your previous SQL attempt resulted in a database error:
Previous SQL: {previous_sql}
Database Error: {previous_error}
Please correct the SQL statement so it executes successfully according to the schema.
"""

    prompt = f"""You are an expert Enterprise Database AI Agent.
You generate valid, optimized SQL queries and plain-English business explanations.

Database Schema Context:
{schema_info}

Rules:
1. Return ONLY read-only SQL queries (SELECT statements or WITH ... SELECT).
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or DDL.
3. Use the exact table and column names from the schema.
4. When joining customers with loans, use customers.customer_id = loan_accounts.customer_id.
5. When filtering by credit score, use credit_reports.credit_score or the comprehensive_client_view.
6. Use LIMIT 50 unless the user asks for aggregations/counts or explicit limits.
7. For full customer name, concatenate (first_name || ' ' || last_name) AS full_name.

{correction_prompt}

User Question: {user_query}

Return a valid JSON object matching this schema:
{{
  "sql": "SELECT ...",
  "analysis": "A concise 1-2 sentence business explanation of the data and what this query retrieves."
}}
"""

    # Try configured model, fallback to others if not found
    last_error = None
    models_to_try = [settings.gemini_model] + [
        m for m in CANDIDATE_MODELS if m != settings.gemini_model
    ]

    for model_name in models_to_try:
        try:
            model = _get_configured_model(model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            data = _extract_json(response.text)
            if "sql" not in data or not data["sql"].strip():
                raise ValueError("Gemini response missing 'sql' field.")
            if "analysis" not in data:
                data["analysis"] = f"Query generated for: {user_query}"
            return data
        except Exception as exc:
            last_error = exc
            logger.warning("Model %s failed: %s. Trying next candidate...", model_name, exc)

    # If all API calls fail, fallback to rule-based template generation
    logger.error("All Gemini API models failed. Falling back to rule-based SQL generator. Error: %s", last_error)
    return _rule_based_fallback(user_query)


def _rule_based_fallback(query: str) -> Dict[str, Any]:
    """Graceful offline fallback for common financial queries."""
    q = query.lower()

    if "credit score" in q or "below 600" in q or "credit" in q:
        sql = (
            "SELECT c.customer_id, c.customer_code, (c.first_name || ' ' || c.last_name) AS full_name, "
            "cr.credit_score, ls.status_name AS loan_status, rt.tier_name AS risk_tier "
            "FROM customers c "
            "LEFT JOIN loan_accounts la ON la.customer_id = c.customer_id "
            "LEFT JOIN loan_statuses ls ON la.loan_status_id = ls.loan_status_id "
            "LEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id "
            "LEFT JOIN risk_tiers rt ON cr.risk_tier_id = rt.risk_tier_id "
            "WHERE cr.credit_score < 600 "
            "ORDER BY cr.credit_score ASC LIMIT 50;"
        )
        analysis = "Retrieved customers with credit score below 600 along with their loan status and risk tier."
    elif "defaulter" in q or "default" in q:
        sql = (
            "SELECT c.customer_code, (c.first_name || ' ' || c.last_name) AS full_name, "
            "la.loan_number, la.outstanding_amount, la.interest_rate, la.default_date "
            "FROM loan_accounts la "
            "JOIN customers c ON la.customer_id = c.customer_id "
            "WHERE la.loan_status_id = 3 "
            "ORDER BY la.outstanding_amount DESC LIMIT 10;"
        )
        analysis = "Top defaulted loans ranked by total outstanding balance."
    elif "loan" in q and ("type" in q or "total" in q or "count" in q or "distribution" in q):
        sql = (
            "SELECT lt.loan_type_name, COUNT(la.loan_id) AS total_loans, "
            "SUM(la.principal_amount) AS total_principal, SUM(la.outstanding_amount) AS total_outstanding "
            "FROM loan_types lt "
            "LEFT JOIN loan_accounts la ON lt.loan_type_id = la.loan_type_id "
            "GROUP BY lt.loan_type_id, lt.loan_type_name "
            "ORDER BY total_outstanding DESC;"
        )
        analysis = "Loan portfolio breakdown categorized by loan product type."
    elif "recent" in q or "transaction" in q:
        sql = (
            "SELECT t.transaction_code, (c.first_name || ' ' || c.last_name) AS customer_name, "
            "tt.type_name AS transaction_type, t.amount, t.currency, t.transaction_date "
            "FROM transactions t "
            "JOIN accounts a ON t.account_id = a.account_id "
            "JOIN customers c ON a.customer_id = c.customer_id "
            "JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id "
            "ORDER BY t.transaction_date DESC LIMIT 20;"
        )
        analysis = "Recent financial transactions across all customer accounts."
    else:
        sql = (
            "SELECT c.customer_id, c.customer_code, (c.first_name || ' ' || c.last_name) AS full_name, "
            "c.email, cs.status_name AS status, c.customer_since "
            "FROM customers c "
            "JOIN customer_status cs ON c.customer_status_id = cs.status_id "
            "ORDER BY c.customer_id ASC LIMIT 25;"
        )
        analysis = f"Retrieved customer records matching: '{query}'."

    return {"sql": sql, "analysis": analysis}
