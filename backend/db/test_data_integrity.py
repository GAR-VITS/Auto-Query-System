"""
Data Integrity Tests - Test Series 9
Tests to verify data integrity across related tables and identify orphaned records.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime

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

# ==================== TEST SERIES 9: DATA INTEGRITY TESTS ====================

def test_1_no_orphaned_customers(conn):
    """Test 1: No orphaned customers (all have valid status_id)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM customers 
            WHERE customer_status_id NOT IN (SELECT status_id FROM customer_status)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(1, "No Orphaned Customers", "PASSED",
                    "All customers reference valid statuses")
            return True
        else:
            log_test(1, "No Orphaned Customers", "FAILED",
                    f"Found {orphaned} customers with invalid status_id")
            return False
    except Exception as e:
        log_test(1, "No Orphaned Customers", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_no_orphaned_accounts(conn):
    """Test 2: No orphaned accounts (all reference valid customers)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM accounts 
            WHERE customer_id NOT IN (SELECT customer_id FROM customers)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(2, "No Orphaned Accounts", "PASSED",
                    "All accounts reference valid customers")
            return True
        else:
            log_test(2, "No Orphaned Accounts", "FAILED",
                    f"Found {orphaned} accounts with invalid customer_id")
            return False
    except Exception as e:
        log_test(2, "No Orphaned Accounts", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_no_orphaned_loans(conn):
    """Test 3: No orphaned loans (all reference valid customers)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_accounts 
            WHERE customer_id NOT IN (SELECT customer_id FROM customers)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(3, "No Orphaned Loans", "PASSED",
                    "All loans reference valid customers")
            return True
        else:
            log_test(3, "No Orphaned Loans", "FAILED",
                    f"Found {orphaned} loans with invalid customer_id")
            return False
    except Exception as e:
        log_test(3, "No Orphaned Loans", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_no_orphaned_transactions(conn):
    """Test 4: No orphaned transactions (all reference valid accounts/loans)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE account_id NOT IN (SELECT account_id FROM accounts)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(4, "No Orphaned Transactions", "PASSED",
                    "All transactions reference valid accounts")
            return True
        else:
            log_test(4, "No Orphaned Transactions", "FAILED",
                    f"Found {orphaned} transactions with invalid account_id")
            return False
    except Exception as e:
        log_test(4, "No Orphaned Transactions", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_no_orphaned_payment_schedules(conn):
    """Test 5: No orphaned payment schedules (all reference valid loans)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_payment_schedule 
            WHERE loan_id NOT IN (SELECT loan_id FROM loan_accounts)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(5, "No Orphaned Payment Schedules", "PASSED",
                    "All payment schedules reference valid loans")
            return True
        else:
            log_test(5, "No Orphaned Payment Schedules", "FAILED",
                    f"Found {orphaned} orphaned payment schedules")
            return False
    except Exception as e:
        log_test(5, "No Orphaned Payment Schedules", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_no_orphaned_credit_reports(conn):
    """Test 6: No orphaned credit reports (all reference valid customers)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM credit_reports 
            WHERE customer_id NOT IN (SELECT customer_id FROM customers)
        """)
        orphaned = cur.fetchone()[0]
        
        if orphaned == 0:
            log_test(6, "No Orphaned Credit Reports", "PASSED",
                    "All credit reports reference valid customers")
            return True
        else:
            log_test(6, "No Orphaned Credit Reports", "FAILED",
                    f"Found {orphaned} orphaned credit reports")
            return False
    except Exception as e:
        log_test(6, "No Orphaned Credit Reports", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_account_type_integrity(conn):
    """Test 7: All accounts have valid type_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM accounts 
            WHERE account_type_id NOT IN (SELECT account_type_id FROM account_types)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(7, "Account Type Integrity", "PASSED",
                    "All accounts reference valid types")
            return True
        else:
            log_test(7, "Account Type Integrity", "FAILED",
                    f"Found {invalid} accounts with invalid type_id")
            return False
    except Exception as e:
        log_test(7, "Account Type Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_account_status_integrity(conn):
    """Test 8: All accounts have valid status_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM accounts 
            WHERE account_status_id NOT IN (SELECT account_status_id FROM account_statuses)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(8, "Account Status Integrity", "PASSED",
                    "All accounts reference valid statuses")
            return True
        else:
            log_test(8, "Account Status Integrity", "FAILED",
                    f"Found {invalid} accounts with invalid status_id")
            return False
    except Exception as e:
        log_test(8, "Account Status Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_loan_type_integrity(conn):
    """Test 9: All loans have valid type_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_accounts 
            WHERE loan_type_id NOT IN (SELECT loan_type_id FROM loan_types)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(9, "Loan Type Integrity", "PASSED",
                    "All loans reference valid types")
            return True
        else:
            log_test(9, "Loan Type Integrity", "FAILED",
                    f"Found {invalid} loans with invalid type_id")
            return False
    except Exception as e:
        log_test(9, "Loan Type Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_loan_status_integrity(conn):
    """Test 10: All loans have valid status_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_accounts 
            WHERE loan_status_id NOT IN (SELECT loan_status_id FROM loan_statuses)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(10, "Loan Status Integrity", "PASSED",
                    "All loans reference valid statuses")
            return True
        else:
            log_test(10, "Loan Status Integrity", "FAILED",
                    f"Found {invalid} loans with invalid status_id")
            return False
    except Exception as e:
        log_test(10, "Loan Status Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_transaction_type_integrity(conn):
    """Test 11: All transactions have valid type_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE transaction_type_id NOT IN (SELECT transaction_type_id FROM transaction_types)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(11, "Transaction Type Integrity", "PASSED",
                    "All transactions reference valid types")
            return True
        else:
            log_test(11, "Transaction Type Integrity", "FAILED",
                    f"Found {invalid} transactions with invalid type_id")
            return False
    except Exception as e:
        log_test(11, "Transaction Type Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_payment_status_integrity(conn):
    """Test 12: All payment schedules have valid status_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM loan_payment_schedule 
            WHERE payment_status_id NOT IN (SELECT payment_status_id FROM payment_statuses)
        """)
        invalid = cur.fetchone()[0]
        
        if invalid == 0:
            log_test(12, "Payment Status Integrity", "PASSED",
                    "All payment schedules reference valid statuses")
            return True
        else:
            log_test(12, "Payment Status Integrity", "FAILED",
                    f"Found {invalid} schedules with invalid status_id")
            return False
    except Exception as e:
        log_test(12, "Payment Status Integrity", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("DATA INTEGRITY TEST SERIES - Series 9")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_no_orphaned_customers(conn)
        test_2_no_orphaned_accounts(conn)
        test_3_no_orphaned_loans(conn)
        test_4_no_orphaned_transactions(conn)
        test_5_no_orphaned_payment_schedules(conn)
        test_6_no_orphaned_credit_reports(conn)
        test_7_account_type_integrity(conn)
        test_8_account_status_integrity(conn)
        test_9_loan_type_integrity(conn)
        test_10_loan_status_integrity(conn)
        test_11_transaction_type_integrity(conn)
        test_12_payment_status_integrity(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - DATA INTEGRITY")
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
