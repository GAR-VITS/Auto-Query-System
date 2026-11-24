"""
Unit Tests for Visualization Rules (Section 10 Specification)
One test per row of the Section 10 table:
1. One category column, one numeric column, 12 or fewer categories -> bar
2. More than 12 categories -> bar of top 10 plus an "Other" bar
3. Date or month column plus numeric -> line
4. Parts of a whole, 6 or fewer positive categories -> doughnut
5. Single row, single value -> kpi (large number, no chart)
6. Anything else -> none, table only
"""

import pytest
from app.agents.contracts import QueryResult
from app.agents.viz_agent import VisualizationAgent

@pytest.fixture
def viz():
    return VisualizationAgent()

def test_row1_bar_chart_under_12_cats(viz):
    # One category column, one numeric column, 12 or fewer categories -> bar
    res = QueryResult(
        sql="SELECT ...",
        columns=["branch_name", "delinquent_loans"],
        rows=[["Mumbai", 12], ["Delhi", 9], ["Bengaluru", 5]],
        row_count=3
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "bar"
    assert len(spec.labels) == 3

def test_row2_bar_chart_over_12_cats_with_other(viz):
    # More than 12 categories -> bar of top 10 plus an "Other" bar
    rows = [[f"City_{i}", 100 - i] for i in range(16)]
    res = QueryResult(
        sql="SELECT ...",
        columns=["city", "txn_volume"],
        rows=rows,
        row_count=16
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "bar"
    assert len(spec.labels) == 11  # top 10 + "Other"
    assert spec.labels[-1] == "Other"

def test_row3_line_chart_date_and_numeric(viz):
    # Date or month column plus numeric -> line
    rows = [["2026-01", 150000], ["2026-02", 180000], ["2026-03", 210000]]
    res = QueryResult(
        sql="SELECT ...",
        columns=["repayment_month", "amount_paid"],
        rows=rows,
        row_count=3
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "line"
    assert spec.labels == ["2026-01", "2026-02", "2026-03"]

def test_row4_doughnut_parts_of_whole(viz):
    # Parts of a whole, 6 or fewer positive categories -> doughnut
    rows = [["Tier A", 450], ["Tier B", 320], ["Tier C", 180], ["Tier D", 90], ["Tier E", 40]]
    res = QueryResult(
        sql="SELECT ...",
        columns=["tier_name", "customer_count"],
        rows=rows,
        row_count=5
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "doughnut"
    assert len(spec.labels) == 5

def test_row5_kpi_single_row_single_val(viz):
    # Single row, single value -> kpi (large number, no chart)
    res = QueryResult(
        sql="SELECT COUNT(*) FROM bank.customers",
        columns=["total_customers"],
        rows=[[2000]],
        row_count=1
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "kpi"
    assert spec.kpi_value == 2000

def test_row6_anything_else_table_only(viz):
    # Multiple text columns, complex shape -> none
    rows = [["Vihaan", "Mumbai", "SAVINGS", "ACTIVE"], ["Suresh", "Delhi", "CURRENT", "HOLD"]]
    res = QueryResult(
        sql="SELECT ...",
        columns=["name", "city", "acc_type", "status"],
        rows=rows,
        row_count=2
    )
    spec = viz.generate_viz(res)
    assert spec.chart_type == "none"
