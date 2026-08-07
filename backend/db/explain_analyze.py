from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_finance",
)

SAMPLE_QUERIES = [
    (
        "Low-credit customers with active loans",
        "SELECT c.customer_id, c.first_name, c.last_name, cr.credit_score, la.outstanding_amount FROM customers c JOIN credit_reports cr ON cr.customer_id = c.customer_id JOIN loan_accounts la ON la.customer_id = c.customer_id WHERE cr.credit_score < 600 AND la.loan_status_id = (SELECT loan_status_id FROM loan_statuses WHERE status_name = 'Active') ORDER BY cr.credit_score ASC LIMIT 50;",
    ),
    (
        "High-value defaulted loans",
        "SELECT loan_id, loan_number, customer_id, outstanding_amount FROM loan_accounts WHERE loan_status_id = (SELECT loan_status_id FROM loan_statuses WHERE status_name = 'Defaulted') ORDER BY outstanding_amount DESC LIMIT 20;",
    ),
    (
        "Recent large transactions",
        "SELECT transaction_id, account_id, amount, transaction_date FROM transactions WHERE transaction_date >= CURRENT_DATE - INTERVAL '90 days' AND amount > 500000 ORDER BY amount DESC LIMIT 50;",
    ),
]


def explain_query(conn, query: str) -> None:
    with conn.cursor() as cur:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) " + query)
        plan = cur.fetchall()
        print("QUERY:")
        print(query)
        print("PLAN:")
        for row in plan:
            print(row[0])
        print("\n" + "=" * 80 + "\n")


def main() -> None:
    print(f"Connecting to database: {DATABASE_URL}")
    with connect(DATABASE_URL) as conn:
        for label, query in SAMPLE_QUERIES:
            print(f"== {label} ==")
            explain_query(conn, query)


if __name__ == "__main__":
    main()
