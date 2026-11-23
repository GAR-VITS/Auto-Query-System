"""
Synthetic Banking Data Generator for NexusDB
Deterministic generation of 16 core banking tables in Indian banking context (INR, IFSC, Indian cities).
Creates demo users, action catalog, credit tiers, loans, repayments, and audit genesis.
"""

import sys
import os
import random
import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import sqlite3
from passlib.hash import bcrypt

def get_db_connection(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

INDIAN_CITIES = [
    ("Mumbai", "Maharashtra", "NEXU0001"),
    ("Delhi", "Delhi", "NEXU0002"),
    ("Bengaluru", "Karnataka", "NEXU0003"),
    ("Hyderabad", "Telangana", "NEXU0004"),
    ("Chennai", "Tamil Nadu", "NEXU0005"),
    ("Kolkata", "West Bengal", "NEXU0006"),
    ("Pune", "Maharashtra", "NEXU0007"),
    ("Ahmedabad", "Gujarat", "NEXU0008"),
    ("Jaipur", "Rajasthan", "NEXU0009"),
    ("Chandigarh", "Punjab", "NEXU0010"),
    ("Lucknow", "Uttar Pradesh", "NEXU0011"),
    ("Kochi", "Kerala", "NEXU0012"),
    ("Indore", "Madhya Pradesh", "NEXU0013"),
    ("Bhopal", "Madhya Pradesh", "NEXU0014"),
    ("Patna", "Bihar", "NEXU0015"),
    ("Nagpur", "Maharashtra", "NEXU0016"),
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharv", "Ananya", "Diya", "Saanvi", "Aadhya", "Pari", "Anushka", "Navya", "Riya",
    "Pooja", "Rahul", "Rohan", "Sneha", "Vikram", "Neha", "Priya", "Amit", "Rajesh", "Suresh"
]

LAST_NAMES = [
    "Sharma", "Verma", "Mehta", "Patel", "Gupta", "Deshmukh", "Kulkarni", "Reddy", "Nair", "Iyer",
    "Mukherjee", "Chatterjee", "Banerjee", "Singh", "Yadav", "Chauhan", "Joshi", "Bhat", "Rao", "Pillai"
]

MERCHANTS = [
    ("Swiggy Foods", "DINING", "Bengaluru"),
    ("Zomato Online", "DINING", "Delhi"),
    ("Reliance Fresh", "GROCERY", "Mumbai"),
    ("DMart Supermart", "GROCERY", "Pune"),
    ("Apollo Pharmacy", "HEALTHCARE", "Hyderabad"),
    ("MakeMyTrip Travels", "TRAVEL", "Delhi"),
    ("Flipkart India", "RETAIL", "Bengaluru"),
    ("Amazon Pay India", "RETAIL", "Hyderabad"),
    ("Indian Oil Petrol", "FUEL", "Mumbai"),
    ("BookMyShow Entertainment", "ENTERTAINMENT", "Mumbai"),
]

def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))

