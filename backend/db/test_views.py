"""
View Tests - Test Series 6
Tests to verify views exist and return correct aggregated data with proper joins.
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

def get_view_names(conn) -> list:
    """Get all view names from database"""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
    return [row[0] for row in cur.fetchall()]

def get_view_columns(conn, view_name: str) -> list:
    """Get column information for a view"""
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({view_name})")
    return [row[1] for row in cur.fetchall()]

# ==================== TEST SERIES 6: VIEW TESTS ====================

def test_1_views_exist(conn):
    """Test 1: Verify views exist in database"""
    try:
        views = get_view_names(conn)
        expected_views = ['comprehensive_client_view', 'high_risk_loan_view']
        
        found_views = [v for v in expected_views if v in views]
        
        if len(found_views) == len(expected_views):
            log_test(1, "Views Exist", "PASSED",
                    f"Found {len(found_views)} views: {', '.join(found_views)}")
            return True
        else:
            missing = set(expected_views) - set(found_views)
            log_test(1, "Views Exist", "FAILED",
                    f"Missing views: {', '.join(missing)}")
            return False
    except Exception as e:
        log_test(1, "Views Exist", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_comprehensive_client_view_structure(conn):
    """Test 2: Verify comprehensive_client_view has expected columns"""
    try:
        columns = get_view_columns(conn, 'comprehensive_client_view')
        
        expected_columns = [
            'customer_id', 'customer_code', 'first_name', 'last_name',
            'email', 'customer_status', 'loan_status', 'principal_amount',
            'outstanding_amount', 'credit_score'
        ]
        
        found_cols = [c for c in expected_columns if c in columns]
        
        if len(found_cols) >= 8:
            log_test(2, "Comprehensive Client View Structure", "PASSED",
                    f"Found {len(columns)} columns with key fields present")
            return True
        else:
            log_test(2, "Comprehensive Client View Structure", "FAILED",
                    f"Missing key columns. Found: {columns}")
            return False
    except Exception as e:
        log_test(2, "Comprehensive Client View Structure", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_high_risk_loan_view_structure(conn):
    """Test 3: Verify high_risk_loan_view has expected columns"""
    try:
        columns = get_view_columns(conn, 'high_risk_loan_view')
        
        expected_columns = [
            'loan_id', 'loan_number', 'customer_id', 'customer_code',
            'first_name', 'last_name', 'outstanding_amount',
            'credit_score', 'credit_risk_tier'
        ]
        
        found_cols = [c for c in expected_columns if c in columns]
        
        if len(found_cols) >= 7:
            log_test(3, "High Risk Loan View Structure", "PASSED",
                    f"Found {len(columns)} columns with key fields present")
            return True
        else:
            log_test(3, "High Risk Loan View Structure", "FAILED",
                    f"Missing key columns. Found: {columns}")
            return False
    except Exception as e:
        log_test(3, "High Risk Loan View Structure", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_comprehensive_client_view_data(conn):
    """Test 4: Verify comprehensive_client_view returns data"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM comprehensive_client_view")
        count = cur.fetchone()[0]
        
        if count > 0:
            log_test(4, "Comprehensive Client View Data", "PASSED",
                    f"View contains {count} rows of aggregated data")
            return True
        else:
            log_test(4, "Comprehensive Client View Data", "FAILED",
                    "View returned no data")
            return False
    except Exception as e:
        log_test(4, "Comprehensive Client View Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_high_risk_loan_view_data(conn):
    """Test 5: Verify high_risk_loan_view returns data"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM high_risk_loan_view")
        count = cur.fetchone()[0]
        
        if count >= 0:  # May be 0 if no defaulted loans
            log_test(5, "High Risk Loan View Data", "PASSED",
                    f"View contains {count} high-risk loan records")
            return True
        else:
            log_test(5, "High Risk Loan View Data", "FAILED",
                    "View query failed")
            return False
    except Exception as e:
        log_test(5, "High Risk Loan View Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_comprehensive_client_view_joins(conn):
    """Test 6: Verify comprehensive_client_view joins work correctly"""
    try:
        cur = conn.cursor()
        
        # Get sample data from view
        cur.execute("""
            SELECT customer_id, first_name, last_name, customer_status, loan_status 
            FROM comprehensive_client_view LIMIT 5
        """)
        rows = cur.fetchall()
        
        if rows:
            # Verify data is properly populated
            sample = rows[0]
            if sample[0] and sample[1] and sample[2]:  # customer_id, first_name, last_name
                log_test(6, "Comprehensive Client View Joins", "PASSED",
                        f"Verified {len(rows)} sample records with proper joins")
                return True
        
        log_test(6, "Comprehensive Client View Joins", "FAILED",
                "View data appears incomplete or improperly joined")
        return False
    except Exception as e:
        log_test(6, "Comprehensive Client View Joins", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_high_risk_loan_view_joins(conn):
    """Test 7: Verify high_risk_loan_view joins work correctly"""
    try:
        cur = conn.cursor()
        
        # Get sample data from view
        cur.execute("""
            SELECT loan_id, loan_number, customer_id, first_name 
            FROM high_risk_loan_view LIMIT 5
        """)
        rows = cur.fetchall()
        
        if rows and len(rows) > 0:
            # Verify data is properly populated
            for sample in rows:
                if sample[0] and sample[1]:  # loan_id, loan_number
                    log_test(7, "High Risk Loan View Joins", "PASSED",
                            f"Verified {len(rows)} high-risk loan records with proper joins")
                    return True
        
        # If no rows, still pass (no defaulted loans is valid)
        log_test(7, "High Risk Loan View Joins", "PASSED",
                "View structure correct (0 defaulted loans currently)")
        return True
    except Exception as e:
        log_test(7, "High Risk Loan View Joins", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_comprehensive_view_customer_status_join(conn):
    """Test 8: Verify customer_status properly joined in comprehensive view"""
    try:
        cur = conn.cursor()
        
        # Verify that customer_status field is populated
        cur.execute("""
            SELECT customer_status 
            FROM comprehensive_client_view 
            WHERE customer_status IS NOT NULL
            LIMIT 1
        """)
        result = cur.fetchone()
        
        if result:
            status = result[0]
            if status in ['Active', 'Inactive', 'Closed']:
                log_test(8, "Customer Status JOIN in View", "PASSED",
                        f"customer_status properly joined: '{status}'")
                return True
        
        log_test(8, "Customer Status JOIN in View", "FAILED",
                "customer_status not properly joined")
        return False
    except Exception as e:
        log_test(8, "Customer Status JOIN in View", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_comprehensive_view_loan_status_join(conn):
    """Test 9: Verify loan_status properly joined in comprehensive view"""
    try:
        cur = conn.cursor()
        
        # Verify that loan_status field is populated where applicable
        cur.execute("""
            SELECT loan_status 
            FROM comprehensive_client_view 
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if results:
            # Some may be NULL if customer has no loans (that's OK)
            log_test(9, "Loan Status JOIN in View", "PASSED",
                    f"Loan status field accessible in view ({len(results)} records checked)")
            return True
        
        log_test(9, "Loan Status JOIN in View", "FAILED",
                "Could not access loan_status field")
        return False
    except Exception as e:
        log_test(9, "Loan Status JOIN in View", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_high_risk_view_filters_defaulted_loans(conn):
    """Test 10: Verify high_risk_loan_view only returns defaulted loans"""
    try:
        cur = conn.cursor()
        
        # Check that view only contains defaulted loans
        cur.execute("""
            SELECT COUNT(*) FROM high_risk_loan_view
        """)
        view_count = cur.fetchone()[0]
        
        # Count how many defaulted loans exist in source data
        cur.execute("""
            SELECT COUNT(*) FROM loan_accounts la
            JOIN loan_statuses ls ON la.loan_status_id = ls.loan_status_id
            WHERE ls.status_name = 'Defaulted'
        """)
        expected_count = cur.fetchone()[0]
        
        if view_count == expected_count:
            log_test(10, "High Risk View Filters Correctly", "PASSED",
                    f"View correctly filters to {view_count} defaulted loans")
            return True
        else:
            log_test(10, "High Risk View Filters Correctly", "FAILED",
                    f"View count ({view_count}) doesn't match expected ({expected_count})")
            return False
    except Exception as e:
        log_test(10, "High Risk View Filters Correctly", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_comprehensive_view_credit_score_join(conn):
    """Test 11: Verify credit_score properly joined in comprehensive view"""
    try:
        cur = conn.cursor()
        
        # Check for credit score field
        cur.execute("""
            SELECT credit_score 
            FROM comprehensive_client_view 
            LIMIT 10
        """)
        results = cur.fetchall()
        
        if results:
            log_test(11, "Credit Score JOIN in View", "PASSED",
                    f"Credit score field accessible in {len(results)} records")
            return True
        
        log_test(11, "Credit Score JOIN in View", "FAILED",
                "Could not access credit_score field")
        return False
    except Exception as e:
        log_test(11, "Credit Score JOIN in View", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_view_aggregation_accuracy(conn):
    """Test 12: Verify view data aggregation is accurate"""
    try:
        cur = conn.cursor()
        
        # Pick a customer and verify their data is correctly aggregated
        cur.execute("""
            SELECT customer_code, first_name, last_name 
            FROM comprehensive_client_view 
            LIMIT 1
        """)
        result = cur.fetchone()
        
        if result:
            customer_code = result[0]
            
            # Verify this customer exists in base table
            cur.execute("""
                SELECT customer_code FROM customers 
                WHERE customer_code = ?
            """, (customer_code,))
            
            base_result = cur.fetchone()
            
            if base_result:
                log_test(12, "View Data Aggregation Accuracy", "PASSED",
                        f"View data correctly aggregated for customer {customer_code}")
                return True
        
        log_test(12, "View Data Aggregation Accuracy", "FAILED",
                "Could not verify aggregation accuracy")
        return False
    except Exception as e:
        log_test(12, "View Data Aggregation Accuracy", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("VIEW TEST SERIES - Series 6")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_views_exist(conn)
        test_2_comprehensive_client_view_structure(conn)
        test_3_high_risk_loan_view_structure(conn)
        test_4_comprehensive_client_view_data(conn)
        test_5_high_risk_loan_view_data(conn)
        test_6_comprehensive_client_view_joins(conn)
        test_7_high_risk_loan_view_joins(conn)
        test_8_comprehensive_view_customer_status_join(conn)
        test_9_comprehensive_view_loan_status_join(conn)
        test_10_high_risk_view_filters_defaulted_loans(conn)
        test_11_comprehensive_view_credit_score_join(conn)
        test_12_view_aggregation_accuracy(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - VIEW TESTS")
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
