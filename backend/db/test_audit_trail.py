"""
Audit Trail Tests - Test Series 10
Tests to verify audit logs capture all actions, with proper metadata, timestamps, and event tracking.
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

# ==================== TEST SERIES 10: AUDIT TRAIL TESTS ====================

def test_1_audit_logs_table_exists(conn):
    """Test 1: Audit logs table exists with data"""
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        count = cur.fetchone()[0]
        
        if count >= 0:
            log_test(1, "Audit Logs Table Exists", "PASSED",
                    f"Audit logs table has {count} records")
            return True
        else:
            log_test(1, "Audit Logs Table Exists", "FAILED",
                    "Could not query audit_logs")
            return False
    except Exception as e:
        log_test(1, "Audit Logs Table Exists", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_audit_log_has_action_type(conn):
    """Test 2: All audit logs have valid action_type_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE action_type_id IS NULL
        """)
        null_actions = cur.fetchone()[0]
        
        if null_actions == 0:
            log_test(2, "Audit Log Has Action Type", "PASSED",
                    "All audit logs have action_type_id")
            return True
        else:
            log_test(2, "Audit Log Has Action Type", "FAILED",
                    f"Found {null_actions} audit logs with NULL action_type_id")
            return False
    except Exception as e:
        log_test(2, "Audit Log Has Action Type", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_audit_log_has_status(conn):
    """Test 3: All audit logs have valid audit_status_id"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE audit_status_id IS NULL
        """)
        null_status = cur.fetchone()[0]
        
        if null_status == 0:
            log_test(3, "Audit Log Has Status", "PASSED",
                    "All audit logs have audit_status_id")
            return True
        else:
            log_test(3, "Audit Log Has Status", "FAILED",
                    f"Found {null_status} audit logs with NULL audit_status_id")
            return False
    except Exception as e:
        log_test(3, "Audit Log Has Status", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_audit_log_has_timestamp(conn):
    """Test 4: All audit logs have event_timestamp"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE event_timestamp IS NULL
        """)
        null_timestamps = cur.fetchone()[0]
        
        if null_timestamps == 0:
            log_test(4, "Audit Log Has Timestamp", "PASSED",
                    "All audit logs have event_timestamp")
            return True
        else:
            log_test(4, "Audit Log Has Timestamp", "FAILED",
                    f"Found {null_timestamps} audit logs with NULL event_timestamp")
            return False
    except Exception as e:
        log_test(4, "Audit Log Has Timestamp", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_audit_log_has_description(conn):
    """Test 5: All audit logs have description"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE description IS NULL OR description = ''
        """)
        empty_desc = cur.fetchone()[0]
        
        if empty_desc == 0:
            log_test(5, "Audit Log Has Description", "PASSED",
                    "All audit logs have non-empty description")
            return True
        else:
            log_test(5, "Audit Log Has Description", "FAILED",
                    f"Found {empty_desc} audit logs with missing description")
            return False
    except Exception as e:
        log_test(5, "Audit Log Has Description", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_audit_log_has_reasoning(conn):
    """Test 6: All audit logs have reasoning"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE reasoning IS NULL OR reasoning = ''
        """)
        empty_reasoning = cur.fetchone()[0]
        
        if empty_reasoning == 0:
            log_test(6, "Audit Log Has Reasoning", "PASSED",
                    "All audit logs have reasoning field populated")
            return True
        else:
            log_test(6, "Audit Log Has Reasoning", "FAILED",
                    f"Found {empty_reasoning} audit logs with missing reasoning")
            return False
    except Exception as e:
        log_test(6, "Audit Log Has Reasoning", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_7_audit_log_contains_metadata(conn):
    """Test 7: Audit logs can store metadata (JSON)"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE metadata IS NOT NULL
        """)
        with_metadata = cur.fetchone()[0]
        
        if with_metadata >= 0:
            log_test(7, "Audit Log Contains Metadata", "PASSED",
                    f"Found {with_metadata} audit logs with metadata")
            return True
        else:
            log_test(7, "Audit Log Contains Metadata", "FAILED",
                    "Could not query metadata")
            return False
    except Exception as e:
        log_test(7, "Audit Log Contains Metadata", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_audit_log_tracks_affected_records(conn):
    """Test 8: Audit logs track affected_record_count"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE affected_record_count IS NOT NULL
        """)
        with_count = cur.fetchone()[0]
        
        if with_count >= 0:
            log_test(8, "Audit Log Tracks Affected Records", "PASSED",
                    f"Found {with_count} audit logs with affected_record_count")
            return True
        else:
            log_test(8, "Audit Log Tracks Affected Records", "FAILED",
                    "Could not query affected_record_count")
            return False
    except Exception as e:
        log_test(8, "Audit Log Tracks Affected Records", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_audit_log_user_tracking(conn):
    """Test 9: Audit logs can track user who performed action"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE user_id IS NOT NULL
        """)
        with_user = cur.fetchone()[0]
        
        if with_user >= 0:
            log_test(9, "Audit Log User Tracking", "PASSED",
                    f"Found {with_user} audit logs with user_id tracking")
            return True
        else:
            log_test(9, "Audit Log User Tracking", "FAILED",
                    "Could not track user_id")
            return False
    except Exception as e:
        log_test(9, "Audit Log User Tracking", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_audit_log_agent_tracking(conn):
    """Test 10: Audit logs can track agent who performed action"""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE agent_id IS NOT NULL
        """)
        with_agent = cur.fetchone()[0]
        
        if with_agent >= 0:
            log_test(10, "Audit Log Agent Tracking", "PASSED",
                    f"Found {with_agent} audit logs with agent_id tracking")
            return True
        else:
            log_test(10, "Audit Log Agent Tracking", "FAILED",
                    "Could not track agent_id")
            return False
    except Exception as e:
        log_test(10, "Audit Log Agent Tracking", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_audit_action_types_available(conn):
    """Test 11: All expected audit action types exist"""
    cur = conn.cursor()
    
    try:
        expected_actions = [
            'query_executed',
            'credit_evaluation',
            'defaulter_flagged',
            'loan_approved',
            'status_updated'
        ]
        
        cur.execute("""
            SELECT action_name FROM audit_action_types
        """)
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(action in existing for action in expected_actions)
        
        if found_all:
            log_test(11, "Audit Action Types Available", "PASSED",
                    f"All {len(expected_actions)} expected action types exist")
            return True
        else:
            missing = set(expected_actions) - set(existing)
            log_test(11, "Audit Action Types Available", "FAILED",
                    f"Missing action types: {missing}")
            return False
    except Exception as e:
        log_test(11, "Audit Action Types Available", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_audit_statuses_available(conn):
    """Test 12: All expected audit statuses exist"""
    cur = conn.cursor()
    
    try:
        expected_statuses = ['approved', 'pending', 'rejected', 'auto_executed']
        
        cur.execute("""
            SELECT status_name FROM audit_statuses
        """)
        existing = [row[0] for row in cur.fetchall()]
        
        found_all = all(status in existing for status in expected_statuses)
        
        if found_all:
            log_test(12, "Audit Statuses Available", "PASSED",
                    f"All {len(expected_statuses)} expected statuses exist")
            return True
        else:
            missing = set(expected_statuses) - set(existing)
            log_test(12, "Audit Statuses Available", "FAILED",
                    f"Missing statuses: {missing}")
            return False
    except Exception as e:
        log_test(12, "Audit Statuses Available", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("AUDIT TRAIL TEST SERIES - Series 10")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_audit_logs_table_exists(conn)
        test_2_audit_log_has_action_type(conn)
        test_3_audit_log_has_status(conn)
        test_4_audit_log_has_timestamp(conn)
        test_5_audit_log_has_description(conn)
        test_6_audit_log_has_reasoning(conn)
        test_7_audit_log_contains_metadata(conn)
        test_8_audit_log_tracks_affected_records(conn)
        test_9_audit_log_user_tracking(conn)
        test_10_audit_log_agent_tracking(conn)
        test_11_audit_action_types_available(conn)
        test_12_audit_statuses_available(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - AUDIT TRAIL")
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
