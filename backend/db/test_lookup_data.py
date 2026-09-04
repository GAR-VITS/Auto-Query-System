"""
Lookup Data Tests - Test Series 5
Tests to verify all seed data inserted correctly and lookup tables contain expected values.
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

# ==================== TEST SERIES 5: LOOKUP DATA TESTS ====================

def test_1_customer_status_seeded(conn):
    """Test 1: Verify customer_status lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM customer_status")
        count = cur.fetchone()[0]
        
        expected_statuses = ['Active', 'Inactive', 'Closed']
        cur.execute("SELECT status_name FROM customer_status")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if count >= 3 and found_all:
            log_test(1, "Customer Status Seed Data", "PASSED",
                    f"Found {count} statuses: {', '.join(expected_statuses)}")
            return True
        else:
            log_test(1, "Customer Status Seed Data", "FAILED",
                    f"Expected 3+ statuses, found {count}. Missing: {set(expected_statuses) - set(existing)}")
            return False
    except Exception as e:
        log_test(1, "Customer Status Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_account_types_seeded(conn):
    """Test 2: Verify account_types lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM account_types")
        count = cur.fetchone()[0]
        
        expected_types = ['Savings', 'Current', 'Loan']
        cur.execute("SELECT type_name FROM account_types")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(atype in existing for atype in expected_types)
        
        if count >= 3 and found_all:
            log_test(2, "Account Types Seed Data", "PASSED",
                    f"Found {count} types: {', '.join(expected_types)}")
            return True
        else:
            log_test(2, "Account Types Seed Data", "FAILED",
                    f"Expected 3+ types, found {count}. Missing: {set(expected_types) - set(existing)}")
            return False
    except Exception as e:
        log_test(2, "Account Types Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_account_statuses_seeded(conn):
    """Test 3: Verify account_statuses lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM account_statuses")
        count = cur.fetchone()[0]
        
        expected_statuses = ['Active', 'Frozen', 'Closed']
        cur.execute("SELECT status_name FROM account_statuses")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if count >= 3 and found_all:
            log_test(3, "Account Statuses Seed Data", "PASSED",
                    f"Found {count} statuses: {', '.join(expected_statuses)}")
            return True
        else:
            log_test(3, "Account Statuses Seed Data", "FAILED",
                    f"Expected 3+ statuses, found {count}")
            return False
    except Exception as e:
        log_test(3, "Account Statuses Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_loan_types_seeded(conn):
    """Test 4: Verify loan_types lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM loan_types")
        count = cur.fetchone()[0]
        
        expected_types = ['Personal', 'Mortgage', 'Business']
        cur.execute("SELECT loan_type_name FROM loan_types")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(ltype in existing for ltype in expected_types)
        
        if count >= 3 and found_all:
            log_test(4, "Loan Types Seed Data", "PASSED",
                    f"Found {count} types: {', '.join(expected_types)}")
            return True
        else:
            log_test(4, "Loan Types Seed Data", "FAILED",
                    f"Expected 3+ types, found {count}")
            return False
    except Exception as e:
        log_test(4, "Loan Types Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_loan_statuses_seeded(conn):
    """Test 5: Verify loan_statuses lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM loan_statuses")
        count = cur.fetchone()[0]
        
        expected_statuses = ['Active', 'Paid Off', 'Defaulted', 'Review', 'Closed']
        cur.execute("SELECT status_name FROM loan_statuses")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if count >= 5 and found_all:
            log_test(5, "Loan Statuses Seed Data", "PASSED",
                    f"Found {count} statuses: {', '.join(expected_statuses)}")
            return True
        else:
            log_test(5, "Loan Statuses Seed Data", "FAILED",
                    f"Expected 5+ statuses, found {count}")
            return False
    except Exception as e:
        log_test(5, "Loan Statuses Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_payment_statuses_seeded(conn):
    """Test 6: Verify payment_statuses lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM payment_statuses")
        count = cur.fetchone()[0]
        
        expected_statuses = ['Due', 'Paid', 'Late', 'Missed']
        cur.execute("SELECT status_name FROM payment_statuses")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if count >= 4 and found_all:
            log_test(6, "Payment Statuses Seed Data", "PASSED",
                    f"Found {count} statuses: {', '.join(expected_statuses)}")
            return True
        else:
            log_test(6, "Payment Statuses Seed Data", "FAILED",
                    f"Expected 4+ statuses, found {count}")
            return False
    except Exception as e:
        log_test(6, "Payment Statuses Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_transaction_types_seeded(conn):
    """Test 7: Verify transaction_types lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM transaction_types")
        count = cur.fetchone()[0]
        
        expected_types = ['Payment', 'Disbursement', 'Fee', 'Adjustment']
        cur.execute("SELECT type_name FROM transaction_types")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(ttype in existing for ttype in expected_types)
        
        if count >= 4 and found_all:
            log_test(7, "Transaction Types Seed Data", "PASSED",
                    f"Found {count} types: {', '.join(expected_types)}")
            return True
        else:
            log_test(7, "Transaction Types Seed Data", "FAILED",
                    f"Expected 4+ types, found {count}")
            return False
    except Exception as e:
        log_test(7, "Transaction Types Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_risk_tiers_seeded(conn):
    """Test 8: Verify risk_tiers lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM risk_tiers")
        count = cur.fetchone()[0]
        
        expected_tiers = ['Low Risk', 'Medium Risk', 'High Risk', 'Critical']
        cur.execute("SELECT tier_name FROM risk_tiers")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(tier in existing for tier in expected_tiers)
        
        if count >= 4 and found_all:
            log_test(8, "Risk Tiers Seed Data", "PASSED",
                    f"Found {count} tiers: {', '.join(expected_tiers)}")
            return True
        else:
            log_test(8, "Risk Tiers Seed Data", "FAILED",
                    f"Expected 4+ tiers, found {count}")
            return False
    except Exception as e:
        log_test(8, "Risk Tiers Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_roles_seeded(conn):
    """Test 9: Verify roles lookup table has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM roles")
        count = cur.fetchone()[0]
        
        expected_roles = ['admin', 'analyst', 'manager', 'viewer']
        cur.execute("SELECT role_name FROM roles")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(role in existing for role in expected_roles)
        
        if count >= 4 and found_all:
            log_test(9, "Roles Seed Data", "PASSED",
                    f"Found {count} roles: {', '.join(expected_roles)}")
            return True
        else:
            log_test(9, "Roles Seed Data", "FAILED",
                    f"Expected 4+ roles, found {count}")
            return False
    except Exception as e:
        log_test(9, "Roles Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_agents_seeded(conn):
    """Test 10: Verify agents registry has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM agents")
        count = cur.fetchone()[0]
        
        expected_agents = ['query', 'analysis', 'visualization']
        cur.execute("SELECT agent_code FROM agents")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(agent in existing for agent in expected_agents)
        
        if count >= 3 and found_all:
            log_test(10, "Agents Registry Seed Data", "PASSED",
                    f"Found {count} agents: {', '.join(expected_agents)}")
            return True
        else:
            log_test(10, "Agents Registry Seed Data", "FAILED",
                    f"Expected 3+ agents, found {count}")
            return False
    except Exception as e:
        log_test(10, "Agents Registry Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_audit_action_types_seeded(conn):
    """Test 11: Verify audit_action_types has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM audit_action_types")
        count = cur.fetchone()[0]
        
        expected_actions = ['query_executed', 'credit_evaluation', 'defaulter_flagged', 'loan_approved', 'status_updated']
        cur.execute("SELECT action_name FROM audit_action_types")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(action in existing for action in expected_actions)
        
        if count >= 5 and found_all:
            log_test(11, "Audit Action Types Seed Data", "PASSED",
                    f"Found {count} action types: {', '.join(expected_actions)}")
            return True
        else:
            log_test(11, "Audit Action Types Seed Data", "FAILED",
                    f"Expected 5+ action types, found {count}")
            return False
    except Exception as e:
        log_test(11, "Audit Action Types Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_audit_statuses_seeded(conn):
    """Test 12: Verify audit_statuses has seed data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM audit_statuses")
        count = cur.fetchone()[0]
        
        expected_statuses = ['approved', 'pending', 'rejected', 'auto_executed']
        cur.execute("SELECT status_name FROM audit_statuses")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if count >= 4 and found_all:
            log_test(12, "Audit Statuses Seed Data", "PASSED",
                    f"Found {count} statuses: {', '.join(expected_statuses)}")
            return True
        else:
            log_test(12, "Audit Statuses Seed Data", "FAILED",
                    f"Expected 4+ statuses, found {count}")
            return False
    except Exception as e:
        log_test(12, "Audit Statuses Seed Data", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("LOOKUP DATA TEST SERIES - Series 5")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_customer_status_seeded(conn)
        test_2_account_types_seeded(conn)
        test_3_account_statuses_seeded(conn)
        test_4_loan_types_seeded(conn)
        test_5_loan_statuses_seeded(conn)
        test_6_payment_statuses_seeded(conn)
        test_7_transaction_types_seeded(conn)
        test_8_risk_tiers_seeded(conn)
        test_9_roles_seeded(conn)
        test_10_agents_seeded(conn)
        test_11_audit_action_types_seeded(conn)
        test_12_audit_statuses_seeded(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - LOOKUP DATA")
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
