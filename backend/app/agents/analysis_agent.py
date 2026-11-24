"""
NexusDB Analysis Agent
Computes deterministic statistics via Pandas over query result rows.
LLM only receives aggregate metrics to phrase the plain-English narrative (zero raw rows exposed).
"""

from typing import Any
import pandas as pd
import numpy as np

from app.agents.contracts import QueryResult, AnalysisResult
from app.llm.base import LLMClient


class AnalysisAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def analyze(self, question: str, query_res: QueryResult) -> AnalysisResult:
        if not query_res.rows or not query_res.columns:
            return AnalysisResult(
                stats={"row_count": 0, "columns": query_res.columns},
                insight_text="No matching records were found in the database for the given search criteria.",
                read_as="Executed search against target banking tables; 0 rows returned.",
                flags=["EMPTY_RESULT"]
            )

        # Convert rows into Pandas DataFrame
        df = pd.DataFrame(query_res.rows, columns=query_res.columns)
        stats: dict[str, Any] = {
            "row_count": len(df),
            "columns": list(df.columns),
            "numeric_summaries": {},
            "top_categories": {},
            "outliers": {},
        }

        # Identify numeric columns and compute descriptive statistics
        for col in df.columns:
            # Check if column is numeric or can be coerced
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if numeric_series.notnull().sum() > len(df) * 0.5:
                # Valid numeric column
                valid = numeric_series.dropna()
                if len(valid) > 0:
                    q25 = float(valid.quantile(0.25))
                    q75 = float(valid.quantile(0.75))
                    iqr = q75 - q25
                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outlier_count = int(((valid < lower_bound) | (valid > upper_bound)).sum())

                    stats["numeric_summaries"][col] = {
                        "min": round(float(valid.min()), 2),
                        "max": round(float(valid.max()), 2),
                        "mean": round(float(valid.mean()), 2),
                        "median": round(float(valid.median()), 2),
                        "sum": round(float(valid.sum()), 2),
                    }
                    if outlier_count > 0:
                        stats["outliers"][col] = {
                            "count": outlier_count,
                            "lower_bound": round(lower_bound, 2),
                            "upper_bound": round(upper_bound, 2),
                        }
            else:
                # Categorical column: find top 5 groups
                val_counts = df[col].astype(str).value_counts().head(5).to_dict()
                stats["top_categories"][col] = val_counts

        # Call LLM narrative method with aggregates only (never raw customer rows!)
        narrative = await self.llm.narrate(question, stats)

        return AnalysisResult(
            stats=stats,
            insight_text=narrative.insight_text,
            read_as=narrative.read_as or query_res.interpretation or "Analyzed database query output.",
            flags=narrative.flags,
        )
