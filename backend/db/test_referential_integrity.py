"""
Referential Integrity Tests - Test Series 2
Tests to verify foreign key constraints, data validation, and integrity rules.
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

# ==================== TEST SERIES 2: REFERENTIAL INTEGRITY ====================

def test_1_foreign_key_enforcement(conn):
    """Test 1: Verify foreign key constraints are enforced"""
    cur = conn.cursor()
    
    try:
        # Try to insert a customer with invalid status_id (no such status exists with id=9999)
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, customer_status_id)
            VALUES ('TEST-INVALID-FK', 'Test', 'User', ?, 9999)
        """, (date.today(),))
        
        log_test(1, "Foreign Key Constraint Enforcement", "FAILED", 
                "Invalid foreign key was accepted (should have been rejected)")
        return False
    except sqlite3.IntegrityError as e:
        log_test(1, "Foreign Key Constraint Enforcement", "PASSED", 
                f"Foreign key constraint properly enforced: {str(e)[:50]}")
        return True
    except Exception as e:
        log_test(1, "Foreign Key Constraint Enforcement", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_2_customer_status_foreign_key(conn):
    """Test 2: Verify customer_status_id references are validated"""
    cur = conn.cursor()
    
    try:
        # Get a valid status ID first
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        valid_status = cur.fetchone()
        
        if not valid_status:
            log_test(2, "Valid Customer Status Reference", "FAILED", "No customer statuses exist")
            return False
        
        # Insert valid customer with valid status
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, customer_status_id)
            VALUES ('TEST-VALID-STATUS', 'Valid', 'Test', ?, ?)
        """, (date.today(), valid_status[0]))
        
        log_test(2, "Valid Customer Status Reference", "PASSED", 
                f"Successfully inserted customer with valid status_id={valid_status[0]}")
        return True
    except Exception as e:
        log_test(2, "Valid Customer Status Reference", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_account_customer_foreign_key(conn):
    """Test 3: Verify account_id references valid customer"""
    cur = conn.cursor()
    
    try:
        # Try to create account with invalid customer_id
        cur.execute("""
            INSERT INTO accounts 
            (account_number, customer_id, account_type_id, account_status_id, opened_date)
            VALUES ('ACC-INVALID-CUST', 99999, 1, 1, ?)
        """, (date.today(),))
        
        log_test(3, "Account Customer Foreign Key", "FAILED", 
                "Invalid customer_id was accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(3, "Account Customer Foreign Key", "PASSED", 
                "Foreign key constraint prevented orphaned account creation")
        return True
    except Exception as e:
        log_test(3, "Account Customer Foreign Key", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_4_loan_account_foreign_keys(conn):
    """Test 4: Verify loan_account foreign keys"""
    cur = conn.cursor()
    
    try:
        # Try to create loan with invalid customer_id and other invalid IDs
        cur.execute("""
            INSERT INTO loan_accounts 
            (loan_number, customer_id, loan_type_id, loan_status_id, 
             principal_amount, outstanding_amount, interest_rate, term_months, 
             payment_frequency, origination_date, maturity_date)
            VALUES ('LOAN-INVALID', 99999, 99999, 99999, 100000, 100000, 5.5, 12, 'Monthly', ?, ?)
        """, (date.today(), date.today() + timedelta(days=365)))
        
        log_test(4, "Loan Account Foreign Keys", "FAILED", 
                "Invalid foreign keys were accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(4, "Loan Account Foreign Keys", "PASSED", 
                "Foreign keys properly validated on loan creation")
        return True
    except Exception as e:
        log_test(4, "Loan Account Foreign Keys", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_5_transaction_foreign_keys(conn):
    """Test 5: Verify transaction references valid account and/or loan"""
    cur = conn.cursor()
    
    try:
        # Try to create transaction with invalid account_id
        cur.execute("""
            INSERT INTO transactions 
            (transaction_code, account_id, transaction_type_id, transaction_date, amount)
            VALUES ('TXN-INVALID-ACC', 99999, 1, ?, 500)
        """, (datetime.now(),))
        
        log_test(5, "Transaction Foreign Keys", "FAILED", 
                "Invalid account_id was accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(5, "Transaction Foreign Keys", "PASSED", 
                "Transaction foreign key constraints enforced")
        return True
    except Exception as e:
        log_test(5, "Transaction Foreign Keys", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_6_user_role_foreign_key(conn):
    """Test 6: Verify user role_id references valid role"""
    cur = conn.cursor()
    
    try:
        # Try to create user with invalid role_id
        cur.execute("""
            INSERT INTO users 
            (email, full_name, role_id)
            VALUES ('invalid@test.com', 'Invalid User', 99999)
        """)
        
        log_test(6, "User Role Foreign Key", "FAILED", 
                "Invalid role_id was accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(6, "User Role Foreign Key", "PASSED", 
                "User role_id foreign key constraint enforced")
        return True
    except Exception as e:
        log_test(6, "User Role Foreign Key", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_7_credit_report_foreign_keys(conn):
    """Test 7: Verify credit report references"""
    cur = conn.cursor()
    
    try:
        # Try to create credit report with invalid customer and risk tier
        cur.execute("""
            INSERT INTO credit_reports 
            (customer_id, bureau_name, credit_score, risk_tier_id, report_date)
            VALUES (99999, 'Invalid Bureau', 750, 99999, ?)
        """, (date.today(),))
        
        log_test(7, "Credit Report Foreign Keys", "FAILED", 
                "Invalid foreign keys accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(7, "Credit Report Foreign Keys", "PASSED", 
                "Credit report foreign keys enforced")
        return True
    except Exception as e:
        log_test(7, "Credit Report Foreign Keys", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_8_audit_log_foreign_keys(conn):
    """Test 8: Verify audit log references"""
    cur = conn.cursor()
    
    try:
        # Try to create audit log with invalid action and status types
        cur.execute("""
            INSERT INTO audit_logs 
            (action_type_id, audit_status_id, description, reasoning)
            VALUES (99999, 99999, 'Invalid Audit', 'Invalid Reason')
        """)
        
        log_test(8, "Audit Log Foreign Keys", "FAILED", 
                "Invalid foreign keys accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(8, "Audit Log Foreign Keys", "PASSED", 
                "Audit log foreign keys enforced")
        return True
    except Exception as e:
        log_test(8, "Audit Log Foreign Keys", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_9_loan_payment_schedule_foreign_key(conn):
    """Test 9: Verify loan payment schedule references valid loan"""
    cur = conn.cursor()
    
    try:
        # Try to create payment schedule with invalid loan_id
        cur.execute("""
            INSERT INTO loan_payment_schedule 
            (loan_id, payment_number, due_date, amount_due, principal_due, 
             interest_due, balance_remaining, payment_status_id)
            VALUES (99999, 1, ?, 1000, 800, 200, 9000, 1)
        """, (date.today(),))
        
        log_test(9, "Loan Payment Schedule Foreign Key", "FAILED", 
                "Invalid loan_id accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(9, "Loan Payment Schedule Foreign Key", "PASSED", 
                "Loan payment schedule foreign key enforced")
        return True
    except Exception as e:
        log_test(9, "Loan Payment Schedule Foreign Key", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_10_spider_table_foreign_keys(conn):
    """Test 10: Verify spider benchmark table foreign keys"""
    cur = conn.cursor()
    
    try:
        # Try to create spider_table with invalid spider_db_id
        cur.execute("""
            INSERT INTO spider_tables 
            (spider_db_id, table_name, description)
            VALUES (99999, 'invalid_table', 'Invalid Table')
        """)
        
        log_test(10, "Spider Table Foreign Key", "FAILED", 
                "Invalid spider_db_id accepted")
        return False
    except sqlite3.IntegrityError:
        log_test(10, "Spider Table Foreign Key", "PASSED", 
                "Spider table foreign key enforced")
        return True
    except Exception as e:
        log_test(10, "Spider Table Foreign Key", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_11_valid_inserts_work(conn):
    """Test 11: Verify valid inserts with correct foreign keys work"""
    cur = conn.cursor()
    
    try:
        # Get valid IDs
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        status_id = cur.fetchone()[0]
        
        # Insert valid customer
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, customer_status_id)
            VALUES ('TEST-VALID-FULL', 'John', 'Doe', ?, ?)
        """, (date.today(), status_id))
        
        cust_id = cur.lastrowid
        
        # Get valid account type and status
        cur.execute("SELECT account_type_id FROM account_types LIMIT 1")
        acc_type_id = cur.fetchone()[0]
        cur.execute("SELECT account_status_id FROM account_statuses LIMIT 1")
        acc_status_id = cur.fetchone()[0]
        
        # Insert valid account
        cur.execute("""
            INSERT INTO accounts 
            (account_number, customer_id, account_type_id, account_status_id, opened_date, current_balance)
            VALUES ('VALID-ACC-123', ?, ?, ?, ?, 5000)
        """, (cust_id, acc_type_id, acc_status_id, date.today()))
        
        acc_id = cur.lastrowid
        
        # Get valid transaction type
        cur.execute("SELECT transaction_type_id FROM transaction_types LIMIT 1")
        txn_type_id = cur.fetchone()[0]
        
        # Insert valid transaction
        cur.execute("""
            INSERT INTO transactions 
            (transaction_code, account_id, transaction_type_id, transaction_date, amount)
            VALUES ('VALID-TXN-123', ?, ?, ?, 500)
        """, (acc_id, txn_type_id, datetime.now()))
        
        log_test(11, "Valid Inserts with Correct FK", "PASSED", 
                "Successfully inserted customer→account→transaction chain")
        return True
    except Exception as e:
        log_test(11, "Valid Inserts with Correct FK", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_data_consistency_check(conn):
    """Test 12: Verify data consistency across related tables"""
    cur = conn.cursor()
    
    try:
        # Check that all customers have valid status_ids
        cur.execute("""
            SELECT COUNT(*) FROM customers c
            WHERE c.customer_status_id NOT IN 
            (SELECT status_id FROM customer_status)
        """)
        orphaned_customers = cur.fetchone()[0]
        
        # Check that all accounts have valid customers
        cur.execute("""
            SELECT COUNT(*) FROM accounts a
            WHERE a.customer_id NOT IN (SELECT customer_id FROM customers)
        """)
        orphaned_accounts = cur.fetchone()[0]
        
        # Check that all users have valid roles
        cur.execute("""
            SELECT COUNT(*) FROM users u
            WHERE u.role_id NOT IN (SELECT role_id FROM roles)
        """)
        orphaned_users = cur.fetchone()[0]
        
        total_orphaned = orphaned_customers + orphaned_accounts + orphaned_users
        
        if total_orphaned == 0:
            log_test(12, "Data Consistency Check", "PASSED", 
                    "All records have valid parent references")
            return True
        else:
            log_test(12, "Data Consistency Check", "FAILED", 
                    f"Found {total_orphaned} orphaned records")
            return False
    except Exception as e:
        log_test(12, "Data Consistency Check", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("REFERENTIAL INTEGRITY TEST SERIES - Series 2")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_foreign_key_enforcement(conn)
        conn.rollback()  # Rollback any changes
        
        test_2_customer_status_foreign_key(conn)
        conn.rollback()
        
        test_3_account_customer_foreign_key(conn)
        conn.rollback()
        
        test_4_loan_account_foreign_keys(conn)
        conn.rollback()
        
        test_5_transaction_foreign_keys(conn)
        conn.rollback()
        
        test_6_user_role_foreign_key(conn)
        conn.rollback()
        
        test_7_credit_report_foreign_keys(conn)
        conn.rollback()
        
        test_8_audit_log_foreign_keys(conn)
        conn.rollback()
        
        test_9_loan_payment_schedule_foreign_key(conn)
        conn.rollback()
        
        test_10_spider_table_foreign_keys(conn)
        conn.rollback()
        
        test_11_valid_inserts_work(conn)
        conn.rollback()
        
        test_12_data_consistency_check(conn)
        conn.rollback()
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - REFERENTIAL INTEGRITY")
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
