"""
Index Performance Tests - Test Series 4
Tests to verify index creation, performance impact, and query optimization.
"""
from __future__ import annotations

import sqlite3
import time
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

def get_index_names(conn) -> dict:
    """Get all indexes from database"""
    cur = conn.cursor()
    cur.execute("""
        SELECT name, tbl_name FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%'
    """)
    indexes = {}
    for name, tbl_name in cur.fetchall():
        if tbl_name not in indexes:
            indexes[tbl_name] = []
        indexes[tbl_name].append(name)
    return indexes

def measure_query_time(conn, query: str, iterations: int = 1) -> float:
    """Measure query execution time"""
    cur = conn.cursor()
    start = time.time()
    
    for _ in range(iterations):
        cur.execute(query)
        cur.fetchall()
    
    end = time.time()
    return end - start

# ==================== TEST SERIES 4: INDEX PERFORMANCE ====================

def test_1_indexes_exist(conn):
    """Test 1: Verify indexes are created"""
    try:
        indexes = get_index_names(conn)
        
        if indexes:
            index_count = sum(len(v) for v in indexes.values())
            tables_with_indexes = len(indexes)
            log_test(1, "Indexes Exist", "PASSED",
                    f"Found {index_count} indexes on {tables_with_indexes} tables")
            return True
        else:
            log_test(1, "Indexes Exist", "FAILED", "No indexes found in database")
            return False
    except Exception as e:
        log_test(1, "Indexes Exist", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_customer_status_index(conn):
    """Test 2: Verify index on customer_status_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'customers' in indexes:
            has_status_index = any('status' in idx.lower() for idx in indexes['customers'])
            if has_status_index:
                log_test(2, "Customer Status Index", "PASSED",
                        "Index on customer_status_id exists")
                return True
        
        log_test(2, "Customer Status Index", "FAILED", 
                "No index on customer_status_id")
        return False
    except Exception as e:
        log_test(2, "Customer Status Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_account_customer_index(conn):
    """Test 3: Verify index on accounts.customer_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'accounts' in indexes:
            has_customer_index = any('customer' in idx.lower() for idx in indexes['accounts'])
            if has_customer_index:
                log_test(3, "Account Customer Index", "PASSED",
                        "Index on accounts.customer_id exists")
                return True
        
        log_test(3, "Account Customer Index", "FAILED",
                "No index on accounts.customer_id")
        return False
    except Exception as e:
        log_test(3, "Account Customer Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_account_status_index(conn):
    """Test 4: Verify index on account_status_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'accounts' in indexes:
            has_status_index = any('status' in idx.lower() for idx in indexes['accounts'])
            if has_status_index:
                log_test(4, "Account Status Index", "PASSED",
                        "Index on account_status_id exists")
                return True
        
        log_test(4, "Account Status Index", "FAILED",
                "No index on account_status_id")
        return False
    except Exception as e:
        log_test(4, "Account Status Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_loan_customer_index(conn):
    """Test 5: Verify index on loan_accounts.customer_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'loan_accounts' in indexes:
            has_customer_index = any('customer' in idx.lower() for idx in indexes['loan_accounts'])
            if has_customer_index:
                log_test(5, "Loan Customer Index", "PASSED",
                        "Index on loan_accounts.customer_id exists")
                return True
        
        log_test(5, "Loan Customer Index", "FAILED",
                "No index on loan_accounts.customer_id")
        return False
    except Exception as e:
        log_test(5, "Loan Customer Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_loan_status_index(conn):
    """Test 6: Verify index on loan_status_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'loan_accounts' in indexes:
            has_status_index = any('status' in idx.lower() for idx in indexes['loan_accounts'])
            if has_status_index:
                log_test(6, "Loan Status Index", "PASSED",
                        "Index on loan_status_id exists")
                return True
        
        log_test(6, "Loan Status Index", "FAILED",
                "No index on loan_status_id")
        return False
    except Exception as e:
        log_test(6, "Loan Status Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_transaction_account_index(conn):
    """Test 7: Verify index on transactions.account_id"""
    try:
        indexes = get_index_names(conn)
        
        if 'transactions' in indexes:
            has_account_index = any('account' in idx.lower() for idx in indexes['transactions'])
            if has_account_index:
                log_test(7, "Transaction Account Index", "PASSED",
                        "Index on transactions.account_id exists")
                return True
        
        log_test(7, "Transaction Account Index", "FAILED",
                "No index on transactions.account_id")
        return False
    except Exception as e:
        log_test(7, "Transaction Account Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_transaction_date_index(conn):
    """Test 8: Verify index on transactions date"""
    try:
        indexes = get_index_names(conn)
        
        if 'transactions' in indexes:
            has_date_index = any('date' in idx.lower() for idx in indexes['transactions'])
            if has_date_index:
                log_test(8, "Transaction Date Index", "PASSED",
                        "Index on transaction_date exists")
                return True
        
        log_test(8, "Transaction Date Index", "FAILED",
                "No index on transaction_date")
        return False
    except Exception as e:
        log_test(8, "Transaction Date Index", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_credit_report_indexes(conn):
    """Test 9: Verify indexes on credit_reports"""
    try:
        indexes = get_index_names(conn)
        
        if 'credit_reports' in indexes:
            has_indexes = len(indexes['credit_reports']) >= 2
            if has_indexes:
                log_test(9, "Credit Report Indexes", "PASSED",
                        f"Found {len(indexes['credit_reports'])} indexes on credit_reports")
                return True
        
        log_test(9, "Credit Report Indexes", "FAILED",
                "Insufficient indexes on credit_reports")
        return False
    except Exception as e:
        log_test(9, "Credit Report Indexes", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_audit_log_indexes(conn):
    """Test 10: Verify indexes on audit_logs"""
    try:
        indexes = get_index_names(conn)
        
        if 'audit_logs' in indexes:
            log_test(10, "Audit Log Indexes", "PASSED",
                    f"Found {len(indexes['audit_logs'])} indexes on audit_logs")
            return True
        
        log_test(10, "Audit Log Indexes", "FAILED",
                "No indexes on audit_logs")
        return False
    except Exception as e:
        log_test(10, "Audit Log Indexes", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_query_performance_indexed(conn):
    """Test 11: Measure query performance on indexed columns"""
    try:
        # Query on indexed column (customer_id in accounts table)
        query = "SELECT * FROM accounts WHERE customer_id = 1 LIMIT 100"
        
        exec_time = measure_query_time(conn, query, iterations=10)
        
        if exec_time < 1.0:  # Should be fast with index
            log_test(11, "Query Performance - Indexed Columns", "PASSED",
                    f"Query on indexed column executed in {exec_time:.4f}s (10 iterations)")
            return True
        else:
            log_test(11, "Query Performance - Indexed Columns", "FAILED",
                    f"Query took {exec_time:.4f}s (potentially slow)")
            return False
    except Exception as e:
        log_test(11, "Query Performance - Indexed Columns", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_index_on_filtered_queries(conn):
    """Test 12: Verify indexes help with WHERE clauses"""
    try:
        # Complex query using indexed columns
        query = """
            SELECT a.account_number, c.first_name, c.last_name 
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.account_status_id = 1
            LIMIT 50
        """
        
        exec_time = measure_query_time(conn, query, iterations=5)
        
        if exec_time < 1.0:
            log_test(12, "Indexes on Filtered Queries", "PASSED",
                    f"Filtered JOIN query executed in {exec_time:.4f}s (5 iterations)")
            return True
        else:
            log_test(12, "Indexes on Filtered Queries", "FAILED",
                    f"Query took {exec_time:.4f}s (potentially slow)")
            return False
    except Exception as e:
        log_test(12, "Indexes on Filtered Queries", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("INDEX PERFORMANCE TEST SERIES - Series 4")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_indexes_exist(conn)
        test_2_customer_status_index(conn)
        test_3_account_customer_index(conn)
        test_4_account_status_index(conn)
        test_5_loan_customer_index(conn)
        test_6_loan_status_index(conn)
        test_7_transaction_account_index(conn)
        test_8_transaction_date_index(conn)
        test_9_credit_report_indexes(conn)
        test_10_audit_log_indexes(conn)
        test_11_query_performance_indexed(conn)
        test_12_index_on_filtered_queries(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - INDEX PERFORMANCE")
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
