"""
Unit Tests for SqlGuard (Section 16 Specification)
Tests 30+ cases covering multiple statements, DDL, DML, SELECT INTO, dangerous functions,
CTEs hiding DML, comment tricks, unknown tables/columns, and automatic LIMIT insertion.
"""

import pytest
from app.core.sql_guard import SqlGuard
from app.memory.catalog import get_catalog_snapshot

@pytest.fixture(scope="module")
def guard():
    return SqlGuard(default_limit=1000, max_limit=1000)

@pytest.fixture(scope="module")
def catalog():
    return get_catalog_snapshot()

# 1-5: Multiple statement rejection & comment tricks
def test_multiple_statements_semicolon(guard, catalog):
    verdict = guard.check("SELECT * FROM bank.customers; DROP TABLE bank.customers;", catalog)
    assert not verdict.ok
    assert verdict.error_code == "MULTIPLE_STATEMENTS"

def test_multiple_statements_newlines(guard, catalog):
    verdict = guard.check("SELECT 1 FROM bank.branches;\nSELECT 2 FROM bank.branches;", catalog)
    assert not verdict.ok
    assert verdict.error_code == "MULTIPLE_STATEMENTS"

def test_comment_trick_inline(guard, catalog):
    verdict = guard.check("SELECT * FROM bank.accounts --;\n; DROP TABLE bank.accounts;", catalog)
    assert not verdict.ok

def test_comment_trick_block(guard, catalog):
    verdict = guard.check("SELECT * FROM bank.accounts /* comment */; DELETE FROM bank.accounts;", catalog)
    assert not verdict.ok

def test_empty_query(guard, catalog):
    verdict = guard.check("", catalog)
    assert not verdict.ok

# 6-12: Prohibited DDL statements
def test_reject_drop_table(guard, catalog):
    verdict = guard.check("DROP TABLE bank.customers", catalog)
    assert not verdict.ok
    assert verdict.error_code in ("UNAUTHORIZED_COMMAND", "DDL_DML_PROHIBITED")

def test_reject_create_table(guard, catalog):
    verdict = guard.check("CREATE TABLE bank.hacked (id INT)", catalog)
    assert not verdict.ok

def test_reject_alter_table(guard, catalog):
    verdict = guard.check("ALTER TABLE bank.accounts ADD COLUMN evil TEXT", catalog)
    assert not verdict.ok

def test_reject_truncate_table(guard, catalog):
    verdict = guard.check("TRUNCATE TABLE bank.transactions", catalog)
    assert not verdict.ok

def test_reject_create_index(guard, catalog):
    verdict = guard.check("CREATE INDEX idx_test ON bank.customers(customer_id)", catalog)
    assert not verdict.ok

def test_reject_drop_database(guard, catalog):
    verdict = guard.check("DROP DATABASE nexus", catalog)
    assert not verdict.ok

def test_reject_drop_schema(guard, catalog):
    verdict = guard.check("DROP SCHEMA bank CASCADE", catalog)
    assert not verdict.ok

# 13-18: Prohibited DML statements
def test_reject_insert(guard, catalog):
    verdict = guard.check("INSERT INTO bank.customers (full_name) VALUES ('Hacker')", catalog)
    assert not verdict.ok

def test_reject_update(guard, catalog):
    verdict = guard.check("UPDATE bank.accounts SET balance = 9999999 WHERE account_id = 1", catalog)
    assert not verdict.ok

def test_reject_delete(guard, catalog):
    verdict = guard.check("DELETE FROM bank.loans WHERE loan_id = 1", catalog)
    assert not verdict.ok

def test_reject_select_into(guard, catalog):
    verdict = guard.check("SELECT * INTO bank.backup_customers FROM bank.customers", catalog)
    assert not verdict.ok
    assert verdict.error_code == "SELECT_INTO_PROHIBITED"

def test_reject_copy(guard, catalog):
    verdict = guard.check("COPY bank.customers TO '/tmp/dump.csv'", catalog)
    assert not verdict.ok

