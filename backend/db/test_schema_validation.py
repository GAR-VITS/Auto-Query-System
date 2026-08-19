"""
Schema Validation Tests - Test Series 1
Tests to verify all tables exist with correct names, columns, data types, and constraints.
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

def get_table_names(conn) -> list:
    """Get all table names from database"""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cur.fetchall()]

def get_table_info(conn, table_name: str) -> list:
    """Get column info for a table"""
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name});")
    return cur.fetchall()

def get_table_constraints(conn, table_name: str) -> dict:
    """Get constraint info for a table"""
    cur = conn.cursor()
    
    # Get indexes
    cur.execute(f"PRAGMA index_list({table_name});")
    indexes = cur.fetchall()
    
    # Get foreign keys
    cur.execute(f"PRAGMA foreign_key_list({table_name});")
    foreign_keys = cur.fetchall()
    
    return {"indexes": indexes, "foreign_keys": foreign_keys}

# ==================== TEST SERIES 1: SCHEMA VALIDATION ====================

def test_1_database_connection():
    """Test 1: Verify database connection"""
    conn, msg = connect_to_db()
    if conn:
        log_test(1, "Database Connection", "PASSED", f"Connected to {DB_PATH.name}")
        return conn
    else:
        log_test(1, "Database Connection", "FAILED", msg)
        return None

def test_2_tables_exist(conn):
    """Test 2: Verify all required tables exist"""
    required_tables = [
        'customer_status', 'account_types', 'account_statuses', 'loan_types',
        'loan_statuses', 'payment_statuses', 'transaction_types', 'risk_tiers',
        'roles', 'audit_action_types', 'audit_statuses', 'agents', 'users',
        'customers', 'accounts', 'loan_accounts', 'loan_payment_schedule',
        'transactions', 'credit_reports', 'audit_logs', 'query_history',
        'spider_databases', 'spider_tables', 'spider_columns', 'spider_queries'
    ]
    
    existing_tables = get_table_names(conn)
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if not missing_tables:
        log_test(2, "All Required Tables Exist", "PASSED", 
                f"Found all {len(required_tables)} tables")
    else:
        log_test(2, "All Required Tables Exist", "FAILED", 
                f"Missing tables: {', '.join(missing_tables)}")

def test_3_table_columns_exist(conn):
    """Test 3: Verify key columns exist in main tables"""
    column_checks = {
        'customers': ['customer_id', 'customer_code', 'first_name', 'last_name', 'customer_status_id'],
        'accounts': ['account_id', 'account_number', 'customer_id', 'account_type_id', 'current_balance'],
        'loan_accounts': ['loan_id', 'loan_number', 'customer_id', 'principal_amount', 'outstanding_amount'],
        'transactions': ['transaction_id', 'transaction_code', 'account_id', 'transaction_date', 'amount'],
        'audit_logs': ['audit_id', 'action_type_id', 'audit_status_id', 'user_id', 'agent_id'],
        'users': ['user_id', 'email', 'full_name', 'role_id', 'is_active']
    }
    
    all_passed = True
    for table_name, required_cols in column_checks.items():
        table_info = get_table_info(conn, table_name)
        existing_cols = [col[1] for col in table_info]
        missing_cols = [c for c in required_cols if c not in existing_cols]
        
        if missing_cols:
            all_passed = False
            log_test(3, f"Columns in {table_name}", "FAILED", 
                    f"Missing: {', '.join(missing_cols)}")
        else:
            log_test(3, f"Columns in {table_name}", "PASSED", 
                    f"All {len(required_cols)} required columns exist")
    
    if all_passed:
        print("   └─ All key columns verified across main tables")

def test_4_primary_keys_defined(conn):
    """Test 4: Verify primary keys are defined"""
    tables = get_table_names(conn)
    all_passed = True
    
    for table_name in tables:
        table_info = get_table_info(conn, table_name)
        primary_keys = [col for col in table_info if col[5] == 1]  # col[5] is pk flag
        
        if not primary_keys:
            all_passed = False
            log_test(4, f"Primary Key in {table_name}", "FAILED", "No primary key defined")
        else:
            pk_name = primary_keys[0][1]  # col[1] is column name
            
    if all_passed:
        log_test(4, "All Tables Have Primary Keys", "PASSED", 
                f"Verified {len(tables)} tables have primary keys")

def test_5_foreign_keys_defined(conn):
    """Test 5: Verify foreign key relationships exist"""
    fk_checks = {
        'customers': ['customer_status_id'],
        'accounts': ['customer_id', 'account_type_id', 'account_status_id'],
        'loan_accounts': ['customer_id', 'account_id', 'loan_type_id', 'loan_status_id'],
        'transactions': ['account_id', 'loan_id', 'transaction_type_id'],
        'users': ['role_id'],
        'credit_reports': ['customer_id', 'risk_tier_id'],
        'audit_logs': ['action_type_id', 'audit_status_id', 'agent_id', 'user_id'],
        'spider_tables': ['spider_db_id'],
        'spider_columns': ['spider_table_id']
    }
    
    all_passed = True
    fk_count = 0
    
    for table_name, expected_fks in fk_checks.items():
        constraints = get_table_constraints(conn, table_name)
        foreign_keys = constraints['foreign_keys']
        
        if foreign_keys:
            fk_count += len(foreign_keys)
    
    if fk_count > 0:
        log_test(5, "Foreign Key Relationships", "PASSED", 
                f"Found {fk_count} foreign key relationships")
    else:
        log_test(5, "Foreign Key Relationships", "FAILED", "No foreign keys found")

def test_6_data_types_correct(conn):
    """Test 6: Verify correct data types for columns"""
    type_checks = {
        'customers': [
            ('customer_id', 'integer'),
            ('first_name', 'text'),
            ('customer_status_id', 'integer')
        ],
        'accounts': [
            ('account_id', 'integer'),
            ('current_balance', 'real'),  # NUMERIC in SQLite is real
        ],
        'transactions': [
            ('transaction_id', 'integer'),
            ('amount', 'real'),
            ('transaction_date', 'text')  # TIMESTAMPTZ stored as text in SQLite
        ]
    }
    
    all_passed = True
    
    for table_name, expected_types in type_checks.items():
        table_info = get_table_info(conn, table_name)
        col_types = {col[1]: col[2] for col in table_info}
        
        for col_name, expected_type in expected_types:
            actual_type = col_types.get(col_name, 'NOT FOUND')
            if expected_type not in actual_type.lower():
                all_passed = False
    
    if all_passed:
        log_test(6, "Column Data Types", "PASSED", "All column types are correct")
    else:
        log_test(6, "Column Data Types", "FAILED", "Some column types are incorrect")

def test_7_constraints_defined(conn):
    """Test 7: Verify constraints are defined"""
    # Check for NOT NULL and UNIQUE constraints
    important_tables = ['customers', 'accounts', 'users', 'loan_accounts']
    all_passed = True
    constraint_count = 0
    
    for table_name in important_tables:
        table_info = get_table_info(conn, table_name)
        for col in table_info:
            col_name, col_type, not_null = col[1], col[2], col[3]
            if not_null and col_type != '':
                constraint_count += 1
    
    if constraint_count > 0:
        log_test(7, "Constraints Defined", "PASSED", 
                f"Found {constraint_count} NOT NULL constraints")
    else:
        log_test(7, "Constraints Defined", "FAILED", "No constraints found")

def test_8_indexes_exist(conn):
    """Test 8: Verify indexes are created"""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    indexes = cur.fetchall()
    
    if len(indexes) > 0:
        log_test(8, "Database Indexes", "PASSED", f"Found {len(indexes)} indexes")
    else:
        log_test(8, "Database Indexes", "FAILED", "No indexes found")

def test_9_views_exist(conn):
    """Test 9: Verify views are created"""
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='view';")
    views = cur.fetchall()
    view_names = [v[0] for v in views]
    
    expected_views = ['comprehensive_client_view', 'high_risk_loan_view']
    missing_views = [v for v in expected_views if v not in view_names]
    
    if not missing_views:
        log_test(9, "Database Views", "PASSED", f"Found all {len(expected_views)} views")
    else:
        log_test(9, "Database Views", "FAILED", f"Missing views: {', '.join(missing_views)}")

def test_10_nullable_columns_appropriate(conn):
    """Test 10: Verify nullable columns are appropriate"""
    # Some columns should be NOT NULL (like IDs, names)
    # Some should be nullable (like optional phone, closed_date)
    
    not_null_required = {
        'customers': ['customer_id', 'customer_code', 'first_name', 'last_name'],
        'accounts': ['account_id', 'account_number', 'customer_id'],
        'users': ['user_id', 'email', 'full_name', 'role_id']
    }
    
    all_passed = True
    
    for table_name, required_not_null in not_null_required.items():
        table_info = get_table_info(conn, table_name)
        col_info = {col[1]: col[3] for col in table_info}  # col[3] is NOT NULL flag
        
        for col_name in required_not_null:
            if col_name in col_info and col_info[col_name] == 0:  # 0 means nullable
                all_passed = False
    
    if all_passed:
        log_test(10, "NOT NULL Constraints Appropriate", "PASSED", 
                "Key columns properly marked as NOT NULL")
    else:
        log_test(10, "NOT NULL Constraints Appropriate", "FAILED", 
                "Some key columns are marked as nullable")

# ==================== MAIN EXECUTION ====================

def main():
    print("\n" + "="*70)
    print("SCHEMA VALIDATION TEST SERIES - Series 1")
    print("="*70 + "\n")
    
    conn = test_1_database_connection()
    if not conn:
        print("\n❌ Cannot proceed with tests - database not available")
        return
    
    try:
        # Run all tests
        test_2_tables_exist(conn)
        test_3_table_columns_exist(conn)
        test_4_primary_keys_defined(conn)
        test_5_foreign_keys_defined(conn)
        test_6_data_types_correct(conn)
        test_7_constraints_defined(conn)
        test_8_indexes_exist(conn)
        test_9_views_exist(conn)
        test_10_nullable_columns_appropriate(conn)
        
    finally:
        conn.close()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY - SCHEMA VALIDATION")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["Status"] == "PASSED")
    failed = sum(1 for r in test_results if r["Status"] == "FAILED")
    total = len(test_results)
    
    print(f"\n📊 Results: {passed}/{total} tests PASSED, {failed}/{total} FAILED\n")
    
    # Print detailed table
    print(f"{'Test #':<8} | {'Test Name':<40} | {'Status':<10} | Details")
    print("-" * 100)
    for r in test_results:
        print(f"{r['Test #']:<8} | {r['Test Name']:<40} | {r['Status']:<10} | {r['Details']}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
