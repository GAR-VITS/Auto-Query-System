import pytest
from app.db.session import get_db_connection
from app.core.executor import SqlExecutor

def test_seeded_row_counts():
    with get_db_connection("nexus_reader") as conn:
        cursor = conn.cursor() if hasattr(conn, "cursor") else conn
        
        # Check customer count
        res = cursor.execute("SELECT count(*) FROM customers").fetchone()
        count = res[0]
        assert count == 2000, f"Expected 2000 customers, got {count}"

        # Check accounts count
        res = cursor.execute("SELECT count(*) FROM accounts").fetchone()
        count = res[0]
        assert count == 3000, f"Expected 3000 accounts, got {count}"

        # Check loans count
        res = cursor.execute("SELECT count(*) FROM loans").fetchone()
        count = res[0]
        assert count == 1500, f"Expected 1500 loans, got {count}"

        # Check delinquent repayments (~8% delinquent loans)
        res = cursor.execute("SELECT count(DISTINCT loan_id) FROM repayments WHERE days_past_due >= 30").fetchone()
        delinquent_loans = res[0]
        assert delinquent_loans > 50, f"Expected delinquent loans, got {delinquent_loans}"

def test_reader_role_cannot_write():
    executor = SqlExecutor(role="nexus_reader")
    # An attempt to run UPDATE or INSERT via read-only executor must fail
    with pytest.raises(Exception):
        executor.run_sync("UPDATE accounts SET balance = balance + 100 WHERE account_id = 1")

    with pytest.raises(Exception):
        executor.run_sync("INSERT INTO accounts (customer_id, type_id, branch_id, balance) VALUES (1, 1, 1, 500)")