def test_reject_replace_into(guard, catalog):
    verdict = guard.check("REPLACE INTO bank.customers (customer_id) VALUES (1)", catalog)
    assert not verdict.ok

# 19-24: Dangerous functions and system catalog probes
def test_reject_pg_sleep(guard, catalog):
    verdict = guard.check("SELECT pg_sleep(10) FROM bank.customers", catalog)
    assert not verdict.ok
    assert verdict.error_code == "DANGEROUS_FUNCTION"

def test_reject_pg_read_file(guard, catalog):
    verdict = guard.check("SELECT pg_read_file('/etc/passwd') FROM bank.customers", catalog)
    assert not verdict.ok
    assert verdict.error_code == "DANGEROUS_FUNCTION"

def test_reject_dblink(guard, catalog):
    verdict = guard.check("SELECT * FROM dblink('host=evil.com', 'SELECT 1')", catalog)
    assert not verdict.ok

def test_reject_lo_import(guard, catalog):
    verdict = guard.check("SELECT lo_import('/etc/shadow') FROM bank.customers", catalog)
    assert not verdict.ok

def test_reject_information_schema(guard, catalog):
    verdict = guard.check("SELECT * FROM information_schema.tables", catalog)
    assert not verdict.ok
    assert verdict.error_code == "SYSTEM_CATALOG_ACCESS"

def test_reject_pg_catalog(guard, catalog):
    verdict = guard.check("SELECT * FROM pg_catalog.pg_user", catalog)
    assert not verdict.ok

# 25-27: CTEs hiding DML
def test_cte_hiding_insert(guard, catalog):
    verdict = guard.check("WITH evil AS (INSERT INTO bank.accounts (account_id) VALUES (999) RETURNING *) SELECT * FROM evil", catalog)
    assert not verdict.ok
    assert verdict.error_code == "DDL_DML_PROHIBITED"

def test_cte_hiding_delete(guard, catalog):
    verdict = guard.check("WITH evil AS (DELETE FROM bank.loans WHERE loan_id = 1 RETURNING *) SELECT * FROM evil", catalog)
    assert not verdict.ok

def test_cte_hiding_update(guard, catalog):
    verdict = guard.check("WITH evil AS (UPDATE bank.accounts SET balance = 0 RETURNING *) SELECT * FROM evil", catalog)
    assert not verdict.ok

# 28-31: Unknown tables and columns validation
def test_unknown_table(guard, catalog):
    verdict = guard.check("SELECT * FROM bank.imaginary_crypto_table", catalog)
    assert not verdict.ok
    assert verdict.error_code == "UNKNOWN_TABLE"

def test_unknown_column(guard, catalog):
    verdict = guard.check("SELECT c.imaginary_column FROM bank.customers c", catalog)
    assert not verdict.ok
    assert verdict.error_code == "UNKNOWN_COLUMN"

def test_valid_table_and_columns(guard, catalog):
    verdict = guard.check("SELECT c.customer_id, c.full_name FROM bank.customers c", catalog)
    assert verdict.ok
    assert "LIMIT 1000" in verdict.sql.upper()

def test_automatic_limit_injection_when_missing(guard, catalog):
    verdict = guard.check("SELECT b.branch_id, b.name FROM bank.branches b", catalog)
    assert verdict.ok
    assert "LIMIT 1000" in verdict.sql.upper()

def test_automatic_limit_capping_when_exceeding_max(guard, catalog):
    verdict = guard.check("SELECT b.branch_id, b.name FROM bank.branches b LIMIT 50000", catalog)
    assert verdict.ok
    assert "LIMIT 1000" in verdict.sql.upper()

def test_existing_lower_limit_preserved(guard, catalog):
    verdict = guard.check("SELECT b.branch_id, b.name FROM bank.branches b LIMIT 25", catalog)
    assert verdict.ok
    assert "LIMIT 25" in verdict.sql.upper()