def generate_database(db_path: Path, full_scale: bool = False):
    random.seed(42)
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    print(f"[*] Initializing schemas and tables in {db_path}...")

    # Drop existing tables cleanly
    tables_to_drop = [
        "ledger_entries", "gl_accounts", "risk_flags", "credit_scores", "credit_tiers",
        "repayments", "loans", "loan_products", "cards", "transactions", "merchants",
        "accounts", "account_types", "customers", "employees", "branches",
        "action_catalog", "users", "roles", "audit_log"
    ]
    for tbl in tables_to_drop:
        cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        cur.execute(f"DROP VIEW IF EXISTS \"bank.{tbl}\"")
        cur.execute(f"DROP VIEW IF EXISTS \"app.{tbl}\"")
        cur.execute(f"DROP VIEW IF EXISTS \"audit.{tbl}\"")

    # 1. branches
    cur.execute("""
    CREATE TABLE branches (
        branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        ifsc_prefix TEXT NOT NULL UNIQUE
    );
    """)

    # 2. employees
    cur.execute("""
    CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        name TEXT NOT NULL,
        designation TEXT NOT NULL
    );
    """)

    # 3. customers
    cur.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        dob DATE NOT NULL,
        city TEXT NOT NULL,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        kyc_status TEXT NOT NULL DEFAULT 'VERIFIED',
        segment TEXT NOT NULL DEFAULT 'RETAIL',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. account_types
    cur.execute("""
    CREATE TABLE account_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        min_balance REAL NOT NULL DEFAULT 0.0
    );
    """)

    # 5. accounts
    cur.execute("""
    CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        type_id INTEGER NOT NULL REFERENCES account_types(type_id),
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        balance REAL NOT NULL DEFAULT 0.0,
        opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. merchants
    cur.execute("""
    CREATE TABLE merchants (
        merchant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        city TEXT NOT NULL
    );
    """)

    # 7. transactions
    cur.execute("""
    CREATE TABLE transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        txn_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        amount REAL NOT NULL,
        direction TEXT NOT NULL CHECK (direction IN ('CR', 'DR')),
        channel TEXT NOT NULL,
        merchant_id INTEGER REFERENCES merchants(merchant_id),
        balance_after REAL NOT NULL
    );
    """)

    # 8. cards
    cur.execute("""
    CREATE TABLE cards (
        card_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        network TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        credit_limit REAL NOT NULL DEFAULT 0.0
    );
    """)

    # 9. loan_products
    cur.execute("""
    CREATE TABLE loan_products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        base_rate REAL NOT NULL,
        max_tenor_months INTEGER NOT NULL
    );
    """)

    # 10. loans
    cur.execute("""
    CREATE TABLE loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        product_id INTEGER NOT NULL REFERENCES loan_products(product_id),
        principal REAL NOT NULL,
        interest_rate REAL NOT NULL,
        tenor_months INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'DISBURSED',
        disbursed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 11. repayments
    cur.execute("""
    CREATE TABLE repayments (
        repayment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
        due_date DATE NOT NULL,
        paid_date DATE,
        amount_due REAL NOT NULL,
        amount_paid REAL NOT NULL DEFAULT 0.0,
        days_past_due INTEGER NOT NULL DEFAULT 0
    );
    """)

    # 12. credit_tiers
    cur.execute("""
    CREATE TABLE credit_tiers (
        tier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        min_score INTEGER NOT NULL,
        max_score INTEGER NOT NULL
    );
    """)

    # 13. credit_scores
    cur.execute("""
    CREATE TABLE credit_scores (
        score_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        score INTEGER NOT NULL,
        tier_id INTEGER NOT NULL REFERENCES credit_tiers(tier_id),
        scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 14. risk_flags
    cur.execute("""
    CREATE TABLE risk_flags (
        flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        flag_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        reason TEXT NOT NULL,
        set_by TEXT NOT NULL,
        set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 15. gl_accounts
    cur.execute("""
    CREATE TABLE gl_accounts (
        gl_id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        type TEXT NOT NULL
    );
    """)

    # 16. ledger_entries
    cur.execute("""
    CREATE TABLE ledger_entries (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        gl_id INTEGER NOT NULL REFERENCES gl_accounts(gl_id),
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        entry_date DATE NOT NULL,
        debit REAL NOT NULL DEFAULT 0.0,
        credit REAL NOT NULL DEFAULT 0.0
    );
    """)

    # App Schema Tables: roles, users, action_catalog
    cur.execute("""
    CREATE TABLE roles (
        role_name TEXT PRIMARY KEY,
        description TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL REFERENCES roles(role_name),
        branch_id INTEGER REFERENCES branches(branch_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE action_catalog (
        action_name TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        allowed_roles TEXT NOT NULL,
        target_table TEXT NOT NULL,
        allowed_columns TEXT NOT NULL
    );
    """)

    # Audit Schema: audit_log
    cur.execute("""
    CREATE TABLE audit_log (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        request_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        event_type TEXT NOT NULL,
        status TEXT NOT NULL,
        payload TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        row_hash TEXT NOT NULL
    );
    """)

    # Trigger to prevent updates or deletes on audit_log
    cur.execute("""
    CREATE TRIGGER trg_audit_no_update
    BEFORE UPDATE ON audit_log
    BEGIN
        SELECT RAISE(FAIL, 'audit.log is strictly append-only. UPDATE prohibited.');
    END;
    """)

    cur.execute("""
    CREATE TRIGGER trg_audit_no_delete
    BEFORE DELETE ON audit_log
    BEGIN
        SELECT RAISE(FAIL, 'audit.log is strictly append-only. DELETE prohibited.');
    END;
    """)

    # Create Views for Schema Compatibility (allowing bank.table, app.table, audit.log)
    for tbl in [
        "branches", "employees", "customers", "account_types", "accounts", "merchants",
        "transactions", "cards", "loan_products", "loans", "repayments", "credit_tiers",
        "credit_scores", "risk_flags", "gl_accounts", "ledger_entries"
    ]:
        cur.execute(f"CREATE VIEW IF NOT EXISTS \"bank.{tbl}\" AS SELECT * FROM {tbl};")

    for tbl in ["roles", "users", "action_catalog"]:
        cur.execute(f"CREATE VIEW IF NOT EXISTS \"app.{tbl}\" AS SELECT * FROM {tbl};")

    cur.execute("CREATE VIEW IF NOT EXISTS \"audit.log\" AS SELECT * FROM audit_log;")

    # =========================================================================
    # Insert Seed Data
    # =========================================================================
    print("[*] Populating Branches...")
    branch_rows = []
    for idx, (city, state, ifsc) in enumerate(INDIAN_CITIES, start=1):
        name = f"Nexus Bank {city} Branch"
        branch_rows.append((idx, name, city, state, ifsc))
    cur.executemany("INSERT INTO branches (branch_id, name, city, state, ifsc_prefix) VALUES (?, ?, ?, ?, ?)", branch_rows)

    print("[*] Populating Employees...")
    emp_rows = []
    designations = ["Branch Officer", "Senior Branch Officer", "Credit Manager", "Assistant Manager", "Cashier"]
    emp_id = 1
    for b_id in range(1, len(INDIAN_CITIES) + 1):
        for d in designations:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            emp_rows.append((emp_id, b_id, name, d))
            emp_id += 1
    cur.executemany("INSERT INTO employees (employee_id, branch_id, name, designation) VALUES (?, ?, ?, ?)", emp_rows)

    print("[*] Populating Account Types...")
    acc_types = [
        (1, "SAVINGS", 1000.0),
        (2, "CURRENT", 10000.0),
        (3, "SALARY", 0.0),
    ]
    cur.executemany("INSERT INTO account_types (type_id, name, min_balance) VALUES (?, ?, ?)", acc_types)

    print("[*] Populating Credit Tiers...")
    tiers = [
        (1, "A", 750, 900),
        (2, "B", 700, 749),
        (3, "C", 650, 699),
        (4, "D", 600, 649),
        (5, "E", 300, 599),
    ]
    cur.executemany("INSERT INTO credit_tiers (tier_id, name, min_score, max_score) VALUES (?, ?, ?, ?)", tiers)

    print("[*] Populating Loan Products...")
    products = [
        (1, "Home Loan", 8.40, 240),
        (2, "Personal Loan", 12.50, 60),
        (3, "Auto Loan", 9.20, 84),
        (4, "MSME Business Credit", 10.75, 120),
    ]
    cur.executemany("INSERT INTO loan_products (product_id, name, base_rate, max_tenor_months) VALUES (?, ?, ?, ?)", products)

    print("[*] Populating Merchants...")
    m_rows = []
    for idx, (mname, cat, mcity) in enumerate(MERCHANTS, start=1):
        m_rows.append((idx, mname, cat, mcity))
    cur.executemany("INSERT INTO merchants (merchant_id, name, category, city) VALUES (?, ?, ?, ?)", m_rows)

    print("[*] Populating GL Accounts...")
    gls = [
        (1, "1010", "Cash and Vault Reserves", "ASSET"),
        (2, "1020", "Retail Customer Deposits", "LIABILITY"),
        (3, "1030", "Term Loan Assets", "ASSET"),
        (4, "1040", "Interest Income on Loans", "REVENUE"),
        (5, "1050", "Processing Fee Income", "REVENUE"),
    ]
    cur.executemany("INSERT INTO gl_accounts (gl_id, code, name, type) VALUES (?, ?, ?, ?)", gls)

    # Customers & Credit Scores
    num_customers = 2000
    print(f"[*] Generating {num_customers} Customers & Credit Scores...")
    customer_rows = []
    score_rows = []
    segments = ["RETAIL", "HNI", "SME", "CORPORATE"]
    kyc_statuses = ["VERIFIED", "VERIFIED", "VERIFIED", "PENDING"]
    start_date = date(2020, 1, 1)

    for c_id in range(1, num_customers + 1):
        fname = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        birth_year = random.randint(1965, 2003)
        dob = f"{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        b_id = random.randint(1, len(INDIAN_CITIES))
        city = INDIAN_CITIES[b_id - 1][0]
        kyc = random.choice(kyc_statuses)
        segment = random.choices(segments, weights=[0.7, 0.15, 0.1, 0.05])[0]
        created = (start_date + timedelta(days=random.randint(0, 1500))).isoformat() + " 10:00:00"

        customer_rows.append((c_id, fname, dob, city, b_id, kyc, segment, created))

        # Credit score: 300 to 900
        score = random.randint(350, 880)
        tier_id = 1 if score >= 750 else (2 if score >= 700 else (3 if score >= 650 else (4 if score >= 600 else 5)))
        score_rows.append((c_id, c_id, score, tier_id, created))

    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", customer_rows)
    cur.executemany("INSERT INTO credit_scores VALUES (?, ?, ?, ?, ?)", score_rows)

    # Accounts
    num_accounts = 3000
    print(f"[*] Generating {num_accounts} Accounts...")
    account_rows = []
    statuses = ["ACTIVE", "HOLD", "FLAGGED", "CLOSED"]
    for a_id in range(1, num_accounts + 1):
        cust_id = random.randint(1, num_customers)
        t_id = random.choices([1, 2, 3], weights=[0.65, 0.2, 0.15])[0]
        # customer's branch
        b_id = customer_rows[cust_id - 1][4]
        status = random.choices(statuses, weights=[0.85, 0.05, 0.05, 0.05])[0]
        balance = round(random.uniform(2500.0, 750000.0), 2)
        opened = (start_date + timedelta(days=random.randint(0, 1500))).isoformat() + " 09:30:00"
        account_rows.append((a_id, cust_id, t_id, b_id, status, balance, opened))

    cur.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)", account_rows)

    # Cards
    print("[*] Generating Cards...")
    card_rows = []
    networks = ["RUPAY", "VISA", "MASTERCARD"]
    card_id = 1
    for a_id in range(1, num_accounts + 1):
        if random.random() < 0.7:  # 70% have cards
            net = random.choice(networks)
            limit = 0.0 if random.random() < 0.6 else round(random.choice([50000, 100000, 200000, 500000]), 2)
            card_rows.append((card_id, a_id, net, "ACTIVE", limit))
            card_id += 1
    cur.executemany("INSERT INTO cards VALUES (?, ?, ?, ?, ?)", card_rows)

    # Loans (1500 loans)
    num_loans = 1500
    print(f"[*] Generating {num_loans} Loans & Repayments...")
    loan_rows = []
    repayment_rows = []
    rep_id = 1
    loan_statuses = ["ACTIVE", "ACTIVE", "DELINQUENT", "CLOSED"]

    for l_id in range(1, num_loans + 1):
        cust_id = random.randint(1, num_customers)
        prod_id = random.randint(1, 4)
        base_rate = products[prod_id - 1][2]
        principal = round(random.choice([100000, 250000, 500000, 1500000, 5000000]), 2)
        tenor = products[prod_id - 1][3]
        rate = round(base_rate + random.uniform(-0.5, 1.5), 2)
        disbursed = (start_date + timedelta(days=random.randint(100, 1200)))
        
        # Determine delinquency: ~8% delinquent (days_past_due >= 30)
        is_delinquent = (random.random() < 0.08)
        l_status = "DELINQUENT" if is_delinquent else random.choices(loan_statuses, weights=[0.8, 0.05, 0.05, 0.1])[0]

        loan_rows.append((l_id, cust_id, prod_id, principal, rate, tenor, l_status, disbursed.isoformat() + " 11:00:00"))

        # Repayments (6 installments per loan)
        emi = round((principal * (rate / 100 / 12) * (1 + rate / 100 / 12)**tenor) / ((1 + rate / 100 / 12)**tenor - 1), 2)
        for month in range(1, 7):
            due_dt = disbursed + timedelta(days=30 * month)
            if is_delinquent and month >= 4:
                dpd = random.randint(31, 120)
                amount_paid = 0.0
                paid_dt = None
            else:
                dpd = 0
                amount_paid = emi
                paid_dt = due_dt.isoformat()
            
            repayment_rows.append((rep_id, l_id, due_dt.isoformat(), paid_dt, emi, amount_paid, dpd))
            rep_id += 1

    cur.executemany("INSERT INTO loans VALUES (?, ?, ?, ?, ?, ?, ?, ?)", loan_rows)
    cur.executemany("INSERT INTO repayments VALUES (?, ?, ?, ?, ?, ?, ?)", repayment_rows)

    # Risk flags (seeded on flagged accounts)
    print("[*] Generating Risk Flags...")
    flag_rows = []
    flag_id = 1
    flag_types = ["AML_SUSPICION", "KYC_MISMATCH", "OVERDRAFT_DEF", "FRAUD_ALERT"]
    severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for acc in account_rows:
        if acc[4] in ("HOLD", "FLAGGED"):
            ft = random.choice(flag_types)
            sev = random.choice(severities)
            reason = f"Automated risk system trigger: {ft.lower()} flagged for compliance review."
            flag_rows.append((flag_id, acc[0], ft, sev, reason, "system_risk_engine", acc[6]))
            flag_id += 1
    cur.executemany("INSERT INTO risk_flags VALUES (?, ?, ?, ?, ?, ?, ?)", flag_rows)

    # Transactions & Ledger Entries
    # To keep seed fast for dev while supporting 150k for full
    tx_count = 150000 if full_scale else 15000
    print(f"[*] Generating {tx_count} Transactions & Ledger Entries...")
    txn_rows = []
    ledger_rows = []
    channels = ["UPI", "NEFT", "IMPS", "RTGS", "ATM", "POS"]
    cur_date = datetime(2026, 11, 20)

    for t_id in range(1, tx_count + 1):
        acc_id = random.randint(1, num_accounts)
        direction = random.choice(["CR", "DR"])
        amount = round(random.uniform(50.0, 45000.0), 2)
        channel = random.choice(channels)
        m_id = random.randint(1, len(MERCHANTS)) if channel in ("POS", "UPI") else None
        ts = (cur_date - timedelta(minutes=random.randint(1, 100000))).isoformat()
        balance_after = round(random.uniform(1000.0, 500000.0), 2)
        txn_rows.append((t_id, acc_id, ts, amount, direction, channel, m_id, balance_after))

    cur.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", txn_rows)

    # Ledger entries with deliberate reconciliation mismatches
    print("[*] Generating Ledger Entries with Deliberate Mismatches...")
    entry_id = 1
    for acc_id in range(1, min(1000, num_accounts) + 1):
        # Normal matching entry
        bal = account_rows[acc_id - 1][5]
        # Introduce deliberate mismatch on account 10482 or every 50th account
        if acc_id % 50 == 0:
            bal_ledger = bal + 15000.0  # Intentional discrepancy for reconciliation query!
        else:
            bal_ledger = bal
        
        ledger_rows.append((entry_id, 2, acc_id, "2026-11-20", 0.0, bal_ledger))
        entry_id += 1
    cur.executemany("INSERT INTO ledger_entries VALUES (?, ?, ?, ?, ?, ?)", ledger_rows)

    # App: Roles
    print("[*] Populating App Roles & Demo Users...")
    roles_data = [
        ("viewer", "Read-only access to ask questions, view charts and summaries"),
        ("branch_officer", "Can ask questions and update account status for accounts in their branch"),
        ("credit_manager", "Can ask questions, update account status, and manage risk flags"),
        ("admin", "Auditor and Administrator: manages users, views full audit trail and verifies cryptographic hash chain"),
    ]
    cur.executemany("INSERT INTO roles (role_name, description) VALUES (?, ?)", roles_data)

    # 4 Demo Users (passwords hashed with bcrypt)
    demo_users = [
        (1, "viewer", "viewer@nexusdb.local", bcrypt.hash("viewer123"), "viewer", None),
        (2, "officer", "officer@nexusdb.local", bcrypt.hash("officer123"), "branch_officer", 1),
        (3, "manager", "manager@nexusdb.local", bcrypt.hash("manager123"), "credit_manager", None),
        (4, "admin", "admin@nexusdb.local", bcrypt.hash("admin123"), "admin", None),
    ]
    cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", demo_users)

    # App: Action Catalog
    action_catalog_data = [
        ("SET_ACCOUNT_STATUS", "Updates account status to ACTIVE, HOLD, or FLAGGED", "branch_officer,credit_manager", "accounts", "status"),
        ("SET_RISK_FLAG", "Appends a new compliance or AML risk flag to an account", "credit_manager", "risk_flags", "account_id,flag_type,severity,reason,set_by"),
        ("CLEAR_RISK_FLAG", "Deactivates or clears an existing risk flag", "credit_manager", "risk_flags", "flag_id"),
    ]
    cur.executemany("INSERT INTO action_catalog VALUES (?, ?, ?, ?, ?)", action_catalog_data)

    # Audit: Genesis Entry
    print("[*] Creating Audit Trail Genesis Row...")
    genesis_prev_hash = "0" * 64
    genesis_payload = canonical_json({"system": "NexusDB", "event": "GENESIS_INITIALIZED"})
    hasher = hashlib.sha256()
    hasher.update((genesis_prev_hash + genesis_payload).encode("utf-8"))
    genesis_row_hash = hasher.hexdigest()

    cur.execute("""
    INSERT INTO audit_log (seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash)
    VALUES (1, CURRENT_TIMESTAMP, 'genesis-req-0000', 'system', 'system', 'LOGIN', 'SUCCESS', ?, ?, ?)
    """, (genesis_payload, genesis_prev_hash, genesis_row_hash))

    conn.commit()
    conn.close()
    print(f"[+] Successfully seeded NexusDB database at {db_path}!")

if __name__ == "__main__":
    is_full = "--full" in sys.argv
    db_file = backend_dir / "db" / "nexus_local.db"
    generate_database(db_file, full_scale=is_full)
