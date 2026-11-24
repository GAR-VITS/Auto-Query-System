"""
NexusDB Visualization Agent
Rules-based chart generation conforming exactly to the Section 10 specification table.
Produces theme-neutral VizSpec models for Chart.js rendering on the client.
"""

import re
from typing import Any
import pandas as pd
from app.agents.contracts import QueryResult, VizSpec, DatasetSpec


class VisualizationAgent:
    def generate_viz(self, query_res: QueryResult) -> VizSpec:
        if not query_res.rows or not query_res.columns:
            return VizSpec(chart_type="none", reason="Empty result set.")

        rows = query_res.rows
        columns = query_res.columns
        row_count = len(rows)

        # Rule 5: Single row, single value -> kpi
        if row_count == 1 and len(columns) == 1:
            val = rows[0][0]
            col_name = columns[0]
            return VizSpec(
                chart_type="kpi",
                kpi_value=val,
                kpi_label=col_name.replace("_", " ").title(),
                reason="Single row, single value matches KPI card rule."
            )

        df = pd.DataFrame(rows, columns=columns)

        # Classify columns into date, numeric, category
        date_cols = []
        numeric_cols = []
        category_cols = []

        for col in df.columns:
            col_lower = col.lower()
            # Date detection
            if any(k in col_lower for k in ("date", "month", "year", "quarter", "day", "ts", "time", "period")):
                date_cols.append(col)
                continue

            num_series = pd.to_numeric(df[col], errors='coerce')
            if num_series.notnull().sum() > len(df) * 0.7:
                numeric_cols.append(col)
            else:
                category_cols.append(col)

        # Rule 3: Date or month column plus numeric -> line
        if date_cols and numeric_cols:
            d_col = date_cols[0]
            n_col = numeric_cols[0]
            # Sort chronologically if possible
            df_sorted = df.copy()
            try:
                df_sorted = df_sorted.sort_values(by=d_col)
            except Exception:
                pass

            labels = df_sorted[d_col].astype(str).tolist()
            data = pd.to_numeric(df_sorted[n_col], errors='coerce').fillna(0).tolist()

            return VizSpec(
                chart_type="line",
                labels=labels,
                datasets=[DatasetSpec(label=n_col.replace("_", " ").title(), data=data)],
                reason="Date or month column plus numeric series matches line chart rule."
            )

        # Rule 4: Parts of a whole, 6 or fewer positive categories -> doughnut
        if len(category_cols) == 1 and len(numeric_cols) == 1:
            c_col = category_cols[0]
            n_col = numeric_cols[0]
            num_cats = len(df[c_col].unique())

            # Check if values are all positive and question or column implies distribution / tier / status / share
            is_distribution = any(k in n_col.lower() or k in c_col.lower() for k in ("share", "pct", "percent", "count", "tier", "status", "ratio", "portion"))
            if num_cats <= 6 and is_distribution:
                labels = df[c_col].astype(str).tolist()
                data = pd.to_numeric(df[n_col], errors='coerce').fillna(0).tolist()
                return VizSpec(
                    chart_type="doughnut",
                    labels=labels,
                    datasets=[DatasetSpec(label=n_col.replace("_", " ").title(), data=data)],
                    reason="Categorical composition with <= 6 positive categories matches doughnut chart rule."
                )

            # Rule 1: One category column, one numeric column, 12 or fewer categories -> bar
            if num_cats <= 12:
                labels = df[c_col].astype(str).tolist()
                data = pd.to_numeric(df[n_col], errors='coerce').fillna(0).tolist()
                return VizSpec(
                    chart_type="bar",
                    labels=labels,
                    datasets=[DatasetSpec(label=n_col.replace("_", " ").title(), data=data)],
                    reason="One category and one numeric column with <= 12 categories matches bar chart rule."
                )

            # Rule 2: More than 12 categories -> bar of top 10 plus an "Other" bar
            top_10 = df.head(10)
            other_rows = df.iloc[10:]
            labels = top_10[c_col].astype(str).tolist() + ["Other"]
            data = pd.to_numeric(top_10[n_col], errors='coerce').fillna(0).tolist()
            other_sum = float(pd.to_numeric(other_rows[n_col], errors='coerce').fillna(0).sum())
            data.append(round(other_sum, 2))

            return VizSpec(
                chart_type="bar",
                labels=labels,
                datasets=[DatasetSpec(label=n_col.replace("_", " ").title(), data=data)],
                reason="More than 12 categories: top 10 categories plus aggregated 'Other' bar matches bar chart rule."
            )

        # Rule 6: Anything else -> none (table only)
        return VizSpec(
            chart_type="none",
            reason="Tabular result shape does not suit standard aggregate chart."
        )
