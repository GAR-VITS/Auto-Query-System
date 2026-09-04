"""
Query Tests - Test Series 8
Tests to verify complex queries work correctly with joins, aggregations, and filtering.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "enterprise_finance.db"

# Test results storage
test_results = []

def log_test(test_num: int, test_name: str, status: str, details: str = ""):
    """Log test result"""
    result = {
        "Test #": test_num,
        "Test Name": test_name,
        "Status": status,
        "Details": details,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    test_results.append(result)
    status_symbol = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏳"
    print(f"{status_symbol} Test {test_num}: {test_name} - {status}")
    if details:
        print(f"   └─ {details}")

def connect_to_db():
    """Connect to SQLite database"""
    if not DB_PATH.exists():
        return None, "Database file does not exist"
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn, "Connected"
    except Exception as e:
        return None, str(e)

# ==================== TEST SERIES 8: QUERY TESTS ====================

def test_1_simple_customer_query(conn):
    """Test 1: Simple customer query works"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT customer_id, first_name, last_name FROM customers LIMIT 10")
        results = cur.fetchall()
        
        if len(results) > 0:
            log_test(1, "Simple Customer Query", "PASSED",
                    f"Retrieved {len(results)} customer records")
            return True
        else:
            log_test(1, "Simple Customer Query", "FAILED",
                    "No customer records found")
            return False
    except Exception as e:
        log_test(1, "Simple Customer Query", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_customer_account_join(conn):
    """Test 2: Customer to Account JOIN works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT c.customer_id, c.first_name, a.account_number, a.current_balance
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if len(results) > 0:
            log_test(2, "Customer-Account JOIN", "PASSED",
                    f"Retrieved {len(results)} customer-account records")
            return True
        else:
            log_test(2, "Customer-Account JOIN", "FAILED",
                    "No join results found")
            return False
    except Exception as e:
        log_test(2, "Customer-Account JOIN", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_customer_loan_join(conn):
    """Test 3: Customer to Loan JOIN works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT c.customer_id, c.first_name, l.loan_number, l.outstanding_amount
            FROM customers c
            LEFT JOIN loan_accounts l ON c.customer_id = l.customer_id
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if len(results) > 0:
            log_test(3, "Customer-Loan JOIN", "PASSED",
                    f"Retrieved {len(results)} customer-loan records")
            return True
        else:
            log_test(3, "Customer-Loan JOIN", "FAILED",
                    "No join results found")
            return False
    except Exception as e:
        log_test(3, "Customer-Loan JOIN", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_three_table_join(conn):
    """Test 4: Three-table JOIN (customer-account-transaction)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT c.first_name, a.account_number, t.amount, t.transaction_date
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            JOIN transactions t ON a.account_id = t.account_id
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if len(results) > 0:
            log_test(4, "Three-Table JOIN", "PASSED",
                    f"Retrieved {len(results)} three-table join records")
            return True
        else:
            log_test(4, "Three-Table JOIN", "FAILED",
                    "No three-table join results")
            return False
    except Exception as e:
        log_test(4, "Three-Table JOIN", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_aggregation_count(conn):
    """Test 5: COUNT aggregation works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) as total_customers FROM customers
        """)
        result = cur.fetchone()
        
        if result and result[0] > 0:
            log_test(5, "COUNT Aggregation", "PASSED",
                    f"COUNT aggregation returned {result[0]} customers")
            return True
        else:
            log_test(5, "COUNT Aggregation", "FAILED",
                    "COUNT aggregation returned 0 or NULL")
            return False
    except Exception as e:
        log_test(5, "COUNT Aggregation", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_aggregation_sum(conn):
    """Test 6: SUM aggregation works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT SUM(current_balance) as total_balance FROM accounts
        """)
        result = cur.fetchone()
        
        if result:
            log_test(6, "SUM Aggregation", "PASSED",
                    f"SUM aggregation returned total balance: {result[0]}")
            return True
        else:
            log_test(6, "SUM Aggregation", "FAILED",
                    "SUM aggregation returned no result")
            return False
    except Exception as e:
        log_test(6, "SUM Aggregation", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_aggregation_avg(conn):
    """Test 7: AVG aggregation works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT AVG(interest_rate) as avg_rate FROM loan_accounts
        """)
        result = cur.fetchone()
        
        if result and result[0] is not None:
            log_test(7, "AVG Aggregation", "PASSED",
                    f"AVG aggregation returned: {result[0]:.2f}")
            return True
        else:
            log_test(7, "AVG Aggregation", "FAILED",
                    "AVG aggregation returned no result")
            return False
    except Exception as e:
        log_test(7, "AVG Aggregation", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_group_by_query(conn):
    """Test 8: GROUP BY query works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT account_status_id, COUNT(*) as account_count
            FROM accounts
            GROUP BY account_status_id
        """)
        results = cur.fetchall()
        
        if len(results) > 0:
            log_test(8, "GROUP BY Query", "PASSED",
                    f"GROUP BY returned {len(results)} groups")
            return True
        else:
            log_test(8, "GROUP BY Query", "FAILED",
                    "GROUP BY returned no groups")
            return False
    except Exception as e:
        log_test(8, "GROUP BY Query", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_having_clause(conn):
    """Test 9: HAVING clause with aggregation"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT customer_id, COUNT(*) as account_count
            FROM accounts
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        """)
        results = cur.fetchall()
        
        if results is not None:
            log_test(9, "HAVING Clause", "PASSED",
                    f"HAVING clause found {len(results)} customers with 2+ accounts")
            return True
        else:
            log_test(9, "HAVING Clause", "FAILED",
                    "HAVING clause query failed")
            return False
    except Exception as e:
        log_test(9, "HAVING Clause", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_where_clause_filtering(conn):
    """Test 10: WHERE clause filtering works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM customers 
            WHERE customer_status_id = 1
        """)
        result = cur.fetchone()[0]
        
        if result >= 0:
            log_test(10, "WHERE Clause Filtering", "PASSED",
                    f"WHERE clause filtered to {result} active customers")
            return True
        else:
            log_test(10, "WHERE Clause Filtering", "FAILED",
                    "WHERE clause filtering failed")
            return False
    except Exception as e:
        log_test(10, "WHERE Clause Filtering", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_between_range_query(conn):
    """Test 11: BETWEEN range queries work"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM credit_reports
            WHERE credit_score BETWEEN 700 AND 800
        """)
        result = cur.fetchone()[0]
        
        if result >= 0:
            log_test(11, "BETWEEN Range Query", "PASSED",
                    f"Found {result} credit reports in 700-800 range")
            return True
        else:
            log_test(11, "BETWEEN Range Query", "FAILED",
                    "BETWEEN query failed")
            return False
    except Exception as e:
        log_test(11, "BETWEEN Range Query", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_subquery_in_clause(conn):
    """Test 12: Subquery with IN clause works"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_accounts
            WHERE customer_id IN (
                SELECT customer_id FROM customers 
                WHERE customer_status_id = 1
            )
        """)
        result = cur.fetchone()[0]
        
        if result >= 0:
            log_test(12, "Subquery IN Clause", "PASSED",
                    f"Subquery found {result} loans for active customers")
            return True
        else:
            log_test(12, "Subquery IN Clause", "FAILED",
                    "Subquery with IN failed")
            return False
    except Exception as e:
        log_test(12, "Subquery IN Clause", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("QUERY TEST SERIES - Series 8")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_simple_customer_query(conn)
        test_2_customer_account_join(conn)
        test_3_customer_loan_join(conn)
        test_4_three_table_join(conn)
        test_5_aggregation_count(conn)
        test_6_aggregation_sum(conn)
        test_7_aggregation_avg(conn)
        test_8_group_by_query(conn)
        test_9_having_clause(conn)
        test_10_where_clause_filtering(conn)
        test_11_between_range_query(conn)
        test_12_subquery_in_clause(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - QUERY TESTS")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["Status"] == "PASSED")
    failed = sum(1 for r in test_results if r["Status"] == "FAILED")
    total = len(test_results)
    
    print(f"\n📊 Results: {passed}/{total} tests PASSED, {failed}/{total} FAILED\n")
    
    # Print detailed table
    print(f"{'Test #':<8} | {'Test Name':<45} | {'Status':<10} | Details")
    print("-" * 115)
    for r in test_results:
        details = (r['Details'][:55] + '...') if len(r['Details']) > 55 else r['Details']
        print(f"{r['Test #']:<8} | {r['Test Name']:<45} | {r['Status']:<10} | {details}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
