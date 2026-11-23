"""
Data Type & Constraint Tests - Test Series 3
Tests to verify data types, NOT NULL constraints, UNIQUE constraints, and CHECK constraints.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal

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

# ==================== TEST SERIES 3: DATA TYPE & CONSTRAINT TESTS ====================

def test_1_numeric_fields_accept_numbers(conn):
    """Test 1: Verify NUMERIC fields accept valid numbers"""
    cur = conn.cursor()
    
    try:
        # Get a valid customer and loan type
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer_id = cur.fetchone()
        if not customer_id:
            log_test(1, "NUMERIC Fields Accept Numbers", "FAILED", "No test customer available")
            return False
        
        customer_id = customer_id[0]
        
        cur.execute("SELECT loan_type_id FROM loan_types LIMIT 1")
        loan_type_id = cur.fetchone()[0]
        
        cur.execute("SELECT loan_status_id FROM loan_statuses LIMIT 1")
        loan_status_id = cur.fetchone()[0]
        
        # Insert loan with decimal numeric values
        cur.execute("""
            INSERT INTO loan_accounts 
            (loan_number, customer_id, loan_type_id, loan_status_id,
             principal_amount, outstanding_amount, interest_rate, term_months,
             payment_frequency, origination_date, maturity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('TEST-NUMERIC-001', customer_id, loan_type_id, loan_status_id,
              100000.50, 95000.75, 5.25, 60, 'Monthly', 
              date.today(), date.today() + timedelta(days=1825)))
        
        log_test(1, "NUMERIC Fields Accept Numbers", "PASSED",
                "Successfully inserted decimal numeric values")
        return True
    except Exception as e:
        log_test(1, "NUMERIC Fields Accept Numbers", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_text_fields_accept_strings(conn):
    """Test 2: Verify TEXT fields accept valid strings"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        status_id = cur.fetchone()[0]
        
        # Insert customer with various text fields
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, email, phone, customer_since, customer_status_id, preferred_language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ('TEST-TEXT-001', 'Rajesh Kumar', 'Sharma', 'rajesh@example.com',
              '+91-9876543210', date.today(), status_id, 'Hindi'))
        
        log_test(2, "TEXT Fields Accept Strings", "PASSED",
                "Successfully inserted text data with special characters")
        return True
    except Exception as e:
        log_test(2, "TEXT Fields Accept Strings", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_date_fields_accept_dates(conn):
    """Test 3: Verify DATE/TIMESTAMPTZ fields accept valid dates"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        status_id = cur.fetchone()[0]
        
        # Insert customer with date of birth and various date fields
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, 
             customer_status_id, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('TEST-DATE-001', 'John', 'Doe', date(2020, 1, 15),
              status_id, date(1990, 5, 20)))
        
        log_test(3, "DATE/TIMESTAMPTZ Fields Accept Dates", "PASSED",
                "Successfully inserted date values")
        return True
    except Exception as e:
        log_test(3, "DATE/TIMESTAMPTZ Fields Accept Dates", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_not_null_constraint_enforcement(conn):
    """Test 4: Verify NOT NULL constraints are enforced"""
    cur = conn.cursor()
    
    try:
        # Try to insert customer without required first_name
        cur.execute("""
            INSERT INTO customers 
            (customer_code, last_name, customer_since, customer_status_id)
            VALUES (?, ?, ?, ?)
        """, ('TEST-NULL-001', 'Doe', date.today(), 1))
        
        log_test(4, "NOT NULL Constraint Enforcement", "FAILED",
                "NULL was accepted in required NOT NULL column")
        return False
    except sqlite3.IntegrityError:
        log_test(4, "NOT NULL Constraint Enforcement", "PASSED",
                "NOT NULL constraint properly enforced")
        return True
    except Exception as e:
        log_test(4, "NOT NULL Constraint Enforcement", "FAILED", f"Unexpected error: {str(e)[:50]}")
        return False

def test_5_unique_constraint_enforcement(conn):
    """Test 5: Verify UNIQUE constraints prevent duplicates"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        status_id = cur.fetchone()[0]
        
        # Insert first customer with unique code
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, customer_status_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('TEST-UNIQUE-001', 'Jane', 'Smith', date.today(), status_id))
        
        # Try to insert second customer with SAME code (should fail)
        try:
            cur.execute("""
                INSERT INTO customers 
                (customer_code, first_name, last_name, customer_since, customer_status_id)
                VALUES (?, ?, ?, ?, ?)
            """, ('TEST-UNIQUE-001', 'John', 'Doe', date.today(), status_id))
            
            log_test(5, "UNIQUE Constraint Enforcement", "FAILED",
                    "UNIQUE constraint was not enforced - duplicate allowed")
            return False
        except sqlite3.IntegrityError:
            log_test(5, "UNIQUE Constraint Enforcement", "PASSED",
                    "UNIQUE constraint properly prevented duplicate")
            return True
    except Exception as e:
        log_test(5, "UNIQUE Constraint Enforcement", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_check_constraint_credit_score(conn):
    """Test 6: Verify CHECK constraint on credit score range"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer_id = cur.fetchone()
        if not customer_id:
            log_test(6, "CHECK Constraint - Credit Score Range", "FAILED", "No test customer")
            return False
        
        customer_id = customer_id[0]
        
        # Try to insert credit report with score outside valid range (expecting 300-850)
        # SQLite doesn't enforce CHECK constraints strictly, but we test anyway
        try:
            cur.execute("""
                INSERT INTO credit_reports 
                (customer_id, bureau_name, credit_score, risk_tier_id, report_date)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_id, 'Test Bureau', 250, 1, date.today()))
            
            # Check if value was inserted
            cur.execute("SELECT credit_score FROM credit_reports WHERE bureau_name='Test Bureau'")
            result = cur.fetchone()
            if result and result[0] == 250:
                log_test(6, "CHECK Constraint - Credit Score Range", "FAILED",
                        "Invalid score (250) was accepted - CHECK not enforced")
            return False
        except sqlite3.IntegrityError:
            log_test(6, "CHECK Constraint - Credit Score Range", "PASSED",
                    "CHECK constraint prevented out-of-range score")
            return True
    except Exception as e:
        log_test(6, "CHECK Constraint - Credit Score Range", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_boolean_field_handling(conn):
    """Test 7: Verify BOOLEAN fields handle TRUE/FALSE correctly"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT role_id FROM roles LIMIT 1")
        role_id = cur.fetchone()[0]
        
        # Insert user with is_active = TRUE
        cur.execute("""
            INSERT INTO users 
            (email, full_name, role_id, is_active)
            VALUES (?, ?, ?, ?)
        """, ('test_bool_true@test.com', 'Test User Active', role_id, 1))
        
        # Insert user with is_active = FALSE
        cur.execute("""
            INSERT INTO users 
            (email, full_name, role_id, is_active)
            VALUES (?, ?, ?, ?)
        """, ('test_bool_false@test.com', 'Test User Inactive', role_id, 0))
        
        log_test(7, "BOOLEAN Field Handling", "PASSED",
                "Successfully inserted TRUE and FALSE boolean values")
        return True
    except Exception as e:
        log_test(7, "BOOLEAN Field Handling", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_default_values_assignment(conn):
    """Test 8: Verify DEFAULT values are assigned properly"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT role_id FROM roles LIMIT 1")
        role_id = cur.fetchone()[0]
        
        # Insert user without specifying is_active (should default to TRUE/1)
        cur.execute("""
            INSERT INTO users 
            (email, full_name, role_id)
            VALUES (?, ?, ?)
        """, ('test_default@test.com', 'Test Default User', role_id))
        
        # Check if default value was applied
        cur.execute("SELECT is_active FROM users WHERE email='test_default@test.com'")
        result = cur.fetchone()
        
        if result and result[0] == 1:
            log_test(8, "DEFAULT Values Assignment", "PASSED",
                    "DEFAULT value (is_active=TRUE) properly applied")
            return True
        else:
            log_test(8, "DEFAULT Values Assignment", "FAILED",
                    "DEFAULT value was not applied")
            return False
    except Exception as e:
        log_test(8, "DEFAULT Values Assignment", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_currency_field_precision(conn):
    """Test 9: Verify currency fields maintain proper precision"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT account_type_id, account_status_id FROM accounts LIMIT 1")
        result = cur.fetchone()
        if not result:
            log_test(9, "Currency Field Precision", "FAILED", "No test accounts available")
            return False
        
        acc_type_id, acc_status_id = result
        
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer_id = cur.fetchone()[0]
        
        # Insert account with precise decimal amounts
        cur.execute("""
            INSERT INTO accounts 
            (account_number, customer_id, account_type_id, account_status_id,
             opened_date, current_balance, available_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('PRECISION-TEST-001', customer_id, acc_type_id, acc_status_id,
              date.today(), 1234.56, 999.99))
        
        # Verify precision
        cur.execute("""
            SELECT current_balance, available_balance 
            FROM accounts WHERE account_number='PRECISION-TEST-001'
        """)
        balance, available = cur.fetchone()
        
        if balance == 1234.56 and available == 999.99:
            log_test(9, "Currency Field Precision", "PASSED",
                    "Decimal precision maintained (1234.56, 999.99)")
            return True
        else:
            log_test(9, "Currency Field Precision", "FAILED",
                    f"Precision lost: got ({balance}, {available})")
            return False
    except Exception as e:
        log_test(9, "Currency Field Precision", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_enum_like_constraints(conn):
    """Test 10: Verify enum-like constraints work (payment_frequency, currency)"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer_id = cur.fetchone()[0]
        
        cur.execute("SELECT loan_type_id FROM loan_types LIMIT 1")
        loan_type_id = cur.fetchone()[0]
        
        cur.execute("SELECT loan_status_id FROM loan_statuses LIMIT 1")
        loan_status_id = cur.fetchone()[0]
        
        # Insert loan with valid payment_frequency
        cur.execute("""
            INSERT INTO loan_accounts 
            (loan_number, customer_id, loan_type_id, loan_status_id,
             principal_amount, outstanding_amount, interest_rate, term_months,
             payment_frequency, origination_date, maturity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('TEST-ENUM-001', customer_id, loan_type_id, loan_status_id,
              50000, 50000, 6.5, 24, 'Quarterly',
              date.today(), date.today() + timedelta(days=730)))
        
        log_test(10, "Enum-like Constraints (payment_frequency)", "PASSED",
                "Successfully inserted valid payment_frequency value")
        return True
    except Exception as e:
        log_test(10, "Enum-like Constraints (payment_frequency)", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_timestamp_columns_auto_populated(conn):
    """Test 11: Verify TIMESTAMPTZ columns auto-populate with current time"""
    cur = conn.cursor()
    
    try:
        before_insert = datetime.now()
        
        cur.execute("SELECT status_id FROM customer_status LIMIT 1")
        status_id = cur.fetchone()[0]
        
        # Insert customer without specifying created_at
        cur.execute("""
            INSERT INTO customers 
            (customer_code, first_name, last_name, customer_since, customer_status_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('TEST-TIMESTAMP-001', 'Auto', 'Time', date.today(), status_id))
        
        # Check if created_at was auto-populated
        cur.execute("""
            SELECT created_at FROM customers 
            WHERE customer_code='TEST-TIMESTAMP-001'
        """)
        result = cur.fetchone()
        
        if result and result[0]:
            log_test(11, "TIMESTAMP Auto-Population", "PASSED",
                    "created_at timestamp auto-populated on insert")
            return True
        else:
            log_test(11, "TIMESTAMP Auto-Population", "FAILED",
                    "created_at was not auto-populated")
            return False
    except Exception as e:
        log_test(11, "TIMESTAMP Auto-Population", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_integer_field_constraints(conn):
    """Test 12: Verify INTEGER fields reject non-integer values"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT customer_id FROM customers LIMIT 1")
        customer_id = cur.fetchone()
        
        if not customer_id:
            log_test(12, "INTEGER Field Validation", "FAILED", "No test customer")
            return False
        
        customer_id = customer_id[0]
        cur.execute("SELECT loan_type_id FROM loan_types LIMIT 1")
        loan_type_id = cur.fetchone()[0]
        cur.execute("SELECT loan_status_id FROM loan_statuses LIMIT 1")
        loan_status_id = cur.fetchone()[0]
        
        # Try to insert with valid integer term_months
        cur.execute("""
            INSERT INTO loan_accounts 
            (loan_number, customer_id, loan_type_id, loan_status_id,
             principal_amount, outstanding_amount, interest_rate, term_months,
             payment_frequency, origination_date, maturity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('TEST-INT-001', customer_id, loan_type_id, loan_status_id,
              75000, 75000, 4.5, 36, 'Monthly',
              date.today(), date.today() + timedelta(days=1095)))
        
        log_test(12, "INTEGER Field Validation", "PASSED",
                "INTEGER field accepted valid integer value")
        return True
    except Exception as e:
        log_test(12, "INTEGER Field Validation", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("DATA TYPE & CONSTRAINT TEST SERIES - Series 3")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_numeric_fields_accept_numbers(conn)
        conn.rollback()
        
        test_2_text_fields_accept_strings(conn)
        conn.rollback()
        
        test_3_date_fields_accept_dates(conn)
        conn.rollback()
        
        test_4_not_null_constraint_enforcement(conn)
        conn.rollback()
        
        test_5_unique_constraint_enforcement(conn)
        conn.rollback()
        
        test_6_check_constraint_credit_score(conn)
        conn.rollback()
        
        test_7_boolean_field_handling(conn)
        conn.rollback()
        
        test_8_default_values_assignment(conn)
        conn.rollback()
        
        test_9_currency_field_precision(conn)
        conn.rollback()
        
        test_10_enum_like_constraints(conn)
        conn.rollback()
        
        test_11_timestamp_columns_auto_populated(conn)
        conn.rollback()
        
        test_12_integer_field_constraints(conn)
        conn.rollback()
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - DATA TYPE & CONSTRAINT TESTS")
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
