"""
SQLite initialization script for local database fallback.
Creates all schema tables, views, lookup values, and realistic synthetic financial data.
"""
from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "enterprise_finance.db"

random.seed(42)

FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rahul", "Pooja",
    "Deepak", "Neha", "Sanjay", "Kavita", "Rohan", "Meera", "Arjun", "Sunita",
    "Kiran", "Divya", "Manoj", "Shweta", "Suresh", "Ritu", "Alok", "Aarti",
    "Gaurav", "Nisha", "Manish", "Tanvi", "Vikas", "Preeti", "Sachin", "Jyoti"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Patel", "Reddy", "Singh", "Gupta", "Verma", "Joshi",
    "Mehta", "Nair", "Iyer", "Rao", "Chopra", "Bose", "Das", "Deshmukh",
    "Malhotra", "Kapoor", "Saxena", "Bhatia", "Chatterjee", "Mishra", "Pandey", "Chauhan"
]

LANGUAGES = ["English", "Hindi", "Bengali", "Tamil", "Marathi", "Telugu", "Kannada"]


def random_date(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, max(days, 1)))


def init_sqlite_database(db_path: Path = DB_PATH, count_customers: int = 150) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Drop existing tables and views
    cur.executescript("""
        DROP VIEW IF EXISTS comprehensive_client_view;
        DROP VIEW IF EXISTS high_risk_loan_view;
        DROP TABLE IF EXISTS query_history;
        DROP TABLE IF EXISTS audit_logs;
        DROP TABLE IF EXISTS credit_reports;
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS loan_payment_schedule;
        DROP TABLE IF EXISTS loan_accounts;
        DROP TABLE IF EXISTS accounts;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS spider_queries;
        DROP TABLE IF EXISTS spider_columns;
        DROP TABLE IF EXISTS spider_tables;
        DROP TABLE IF EXISTS spider_databases;
        DROP TABLE IF EXISTS audit_statuses;
        DROP TABLE IF EXISTS audit_action_types;
        DROP TABLE IF EXISTS agents;
        DROP TABLE IF EXISTS roles;
        DROP TABLE IF EXISTS risk_tiers;
        DROP TABLE IF EXISTS transaction_types;
        DROP TABLE IF EXISTS payment_statuses;
        DROP TABLE IF EXISTS loan_statuses;
        DROP TABLE IF EXISTS loan_types;
        DROP TABLE IF EXISTS account_statuses;
        DROP TABLE IF EXISTS account_types;
        DROP TABLE IF EXISTS customer_status;
    """)

    # Schema creation
    cur.executescript("""
        CREATE TABLE customer_status (
            status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE account_types (
            account_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE account_statuses (
            account_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE loan_types (
            loan_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_type_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE loan_statuses (
            loan_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE payment_statuses (
            payment_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE transaction_types (
            transaction_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE risk_tiers (
            risk_tier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier_name TEXT NOT NULL UNIQUE,
            min_score INT NOT NULL,
            max_score INT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE,
            permissions TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE agents (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            current_status TEXT NOT NULL,
            last_run_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            role_id INT NOT NULL REFERENCES roles(role_id),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login_at TEXT
        );

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_code TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            date_of_birth TEXT,
            customer_since TEXT NOT NULL,
            customer_status_id INT NOT NULL REFERENCES customer_status(status_id),
            preferred_language TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT NOT NULL UNIQUE,
            customer_id INT NOT NULL REFERENCES customers(customer_id),
            account_type_id INT NOT NULL REFERENCES account_types(account_type_id),
            account_status_id INT NOT NULL REFERENCES account_statuses(account_status_id),
            currency TEXT NOT NULL DEFAULT 'INR',
            opened_date TEXT NOT NULL,
            closed_date TEXT,
            current_balance REAL NOT NULL DEFAULT 0,
            available_balance REAL NOT NULL DEFAULT 0,
            overdraft_limit REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE loan_accounts (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_number TEXT NOT NULL UNIQUE,
            customer_id INT NOT NULL REFERENCES customers(customer_id),
            account_id INT REFERENCES accounts(account_id),
            loan_type_id INT NOT NULL REFERENCES loan_types(loan_type_id),
            loan_status_id INT NOT NULL REFERENCES loan_statuses(loan_status_id),
            principal_amount REAL NOT NULL,
            outstanding_amount REAL NOT NULL,
            interest_rate REAL NOT NULL,
            term_months INT NOT NULL,
            payment_frequency TEXT NOT NULL,
            origination_date TEXT NOT NULL,
            next_payment_date TEXT,
            maturity_date TEXT NOT NULL,
            default_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE loan_payment_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INT NOT NULL REFERENCES loan_accounts(loan_id),
            payment_number INT NOT NULL,
            due_date TEXT NOT NULL,
            amount_due REAL NOT NULL,
            principal_due REAL NOT NULL,
            interest_due REAL NOT NULL,
            balance_remaining REAL NOT NULL,
            payment_status_id INT NOT NULL REFERENCES payment_statuses(payment_status_id),
            paid_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_code TEXT NOT NULL UNIQUE,
            account_id INT NOT NULL REFERENCES accounts(account_id),
            loan_id INT REFERENCES loan_accounts(loan_id),
            transaction_type_id INT NOT NULL REFERENCES transaction_types(transaction_type_id),
            transaction_date TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'INR',
            balance_after REAL,
            reference TEXT,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE credit_reports (
            credit_report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INT NOT NULL REFERENCES customers(customer_id),
            bureau_name TEXT NOT NULL,
            credit_score INT NOT NULL,
            risk_tier_id INT NOT NULL REFERENCES risk_tiers(risk_tier_id),
            report_date TEXT NOT NULL,
            report_summary TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE audit_action_types (
            action_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE audit_statuses (
            audit_status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        );

        CREATE TABLE audit_logs (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            action_type_id INT NOT NULL REFERENCES audit_action_types(action_type_id),
            audit_status_id INT NOT NULL REFERENCES audit_statuses(audit_status_id),
            agent_id INT REFERENCES agents(agent_id),
            user_id INT REFERENCES users(user_id),
            description TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            affected_record_count INT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE query_history (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INT REFERENCES users(user_id),
            question TEXT NOT NULL,
            sql_text TEXT NOT NULL,
            row_count INT,
            execution_time_ms REAL,
            corrections INT DEFAULT 0,
            analysis TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Lookup Inserts
        INSERT INTO customer_status (status_id, status_name, description) VALUES
            (1, 'Active', 'Customer has an active relationship.'),
            (2, 'Inactive', 'Customer record is not active.'),
            (3, 'Closed', 'Customer relationship is closed.');

        INSERT INTO account_types (account_type_id, type_name, description) VALUES
            (1, 'Savings', 'Interest-bearing savings account.'),
            (2, 'Current', 'Non-interest-bearing current account.'),
            (3, 'Loan', 'Loan settlement account.');

        INSERT INTO account_statuses (account_status_id, status_name, description) VALUES
            (1, 'Active', 'Account is open.'),
            (2, 'Frozen', 'Account is restricted.'),
            (3, 'Closed', 'Account is closed.');

        INSERT INTO loan_types (loan_type_id, loan_type_name, description) VALUES
            (1, 'Personal', 'Unsecured personal loan.'),
            (2, 'Mortgage', 'Secured loan backed by real estate.'),
            (3, 'Business', 'Business working capital loan.');

        INSERT INTO loan_statuses (loan_status_id, status_name, description) VALUES
            (1, 'Active', 'Loan is current and being serviced.'),
            (2, 'Paid Off', 'Loan has been fully repaid.'),
            (3, 'Defaulted', 'Loan is in default status.'),
            (4, 'Review', 'Loan requires manual review.'),
            (5, 'Closed', 'Loan account has been closed.');

        INSERT INTO payment_statuses (payment_status_id, status_name, description) VALUES
            (1, 'Due', 'Payment is scheduled but not yet paid.'),
            (2, 'Paid', 'Payment has been received.'),
            (3, 'Late', 'Payment is overdue.'),
            (4, 'Missed', 'Payment was missed.');

        INSERT INTO transaction_types (transaction_type_id, type_name, description) VALUES
            (1, 'Payment', 'Customer payment against loan or account.'),
            (2, 'Disbursement', 'Loan funds released.'),
            (3, 'Fee', 'Service fee or penalty.'),
            (4, 'Adjustment', 'Balance adjustment.');

        INSERT INTO risk_tiers (risk_tier_id, tier_name, min_score, max_score, description) VALUES
            (1, 'Low Risk', 720, 850, 'Strong credit profile with low default probability.'),
            (2, 'Medium Risk', 650, 719, 'Moderate credit profile with some risk.'),
            (3, 'High Risk', 600, 649, 'Weak credit profile with elevated risk.'),
            (4, 'Critical', 300, 599, 'Very low credit score and high default risk.');

        INSERT INTO roles (role_id, role_name, permissions, description) VALUES
            (1, 'admin', 'read,write,approve,audit', 'Full system administrator role.'),
            (2, 'analyst', 'read,write', 'Data analyst role.'),
            (3, 'manager', 'read,approve', 'Manager role with approval authority.'),
            (4, 'viewer', 'read', 'Read-only role.');

        INSERT INTO agents (agent_id, agent_code, name, description, current_status, last_run_at) VALUES
            (1, 'query', 'Query Agent', 'Translates natural language to SQL & self-corrects syntax errors', 'idle', datetime('now', '-2 minutes')),
            (2, 'analysis', 'Analysis Agent', 'Evaluates results with Pandas & plain-English summaries', 'idle', datetime('now', '-5 minutes')),
            (3, 'visualization', 'Visualization Agent', 'Builds interactive charts from query output', 'idle', datetime('now', '-12 minutes'));

        INSERT INTO audit_action_types (action_type_id, action_name, description) VALUES
            (1, 'query_executed', 'Natural language SQL query execution logged.'),
            (2, 'credit_evaluation', 'Automated credit evaluation event.'),
            (3, 'defaulter_flagged', 'Customer flagged as high-risk or defaulter.'),
            (4, 'loan_approved', 'Loan approval event recorded.'),
            (5, 'status_updated', 'Status change or workflow transition logged.');

        INSERT INTO audit_statuses (audit_status_id, status_name, description) VALUES
            (1, 'approved', 'Action was approved.'),
            (2, 'pending', 'Action is pending review.'),
            (3, 'rejected', 'Action was rejected.'),
            (4, 'auto_executed', 'Action was executed automatically.');

        -- Standard Users
        INSERT INTO users (user_id, email, full_name, role_id, is_active) VALUES
            (1, 'analyst@enterprise.com', 'Enterprise Analyst', 2, 1),
            (2, 'manager@enterprise.com', 'Risk Manager', 3, 1),
            (3, 'admin@enterprise.com', 'System Admin', 1, 1),
            (4, 'viewer@enterprise.com', 'Auditor Viewer', 4, 1);

        -- Views
        CREATE VIEW comprehensive_client_view AS
        SELECT
            c.customer_id,
            c.customer_code,
            c.first_name,
            c.last_name,
            (c.first_name || ' ' || c.last_name) AS full_name,
            c.email,
            c.phone,
            c.customer_status_id,
            cs.status_name AS customer_status,
            la.loan_id,
            la.loan_number,
            la.loan_status_id,
            ls.status_name AS loan_status,
            la.principal_amount,
            la.outstanding_amount,
            la.interest_rate,
            la.term_months,
            la.origination_date,
            la.maturity_date,
            cr.credit_score,
            rt.tier_name AS credit_risk_tier,
            cr.report_date
        FROM customers c
        LEFT JOIN customer_status cs ON c.customer_status_id = cs.status_id
        LEFT JOIN loan_accounts la ON la.customer_id = c.customer_id
        LEFT JOIN loan_statuses ls ON la.loan_status_id = ls.loan_status_id
        LEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id
        LEFT JOIN risk_tiers rt ON cr.risk_tier_id = rt.risk_tier_id;

        CREATE VIEW high_risk_loan_view AS
        SELECT
            la.loan_id,
            la.loan_number,
            c.customer_id,
            c.customer_code,
            c.first_name,
            c.last_name,
            (c.first_name || ' ' || c.last_name) AS full_name,
            la.outstanding_amount,
            la.default_date,
            cr.credit_score,
            rt.tier_name AS credit_risk_tier
        FROM loan_accounts la
        JOIN customers c ON la.customer_id = c.customer_id
        LEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id
        LEFT JOIN risk_tiers rt ON cr.risk_tier_id = rt.risk_tier_id
        WHERE la.loan_status_id = 3;
    """)

    # Seed Customers
    today = date.today()
    customers_data = []
    for i in range(1, count_customers + 1):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        code = f"C-{1000 + i:04d}"
        email = f"{fn.lower()}.{ln.lower()}{i}@enterprise.com"
        phone = f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
        dob = random_date(date(today.year - 65, 1, 1), date(today.year - 22, 1, 1)).isoformat()
        since = random_date(date(today.year - 10, 1, 1), today - timedelta(days=30)).isoformat()
        status_id = 1 if random.random() < 0.85 else (2 if random.random() < 0.8 else 3)
        lang = random.choice(LANGUAGES)
        customers_data.append((code, fn, ln, email, phone, dob, since, status_id, lang))

    cur.executemany("""
        INSERT INTO customers (customer_code, first_name, last_name, email, phone, date_of_birth, customer_since, customer_status_id, preferred_language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers_data)

    # Seed Accounts
    accounts_data = []
    for cust_id in range(1, count_customers + 1):
        acc_num = f"A-{1000 + cust_id:04d}-01"
        opened = random_date(date(today.year - 8, 1, 1), today - timedelta(days=60)).isoformat()
        balance = round(random.uniform(15000, 350000), 2)
        avail = round(balance * random.uniform(0.85, 1.0), 2)
        accounts_data.append((acc_num, cust_id, 1, 1, 'INR', opened, balance, avail, 5000.0))

        if random.random() < 0.4:
            acc_num2 = f"A-{1000 + cust_id:04d}-02"
            balance2 = round(random.uniform(5000, 120000), 2)
            accounts_data.append((acc_num2, cust_id, 2, 1, 'INR', opened, balance2, balance2, 0.0))

    cur.executemany("""
        INSERT INTO accounts (account_number, customer_id, account_type_id, account_status_id, currency, opened_date, current_balance, available_balance, overdraft_limit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, accounts_data)

    # Seed Loans for ~45% of customers
    loans_data = []
    schedules_data = []
    loan_idx = 1
    for cust_id in range(1, count_customers + 1):
        if random.random() < 0.45 or cust_id in [1, 2, 3, 4, 5, 8, 12, 15, 20]:
            loan_num = f"LA-{8000 + loan_idx:04d}"
            loan_type_id = random.choice([1, 2, 3])
            # statuses: 1: Active, 2: Paid Off, 3: Defaulted, 4: Review
            if cust_id in [2, 8, 15]:
                loan_status_id = 3  # Defaulted
            elif cust_id in [4, 12]:
                loan_status_id = 4  # Review
            else:
                loan_status_id = random.choices([1, 2, 3, 4], weights=[0.6, 0.2, 0.1, 0.1])[0]

            principal = round(random.uniform(100000, 1500000), 2)
            interest = round(random.uniform(8.5, 15.5), 2)
            term = random.choice([24, 36, 48, 60])
            orig_date = random_date(date(today.year - 3, 1, 1), today - timedelta(days=90))
            mat_date = orig_date + timedelta(days=30 * term)

            if loan_status_id == 2:
                outstanding = 0.0
                next_pay = None
                def_date = None
            elif loan_status_id == 3:
                outstanding = round(principal * random.uniform(0.6, 0.95), 2)
                next_pay = (today - timedelta(days=30)).isoformat()
                def_date = (today - timedelta(days=random.randint(45, 180))).isoformat()
            else:
                outstanding = round(principal * random.uniform(0.2, 0.85), 2)
                next_pay = (today + timedelta(days=random.randint(5, 28))).isoformat()
                def_date = None

            loans_data.append((
                loan_num, cust_id, cust_id, loan_type_id, loan_status_id,
                principal, outstanding, interest, term, "Monthly",
                orig_date.isoformat(), next_pay, mat_date.isoformat(), def_date
            ))

            # Payment schedules
            due = orig_date + timedelta(days=30)
            for p_num in range(1, min(term, 12) + 1):
                p_status = 2 if loan_status_id in [1, 2] else (4 if loan_status_id == 3 else 3)
                p_amt = round(principal / term + principal * 0.005, 2)
                paid = due.isoformat() if p_status == 2 else None
                schedules_data.append((loan_idx, p_num, due.isoformat(), p_amt, round(p_amt * 0.8, 2), round(p_amt * 0.2, 2), outstanding, p_status, paid))
                due += timedelta(days=30)

            loan_idx += 1

    cur.executemany("""
        INSERT INTO loan_accounts (loan_number, customer_id, account_id, loan_type_id, loan_status_id, principal_amount, outstanding_amount, interest_rate, term_months, payment_frequency, origination_date, next_payment_date, maturity_date, default_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, loans_data)

    cur.executemany("""
        INSERT INTO loan_payment_schedule (loan_id, payment_number, due_date, amount_due, principal_due, interest_due, balance_remaining, payment_status_id, paid_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, schedules_data)

    # Seed Credit Reports
    credit_data = []
    for cust_id in range(1, count_customers + 1):
        if cust_id in [1, 2, 3, 4, 5]:
            score = [542, 558, 571, 589, 595][cust_id - 1]
        elif cust_id in [8, 12, 15]:
            score = random.randint(520, 590)
        else:
            score = random.randint(610, 840)

        if score >= 720:
            tier_id = 1
        elif score >= 650:
            tier_id = 2
        elif score >= 600:
            tier_id = 3
        else:
            tier_id = 4

        bureau = random.choice(["CIBIL", "Experian", "Equifax", "TransUnion"])
        rep_date = random_date(date(today.year - 1, 1, 1), today).isoformat()
        summary = f"Bureau {bureau} credit score {score} rated as Tier {tier_id}."
        credit_data.append((cust_id, bureau, score, tier_id, rep_date, summary))

    cur.executemany("""
        INSERT INTO credit_reports (customer_id, bureau_name, credit_score, risk_tier_id, report_date, report_summary)
        VALUES (?, ?, ?, ?, ?, ?)
    """, credit_data)

    # Seed Transactions
    tx_data = []
    tx_id = 1
    for cust_id in range(1, min(count_customers + 1, 80)):
        for _ in range(random.randint(4, 10)):
            tx_code = f"TX-{10000 + tx_id}"
            tx_type = random.choice([1, 2, 3, 4])
            tx_amt = round(random.uniform(500, 75000), 2)
            tx_date = random_date(today - timedelta(days=180), today).isoformat()
            ref = f"REF-{random.randint(100000, 999999)}"
            desc = f"Transaction for customer #{cust_id}"
            tx_data.append((tx_code, cust_id, None, tx_type, tx_date, tx_amt, 'INR', 50000.0, ref, desc))
            tx_id += 1

    cur.executemany("""
        INSERT INTO transactions (transaction_code, account_id, loan_id, transaction_type_id, transaction_date, amount, currency, balance_after, reference, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tx_data)

    # Seed Audit Logs
    audit_data = [
        (1, 4, 1, 1, "NL query: customers with credit score below 600", "Read-only SELECT query passed RBAC validation. No write operations detected.", 5, '{"agent": "query"}'),
        (3, 1, 2, 2, "Flagged C-0891 as high-risk defaulter", "Credit score 558, 127 days overdue, outstanding ₹8.45L. Rule R-042 triggered automatic flag.", 1, '{"agent": "analysis"}'),
        (2, 2, 2, 3, "Automated credit evaluation for loan application LA-9921", "Applicant score 612, debt-to-income 0.38. Awaiting manager approval per policy POL-018.", None, '{"agent": "analysis"}'),
        (4, 1, None, 3, "Approved loan LA-9918 for ₹3.2L", "All validation rules passed: score 720, income verified, collateral attached.", 1, '{"agent": "system"}'),
        (1, 4, 1, 1, "Self-corrected SQL after syntax error (attempt 2)", "Initial query failed on JOIN clause. Agent loop rewrote query using schema context.", 3, '{"agent": "query", "corrections": 1}'),
    ]
    cur.executemany("""
        INSERT INTO audit_logs (action_type_id, audit_status_id, agent_id, user_id, description, reasoning, affected_record_count, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, audit_data)

    # Seed Query History
    sample_queries = [
        (1, "Show customers with credit score below 600", "SELECT c.customer_id, (c.first_name || ' ' || c.last_name) AS full_name, cr.credit_score, ls.status_name AS loan_status FROM customers c LEFT JOIN loan_accounts la ON la.customer_id = c.customer_id LEFT JOIN loan_statuses ls ON la.loan_status_id = ls.loan_status_id LEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id WHERE cr.credit_score < 600 ORDER BY cr.credit_score ASC LIMIT 50;", 5, 142.0, 0, "Found 5 customers below the 600 credit threshold. 1 account is in default status and 1 is under review."),
        (1, "Top defaulters by outstanding amount", "SELECT c.customer_code, (c.first_name || ' ' || c.last_name) AS full_name, la.loan_number, la.outstanding_amount FROM loan_accounts la JOIN customers c ON la.customer_id = c.customer_id WHERE la.loan_status_id = 3 ORDER BY la.outstanding_amount DESC LIMIT 10;", 3, 98.0, 1, "Top defaulted loan accounts ranked by outstanding balances."),
    ]
    cur.executemany("""
        INSERT INTO query_history (user_id, question, sql_text, row_count, execution_time_ms, corrections, analysis)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_queries)

    conn.commit()
    conn.close()
    print(f"SQLite database initialized successfully at {db_path}")


if __name__ == "__main__":
    init_sqlite_database()
