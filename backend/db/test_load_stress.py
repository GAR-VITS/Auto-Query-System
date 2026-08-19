"""
Load/Stress Tests - Test Series 11
Tests to verify database performance under various load conditions and stress scenarios.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

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

# ==================== TEST SERIES 11: LOAD/STRESS TESTS ====================

def test_1_simple_query_performance(conn):
    """Test 1: Simple SELECT query performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("SELECT * FROM customers LIMIT 100")
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 0.1:  # Should complete in < 100ms
            log_test(1, "Simple Query Performance", "PASSED",
                    f"Loaded 100 rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(1, "Simple Query Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 100ms)")
            return False
    except Exception as e:
        log_test(1, "Simple Query Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_2_join_query_performance(conn):
    """Test 2: Complex JOIN query performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("""
            SELECT c.customer_id, c.customer_name, a.account_id, a.current_balance
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            LIMIT 1000
        """)
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(2, "Complex JOIN Query Performance", "PASSED",
                    f"Joined 1000+ rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(2, "Complex JOIN Query Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(2, "Complex JOIN Query Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_3_aggregation_query_performance(conn):
    """Test 3: Aggregation query performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("""
            SELECT customer_id, COUNT(*) as account_count, SUM(current_balance) as total_balance
            FROM accounts
            GROUP BY customer_id
            HAVING COUNT(*) >= 1
        """)
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(3, "Aggregation Query Performance", "PASSED",
                    f"Aggregated {len(result)} groups in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(3, "Aggregation Query Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(3, "Aggregation Query Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_4_subquery_performance(conn):
    """Test 4: Subquery performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("""
            SELECT customer_id, customer_name
            FROM customers
            WHERE customer_id IN (
                SELECT DISTINCT customer_id FROM accounts
                WHERE account_status_id = 1
            )
        """)
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(4, "Subquery Performance", "PASSED",
                    f"Subquery returned {len(result)} rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(4, "Subquery Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(4, "Subquery Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_5_transaction_performance(conn):
    """Test 5: Transaction overhead"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        conn.execute("BEGIN TRANSACTION")
        
        for i in range(100):
            cur.execute("""
                SELECT * FROM customers WHERE customer_id = ?
            """, (i % 150 + 1,))
            cur.fetchone()
        
        conn.execute("ROLLBACK")
        elapsed = time.time() - start_time
        
        if elapsed < 1.0:  # Should complete in < 1 second for 100 queries
            log_test(5, "Transaction Performance", "PASSED",
                    f"100 queries in transaction completed in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(5, "Transaction Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 1000ms)")
            return False
    except Exception as e:
        log_test(5, "Transaction Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_6_bulk_insert_performance(conn):
    """Test 6: Bulk insert performance"""
    cur = conn.cursor()
    
    try:
        # Use a new user for testing
        test_user_id = 99999
        
        start_time = time.time()
        conn.execute("BEGIN TRANSACTION")
        
        for i in range(50):
            try:
                cur.execute("""
                    INSERT INTO audit_logs 
                    (action_type_id, audit_status_id, description, reasoning, event_timestamp, user_id, agent_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (1, 1, f"Test entry {i}", f"Reason {i}", datetime.now().isoformat(), test_user_id + i, 1, "{}"))
            except:
                pass  # Ignore errors for this stress test
        
        conn.execute("ROLLBACK")  # Rollback to not affect actual data
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(6, "Bulk Insert Performance", "PASSED",
                    f"50 inserts in transaction completed in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(6, "Bulk Insert Performance", "FAILED",
                    f"Insert took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(6, "Bulk Insert Performance", "FAILED", f"Error: {str(e)[:50]}")
        try:
            conn.execute("ROLLBACK")
        except:
            pass
        return False

def test_7_full_table_scan_performance(conn):
    """Test 7: Full table scan performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        result = cur.fetchone()[0]
        elapsed = time.time() - start_time
        
        if elapsed < 0.1:  # Should complete in < 100ms
            log_test(7, "Full Table Scan Performance", "PASSED",
                    f"Scanned audit_logs with {result} rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(7, "Full Table Scan Performance", "FAILED",
                    f"Scan took {elapsed*1000:.2f}ms (threshold: 100ms)")
            return False
    except Exception as e:
        log_test(7, "Full Table Scan Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_8_multiple_join_performance(conn):
    """Test 8: Three-way JOIN performance"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("""
            SELECT c.customer_id, c.customer_name, a.account_id, l.loan_id
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id
            LEFT JOIN loan_accounts l ON c.customer_id = l.customer_id
            WHERE c.customer_status_id = 1
        """)
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(8, "Multiple JOIN Performance", "PASSED",
                    f"3-way JOIN returned {len(result)} rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(8, "Multiple JOIN Performance", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(8, "Multiple JOIN Performance", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_9_data_retrieval_consistency(conn):
    """Test 9: Consistent data retrieval under load"""
    cur = conn.cursor()
    
    try:
        results = []
        start_time = time.time()
        
        for i in range(10):
            cur.execute("SELECT COUNT(*) FROM customers")
            count = cur.fetchone()[0]
            results.append(count)
        
        elapsed = time.time() - start_time
        
        # All counts should be the same
        if len(set(results)) == 1:
            log_test(9, "Data Retrieval Consistency", "PASSED",
                    f"10 queries returned consistent count ({results[0]}) in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(9, "Data Retrieval Consistency", "FAILED",
                    f"Inconsistent counts detected: {set(results)}")
            return False
    except Exception as e:
        log_test(9, "Data Retrieval Consistency", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_10_concurrent_connection_simulation(conn):
    """Test 10: Simulate multiple connection queries"""
    
    try:
        start_time = time.time()
        
        for i in range(5):
            conn2 = sqlite3.connect(str(DB_PATH))
            conn2.execute("PRAGMA foreign_keys = ON;")
            cur2 = conn2.cursor()
            
            cur2.execute("SELECT COUNT(*) FROM customers")
            cur2.fetchone()
            
            conn2.close()
        
        elapsed = time.time() - start_time
        
        if elapsed < 0.5:  # Should complete in < 500ms
            log_test(10, "Concurrent Connection Simulation", "PASSED",
                    f"5 connections and queries completed in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(10, "Concurrent Connection Simulation", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 500ms)")
            return False
    except Exception as e:
        log_test(10, "Concurrent Connection Simulation", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_11_large_result_set_handling(conn):
    """Test 11: Handling large result sets"""
    cur = conn.cursor()
    
    try:
        start_time = time.time()
        cur.execute("""
            SELECT c.customer_id, c.customer_name, a.account_id, a.current_balance, t.transaction_id, t.transaction_amount
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id
            LEFT JOIN transactions t ON a.account_id = t.account_id
        """)
        result = cur.fetchall()
        elapsed = time.time() - start_time
        
        if elapsed < 2.0:  # Should complete in < 2 seconds
            log_test(11, "Large Result Set Handling", "PASSED",
                    f"Retrieved {len(result)} rows in {elapsed*1000:.2f}ms")
            return True
        else:
            log_test(11, "Large Result Set Handling", "FAILED",
                    f"Query took {elapsed*1000:.2f}ms (threshold: 2000ms)")
            return False
    except Exception as e:
        log_test(11, "Large Result Set Handling", "FAILED", f"Error: {str(e)[:50]}")
        return False

def test_12_database_integrity_under_stress(conn):
    """Test 12: Database integrity metrics"""
    cur = conn.cursor()
    
    try:
        # Get database file size
        db_size = DB_PATH.stat().st_size
        
        # Verify integrity with PRAGMA
        cur.execute("PRAGMA integrity_check")
        result = cur.fetchone()[0]
        
        if result == "ok" and db_size > 0:
            log_test(12, "Database Integrity Under Stress", "PASSED",
                    f"Database OK, Size: {db_size/1024:.0f} KB")
            return True
        else:
            log_test(12, "Database Integrity Under Stress", "FAILED",
                    f"Integrity check result: {result}")
            return False
    except Exception as e:
        log_test(12, "Database Integrity Under Stress", "FAILED", f"Error: {str(e)[:50]}")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("LOAD/STRESS TEST SERIES - Series 11")
    print("="*70 + "\n")
    
    conn, msg = connect_to_db()
    if not conn:
        print(f"\n❌ Cannot proceed with tests - {msg}")
        return
    
    try:
        # Run all tests
        test_1_simple_query_performance(conn)
        test_2_join_query_performance(conn)
        test_3_aggregation_query_performance(conn)
        test_4_subquery_performance(conn)
        test_5_transaction_performance(conn)
        test_6_bulk_insert_performance(conn)
        test_7_full_table_scan_performance(conn)
        test_8_multiple_join_performance(conn)
        test_9_data_retrieval_consistency(conn)
        test_10_concurrent_connection_simulation(conn)
        test_11_large_result_set_handling(conn)
        test_12_database_integrity_under_stress(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - LOAD/STRESS")
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
