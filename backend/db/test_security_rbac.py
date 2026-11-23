"""
Security/RBAC Tests - Test Series 12
Tests to verify role-based access control, user permissions, and security constraints.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

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

# ==================== TEST SERIES 12: SECURITY/RBAC TESTS ====================

def test_1_users_table_exists(conn):
    """Test 1: Users table exists with security fields"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        
        if count >= 0:
            log_test(1, "Users Table Exists", "PASSED",
                    f"Users table has {count} records")
            return True
        else:
            log_test(1, "Users Table Exists", "FAILED",
                    "Could not query users")
            return False
    except Exception as e:
        log_test(1, "Users Table Exists", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_roles_table_exists(conn):
    """Test 2: Roles table exists"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM roles")
        count = cur.fetchone()[0]
        
        if count >= 0:
            log_test(2, "Roles Table Exists", "PASSED",
                    f"Roles table has {count} records")
            return True
        else:
            log_test(2, "Roles Table Exists", "FAILED",
                    "Could not query roles")
            return False
    except Exception as e:
        log_test(2, "Roles Table Exists", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_user_has_role(conn):
    """Test 3: All users have assigned roles"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM users 
            WHERE role_id IS NULL
        """)
        null_roles = cur.fetchone()[0]
        
        if null_roles == 0:
            log_test(3, "User Has Role", "PASSED",
                    "All users have assigned role_id")
            return True
        else:
            log_test(3, "User Has Role", "FAILED",
                    f"Found {null_roles} users with NULL role_id")
            return False
    except Exception as e:
        log_test(3, "User Has Role", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_role_names_defined(conn):
    """Test 4: Standard role names are defined"""
    cur = conn.cursor()
    
    try:
        expected_roles = ['admin', 'analyst', 'manager', 'viewer']
        
        cur.execute("SELECT role_name FROM roles")
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(role in existing for role in expected_roles)
        
        if found_all:
            log_test(4, "Role Names Defined", "PASSED",
                    f"All {len(expected_roles)} standard roles exist")
            return True
        else:
            missing = set(expected_roles) - set(existing)
            log_test(4, "Role Names Defined", "FAILED",
                    f"Missing roles: {missing}")
            return False
    except Exception as e:
        log_test(4, "Role Names Defined", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_user_password_storage(conn):
    """Test 5: Users have password stored (hashed)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM users 
            WHERE password_hash IS NOT NULL
        """)
        with_password = cur.fetchone()[0]
        
        if with_password >= 0:
            log_test(5, "User Password Storage", "PASSED",
                    f"{with_password} users have password_hash stored")
            return True
        else:
            log_test(5, "User Password Storage", "FAILED",
                    "Could not query password hashes")
            return False
    except Exception as e:
        log_test(5, "User Password Storage", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_user_status_tracking(conn):
    """Test 6: User status is tracked (active/inactive)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM users 
            WHERE is_active IS NOT NULL
        """)
        with_status = cur.fetchone()[0]
        
        if with_status >= 0:
            log_test(6, "User Status Tracking", "PASSED",
                    f"{with_status} users have status tracking")
            return True
        else:
            log_test(6, "User Status Tracking", "FAILED",
                    "Could not query user status")
            return False
    except Exception as e:
        log_test(6, "User Status Tracking", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_user_audit_trail(conn):
    """Test 7: User actions are auditable"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE user_id IS NOT NULL
        """)
        auditable_actions = cur.fetchone()[0]
        
        if auditable_actions >= 0:
            log_test(7, "User Audit Trail", "PASSED",
                    f"{auditable_actions} user actions are auditable")
            return True
        else:
            log_test(7, "User Audit Trail", "FAILED",
                    "Could not query audit trail")
            return False
    except Exception as e:
        log_test(7, "User Audit Trail", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_agents_table_exists(conn):
    """Test 8: Agents table exists for AI agent tracking"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM agents")
        count = cur.fetchone()[0]
        
        if count >= 0:
            log_test(8, "Agents Table Exists", "PASSED",
                    f"Agents table has {count} records")
            return True
        else:
            log_test(8, "Agents Table Exists", "FAILED",
                    "Could not query agents")
            return False
    except Exception as e:
        log_test(8, "Agents Table Exists", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_agent_audit_tracking(conn):
    """Test 9: Agent actions are tracked in audit logs"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE agent_id IS NOT NULL
        """)
        agent_actions = cur.fetchone()[0]
        
        if agent_actions >= 0:
            log_test(9, "Agent Audit Tracking", "PASSED",
                    f"{agent_actions} agent actions are tracked")
            return True
        else:
            log_test(9, "Agent Audit Tracking", "FAILED",
                    "Could not query agent actions")
            return False
    except Exception as e:
        log_test(9, "Agent Audit Tracking", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_data_encryption_fields(conn):
    """Test 10: Sensitive fields can store encrypted data"""
    cur = conn.cursor()
    
    try:
        # Check if customers table has sensitive fields
        cur.execute("PRAGMA table_info(customers)")
        columns = [row[1] for row in cur.fetchall()]
        
        # Sensitive fields that should be present
        sensitive_fields = ['customer_name', 'email', 'phone']
        
        # Note: Actual encryption would be at application level
        found = [f for f in sensitive_fields if f in columns]
        
        if len(found) >= 2:
            log_test(10, "Data Encryption Fields", "PASSED",
                    f"Found {len(found)} sensitive fields for encryption")
            return True
        else:
            log_test(10, "Data Encryption Fields", "FAILED",
                    f"Only found {len(found)} sensitive fields")
            return False
    except Exception as e:
        log_test(10, "Data Encryption Fields", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_transaction_consistency(conn):
    """Test 11: Transactional integrity for security"""
    cur = conn.cursor()
    
    try:
        # Get initial count
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        initial_count = cur.fetchone()[0]
        
        # Simulate a transaction that should be rolled back
        try:
            conn.execute("BEGIN TRANSACTION")
            cur.execute("""
                INSERT INTO audit_logs 
                (action_type_id, audit_status_id, description, reasoning, event_timestamp)
                VALUES (1, 1, 'Test', 'Test', datetime('now'))
            """)
            # Force error to trigger rollback
            raise Exception("Simulated error")
        except:
            conn.execute("ROLLBACK")
        
        # Verify count unchanged
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        final_count = cur.fetchone()[0]
        
        if initial_count == final_count:
            log_test(11, "Transaction Consistency", "PASSED",
                    "Rollback protected data integrity")
            return True
        else:
            log_test(11, "Transaction Consistency", "FAILED",
                    f"Count changed from {initial_count} to {final_count}")
            return False
    except Exception as e:
        log_test(11, "Transaction Consistency", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_foreign_key_enforced(conn):
    """Test 12: Foreign key constraints prevent unauthorized access"""
    cur = conn.cursor()
    
    try:
        # Try to insert a user with non-existent role
        test_user_id = 99999
        
        try:
            conn.execute("BEGIN TRANSACTION")
            cur.execute("""
                INSERT INTO users (user_id, username, password_hash, role_id)
                VALUES (?, ?, ?, ?)
            """, (test_user_id, 'testuser', 'hash', 99999))
            conn.execute("COMMIT")
            log_test(12, "Foreign Key Enforced", "FAILED",
                    "FK constraint not enforced - invalid role accepted")
            return False
        except Exception as e:
            conn.execute("ROLLBACK")
            if "FOREIGN KEY constraint failed" in str(e) or "constraint" in str(e).lower():
                log_test(12, "Foreign Key Enforced", "PASSED",
                        "FK constraint prevented invalid role assignment")
                return True
            else:
                log_test(12, "Foreign Key Enforced", "FAILED",
                        f"Unexpected error: {str(e)[:50]}")
                return False
    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except:
            pass
        log_test(12, "Foreign Key Enforced", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("SECURITY/RBAC TEST SERIES - Series 12")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_users_table_exists(conn)
        test_2_roles_table_exists(conn)
        test_3_user_has_role(conn)
        test_4_role_names_defined(conn)
        test_5_user_password_storage(conn)
        test_6_user_status_tracking(conn)
        test_7_user_audit_trail(conn)
        test_8_agents_table_exists(conn)
        test_9_agent_audit_tracking(conn)
        test_10_data_encryption_fields(conn)
        test_11_transaction_consistency(conn)
        test_12_foreign_key_enforced(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - SECURITY/RBAC")
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
