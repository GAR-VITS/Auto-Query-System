from __future__ import annotations

import os
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from dotenv import load_dotenv
from faker import Faker
from psycopg import connect

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_finance",
)

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)


def get_lookup_map(conn, table: str, key_field: str, id_field: str) -> Dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT {id_field}, {key_field} FROM {table}")
        return {row[1]: row[0] for row in cur.fetchall()}


def truncate_data(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "TRUNCATE TABLE query_history, audit_logs, credit_reports, loan_payment_schedule, transactions, loan_accounts, accounts, customers, users RESTART IDENTITY CASCADE"
        )
        conn.commit()


def insert_users(conn: connect, role_map: Dict[str, int]) -> Dict[str, int]:
    users = [
        ("admin@enterprise.com", "Admin User", role_map["admin"], True),
        ("analyst@enterprise.com", "Analyst User", role_map["analyst"], True),
        ("manager@enterprise.com", "Manager User", role_map["manager"], True),
        ("viewer@enterprise.com", "Viewer User", role_map["viewer"], True),
    ]
    user_ids: Dict[str, int] = {}
    with conn.cursor() as cur:
        for email, full_name, role_id, is_active in users:
            cur.execute(
                "INSERT INTO users (email, full_name, role_id, is_active, created_at) VALUES (%s, %s, %s, %s, NOW()) RETURNING user_id",
                (email, full_name, role_id, is_active),
            )
            user_ids[email] = cur.fetchone()[0]
        for i in range(8):
            role_name = random.choice(["analyst", "manager", "viewer"])
            email = f"user{i + 1}@enterprise.com"
            full_name = fake.name()
            role_id = role_map[role_name]
            cur.execute(
                "INSERT INTO users (email, full_name, role_id, is_active, created_at) VALUES (%s, %s, %s, TRUE, NOW()) RETURNING user_id",
                (email, full_name, role_id),
            )
            user_ids[email] = cur.fetchone()[0]
    conn.commit()
    return user_ids


def choose_risk_tier(score: int, tier_map: Dict[str, int]) -> int:
    if score >= 720:
        return tier_map["Low Risk"]
    if score >= 650:
        return tier_map["Medium Risk"]
    if score >= 600:
        return tier_map["High Risk"]
    return tier_map["Critical"]


def random_date(start: date, end: date) -> date:
    days = (end - start).days
    return start + timedelta(days=random.randint(0, max(days, 0)))


def generate_customers(conn, status_map: Dict[str, int], count: int = 1000) -> List[Dict]:
    customers = []
    with conn.cursor() as cur:
        for index in range(1, count + 1):
            first_name = fake.first_name()
            last_name = fake.last_name()
            age = int(np.clip(np.random.normal(42, 12), 21, 75))
            birth_year = date.today().year - age
            date_of_birth = fake.date_of_birth(minimum_age=21, maximum_age=75)
            customer_since = random_date(
                date(date.today().year - min(age - 18, 15), 1, 1),
                date.today() - timedelta(days=30),
            )
            code = f"C-{1000 + index:04d}"
            email = f"{first_name}.{last_name}{index}@enterprise.com".lower()
            language = random.choice(["English", "Hindi", "Bengali", "Tamil", "Marathi", "Telugu", "Kannada"])
            status_name = random.choices(["Active", "Inactive", "Closed"], weights=[0.82, 0.12, 0.06])[0]
            customer = (
                code,
                first_name,
                last_name,
                email,
                fake.phone_number(),
                date_of_birth,
                customer_since,
                status_map[status_name],
                language,
                datetime.combine(customer_since, datetime.min.time()) + timedelta(hours=random.randint(8, 16)),
                datetime.now(),
            )
            cur.execute(
                "INSERT INTO customers (customer_code, first_name, last_name, email, phone, date_of_birth, customer_since, customer_status_id, preferred_language, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING customer_id",
                customer,
            )
            customer_id = cur.fetchone()[0]
            customers.append({
                "customer_id": customer_id,
                "customer_code": code,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "date_of_birth": date_of_birth,
                "customer_since": customer_since,
                "status": status_name,
            })
    conn.commit()
    return customers


def insert_accounts(conn, customers: List[Dict], account_type_map: Dict[str, int], account_status_map: Dict[str, int]) -> Dict[int, List[int]]:
    customer_accounts: Dict[int, List[int]] = {}
    with conn.cursor() as cur:
        for customer in customers:
            account_count = random.choices([1, 2, 3], weights=[0.64, 0.28, 0.08])[0]
            if customer["customer_code"].endswith("0"):
                account_count = max(account_count, 2)
            account_ids = []
            for account_index in range(account_count):
                account_type = random.choices(["Savings", "Current"], weights=[0.65, 0.35])[0]
                opening_date = random_date(customer["customer_since"], date.today() - timedelta(days=30))
                balance = float(np.clip(np.random.normal(50000, 70000), 1000, 250000))
                available_balance = balance - float(np.clip(np.random.normal(0, 2500), -500, 500))
                account = (
                    f"A-{customer['customer_code'][-4:]}-{account_index + 1:02d}",
                    customer["customer_id"],
                    account_type_map[account_type],
                    account_status_map["Active"],
                    "INR",
                    opening_date,
                    None,
                    round(balance, 2),
                    round(max(available_balance, 0), 2),
                    datetime.combine(opening_date, datetime.min.time()),
                    datetime.now(),
                )
                cur.execute(
                    "INSERT INTO accounts (account_number, customer_id, account_type_id, account_status_id, currency, opened_date, closed_date, current_balance, available_balance, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING account_id",
                    account,
                )
                account_ids.append(cur.fetchone()[0])
            customer_accounts[customer["customer_id"]] = account_ids
    conn.commit()
    return customer_accounts


def generate_loan_accounts(
    conn,
    customers: List[Dict],
    customer_accounts: Dict[int, List[int]],
    loan_type_map: Dict[str, int],
    loan_status_map: Dict[str, int],
    payment_status_map: Dict[str, int],
    account_type_map: Dict[str, int],
) -> List[Dict]:
    loan_customers = random.sample(customers, int(len(customers) * 0.42))
    loan_accounts = []
    with conn.cursor() as cur:
        for customer in loan_customers:
            base_date = random_date(customer["customer_since"], date.today() - timedelta(days=180))
            loan_type = random.choices(["Personal", "Mortgage", "Business"], weights=[0.45, 0.30, 0.25])[0]
            status = random.choices(
                ["Active", "Paid Off", "Defaulted", "Review"], weights=[0.56, 0.18, 0.12, 0.14]
            )[0]
            principal = float(np.clip(np.random.normal(550000, 320000), 50000, 2800000))
            interest_rate = float(np.clip(np.random.normal(11.5, 2.5), 6.5, 18.0))
            term_months = int(random.choice([24, 36, 48, 60]))
            origination_date = base_date
            maturity_date = origination_date + timedelta(days=30 * term_months)
            outstanding = principal * float(np.clip(np.random.uniform(0.05, 0.96), 0.05, 0.96))
            if status == "Paid Off":
                outstanding = 0.0
            if status == "Defaulted":
                outstanding = float(np.clip(np.random.normal(principal * 0.78, 40000), principal * 0.55, principal * 0.95))
            due_date = origination_date + timedelta(days=30)
            account_num = f"A-{customer['customer_code'][-4:]}-LN"
            cur.execute(
                "INSERT INTO accounts (account_number, customer_id, account_type_id, account_status_id, currency, opened_date, current_balance, available_balance, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING account_id",
                (
                    account_num,
                    customer["customer_id"],
                    account_type_map["Loan"],
                    account_status_map["Active"],
                    "INR",
                    origination_date,
                    round(outstanding, 2),
                    round(max(outstanding * 0.9, 0.0), 2),
                    datetime.combine(origination_date, datetime.min.time()),
                    datetime.now(),
                ),
            )
            loan_account_id = cur.fetchone()[0]
            loan_number = f"LA-{customer['customer_code'][-4:]}-{random.randint(100,999)}"
            payment_frequency = "Monthly"
            next_payment_date = due_date if status != "Paid Off" else None
            default_date = None
            if status == "Defaulted":
                default_date = date.today() - timedelta(days=random.randint(45, 180))
                next_payment_date = date.today() - timedelta(days=15)
            cur.execute(
                "INSERT INTO loan_accounts (loan_number, customer_id, account_id, loan_type_id, loan_status_id, principal_amount, outstanding_amount, interest_rate, term_months, payment_frequency, origination_date, next_payment_date, maturity_date, default_date, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING loan_id",
                (
                    loan_number,
                    customer["customer_id"],
                    loan_account_id,
                    loan_type_map[loan_type],
                    loan_status_map[status],
                    round(principal, 2),
                    round(outstanding, 2),
                    round(interest_rate, 2),
                    term_months,
                    payment_frequency,
                    origination_date,
                    next_payment_date,
                    maturity_date,
                    default_date,
                    datetime.combine(origination_date, datetime.min.time()),
                    datetime.now(),
                ),
            )
            loan_id = cur.fetchone()[0]
            loan_accounts.append(
                {
                    "loan_id": loan_id,
                    "loan_number": loan_number,
                    "customer_id": customer["customer_id"],
                    "account_id": loan_account_id,
                    "status": status,
                    "principal": principal,
                    "outstanding": outstanding,
                    "origination_date": origination_date,
                    "maturity_date": maturity_date,
                    "due_date": due_date,
                    "term_months": term_months,
                    "payment_status_id": payment_status_map["Paid" if status in ["Active", "Paid Off"] else "Missed"],
                    "loan_status_name": status,
                }
            )
    conn.commit()
    return loan_accounts


def insert_payment_schedule(conn, loan_accounts: List[Dict], payment_status_map: Dict[str, int]) -> None:
    with conn.cursor() as cur:
        for loan in loan_accounts:
            balance_remaining = loan["principal"]
            payment_count = max(12, min(loan["term_months"], 60)) if loan.get("term_months") else 36
            due_date = loan["origination_date"] + timedelta(days=30)
            monthly_amount = round(loan["principal"] / payment_count + loan["principal"] * 0.002, 2)
            for payment_number in range(1, payment_count + 1):
                if loan["principal"] > 0:
                    interest_due = round(balance_remaining * (loan["outstanding"] / loan["principal"]) * 0.005, 2)
                else:
                    interest_due = 0.0
                principal_due = round(max(monthly_amount - interest_due, 0.0), 2)
                amount_due = round(principal_due + interest_due, 2)
                balance_remaining = max(round(balance_remaining - principal_due, 2), 0.0)
                status = "Paid"
                paid_date = due_date + timedelta(days=random.randint(0, 5))
                if loan["loan_status_name"] == "Defaulted" and due_date > date.today() - timedelta(days=90):
                    status = "Missed"
                    paid_date = None
                elif loan["loan_status_name"] == "Review" and random.random() < 0.3:
                    status = "Late"
                    paid_date = due_date + timedelta(days=random.randint(5, 25))
                cur.execute(
                    "INSERT INTO loan_payment_schedule (loan_id, payment_number, due_date, amount_due, principal_due, interest_due, balance_remaining, payment_status_id, paid_date, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                    (
                        loan["loan_id"],
                        payment_number,
                        due_date,
                        amount_due,
                        principal_due,
                        interest_due,
                        balance_remaining,
                        payment_status_map[status],
                        paid_date,
                    ),
                )
                due_date += timedelta(days=30)
    conn.commit()


def insert_transactions(
    conn,
    customers: List[Dict],
    customer_accounts: Dict[int, List[int]],
    loan_accounts: List[Dict],
    transaction_type_map: Dict[str, int],
) -> None:
    loan_by_account = {loan["account_id"]: loan for loan in loan_accounts}
    anomalous_accounts = set(random.sample([customer["customer_id"] for customer in customers], k=15))
    with conn.cursor() as cur:
        for customer in customers:
            for account_id in customer_accounts[customer["customer_id"]]:
                cur.execute("SELECT opened_date, current_balance FROM accounts WHERE account_id = %s", (account_id,))
                account_row = cur.fetchone()
                if not account_row:
                    continue
                opened_date, current_balance = account_row
                transaction_date = opened_date + timedelta(days=7)
                for _ in range(random.randint(6, 18)):
                    amount = round(abs(random.gauss(18000, 13000)), 2)
                    txn_type = random.choices(["Payment", "Disbursement", "Fee", "Adjustment"], [0.45, 0.15, 0.25, 0.15])[0]
                    if account_id in loan_by_account:
                        if txn_type == "Disbursement":
                            transaction_type_id = transaction_type_map["Disbursement"]
                        else:
                            transaction_type_id = transaction_type_map["Payment"]
                            if loan_by_account[account_id]["loan_status_name"] == "Defaulted" and transaction_date > date.today() - timedelta(days=90):
                                txn_type = "Fee"
                                transaction_type_id = transaction_type_map["Fee"]
                    else:
                        transaction_type_id = transaction_type_map[txn_type]
                    if customer["customer_id"] in anomalous_accounts and random.random() < 0.06:
                        amount *= random.choice([10, 12, 15])
                    balance_after = max(current_balance + amount * (1 if txn_type != "Payment" else -1), -5000.0)
                    description = "Large branch transfer" if amount > 200000 else fake.sentence(nb_words=5)
                    cur.execute(
                        "INSERT INTO transactions (transaction_code, account_id, loan_id, transaction_type_id, transaction_date, amount, currency, balance_after, reference, description, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                        (
                            f"T-{account_id}-{int(transaction_date.strftime('%Y%m%d'))}-{random.randint(1000,9999)}",
                            account_id,
                            loan_by_account.get(account_id, {}).get("loan_id"),
                            transaction_type_id,
                            transaction_date,
                            round(amount, 2),
                            "INR",
                            round(balance_after, 2),
                            fake.bothify(text="REF-####"),
                            description,
                        ),
                    )
                    current_balance = balance_after
                    transaction_date += timedelta(days=random.randint(4, 24))
        # create some high-value anomaly transactions across random accounts
        account_ids = [acc_id for ids in customer_accounts.values() for acc_id in ids]
        for _ in range(12):
            account_id = random.choice(account_ids)
            cur.execute("SELECT opened_date, current_balance FROM accounts WHERE account_id = %s", (account_id,))
            opened_date, current_balance = cur.fetchone()
            transaction_date = random_date(opened_date + timedelta(days=30), date.today() - timedelta(days=1))
            amount = round(random.uniform(650000, 1800000), 2)
            balance_after = current_balance + amount if random.random() < 0.5 else current_balance - amount
            cur.execute(
                "INSERT INTO transactions (transaction_code, account_id, loan_id, transaction_type_id, transaction_date, amount, currency, balance_after, reference, description, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                (
                    f"T-ANOM-{account_id}-{random.randint(100000,999999)}",
                    account_id,
                    None,
                    transaction_type_map["Adjustment"],
                    transaction_date,
                    amount,
                    "INR",
                    round(balance_after, 2),
                    "ANOM-REF",
                    "Unusually large transaction for anomaly detection.",
                ),
            )
    conn.commit()


def insert_credit_reports(conn, customers: List[Dict], risk_tier_map: Dict[str, int]) -> None:
    with conn.cursor() as cur:
        for customer in customers:
            age = (date.today() - customer["date_of_birth"]).days // 365
            if customer["customer_code"].endswith("0"):
                score = int(np.clip(np.random.normal(800, 25), 760, 850))
            else:
                score = int(np.clip(np.random.normal(680 + (age - 40) * 0.8, 70), 300, 850))
            tier_id = choose_risk_tier(score, risk_tier_map)
            cur.execute(
                "INSERT INTO credit_reports (customer_id, bureau_name, credit_score, risk_tier_id, report_date, report_summary, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                (
                    customer["customer_id"],
                    random.choice(["TransUnion", "Equifax", "CIBIL", "Experian"]),
                    score,
                    tier_id,
                    random_date(date.today() - timedelta(days=180), date.today()),
                    f"Credit report with score {score} and tier {tier_id}.",
                ),
            )
            if random.random() < 0.35:
                score2 = int(np.clip(score + random.randint(-12, 12), 300, 850))
                tier_id2 = choose_risk_tier(score2, risk_tier_map)
                cur.execute(
                    "INSERT INTO credit_reports (customer_id, bureau_name, credit_score, risk_tier_id, report_date, report_summary, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                    (
                        customer["customer_id"],
                        random.choice(["TransUnion", "Equifax", "CIBIL", "Experian"]),
                        score2,
                        tier_id2,
                        random_date(date.today() - timedelta(days=360), date.today() - timedelta(days=30)),
                        f"Historical credit snapshot with score {score2}.",
                    ),
                )
    conn.commit()


def create_spider_sample(conn: connect) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO spider_databases (database_name, domain, description) VALUES (%s, %s, %s) RETURNING spider_db_id",
            ("banking_spider", "finance", "Synthetic Spider benchmark database for financial NL2SQL evaluation."),
        )
        spider_db_id = cur.fetchone()[0]
        tables = [
            ("customers", "Customer demographics and account metadata."),
            ("loan_accounts", "Loan ledger with borrower, status, and balance details."),
            ("transactions", "Financial transaction history for accounts."),
        ]
        table_ids = {}
        for table_name, table_description in tables:
            cur.execute(
                "INSERT INTO spider_tables (spider_db_id, table_name, description) VALUES (%s, %s, %s) RETURNING spider_table_id",
                (spider_db_id, table_name, table_description),
            )
            table_ids[table_name] = cur.fetchone()[0]
        columns = [
            ("customers", "customer_id", "INTEGER", True, False, "Customer primary key."),
            ("customers", "full_name", "TEXT", False, False, "Customer name."),
            ("customers", "credit_score", "INTEGER", False, False, "Latest credit score."),
            ("loan_accounts", "loan_id", "INTEGER", True, False, "Loan primary key."),
            ("loan_accounts", "customer_id", "INTEGER", False, True, "FK to customers.") ,
            ("loan_accounts", "outstanding_amount", "NUMERIC", False, False, "Current loan balance."),
            ("transactions", "transaction_id", "INTEGER", True, False, "Transaction primary key."),
            ("transactions", "account_id", "INTEGER", False, False, "Account reference."),
            ("transactions", "amount", "NUMERIC", False, False, "Transaction amount."),
        ]
        for table_name, column_name, data_type, is_primary, is_foreign, description in columns:
            cur.execute(
                "INSERT INTO spider_columns (spider_table_id, column_name, data_type, is_primary, is_foreign, description) VALUES (%s, %s, %s, %s, %s, %s)",
                (table_ids[table_name], column_name, data_type, is_primary, is_foreign, description),
            )
        spider_queries = [
            (
                "List all customers with credit score below 600 and active loans.",
                "SELECT c.customer_id, c.full_name, c.credit_score, l.loan_status_id FROM customers c JOIN loan_accounts l ON c.customer_id = l.customer_id WHERE c.credit_score < 600 AND l.loan_status_id = 1;",
                "medium",
            ),
            (
                "Find transactions with amount greater than 500000 in the last year.",
                "SELECT transaction_id, account_id, amount, transaction_date FROM transactions WHERE amount > 500000 AND transaction_date >= CURRENT_DATE - INTERVAL '1 year';",
                "easy",
            ),
        ]
        for nl, sql_text, difficulty in spider_queries:
            cur.execute(
                "INSERT INTO spider_queries (spider_db_id, natural_language, sql_query, difficulty) VALUES (%s, %s, %s, %s)",
                (spider_db_id, nl, sql_text, difficulty),
            )
    conn.commit()


def insert_audit_and_query_history(conn: connect, user_map: Dict[str, int], agents: List[int]) -> None:
    audit_actions = [
        ("query_executed", "auto_executed", "query", "analyst@enterprise.com", "Read-only SELECT query passed RBAC validation.", "No write operations detected.", None),
        ("defaulter_flagged", "approved", "analysis", "manager@enterprise.com", "Flagged customer for high-risk defaulter status.", "Credit score below threshold and delinquent payments.", 1),
        ("loan_approved", "approved", "system", "admin@enterprise.com", "Loan application approved.", "All validation rules passed.", None),
    ]
    with conn.cursor() as cur:
        for action, status, agent_code, user_email, description, reasoning, affected_records in audit_actions:
            agent_id = random.choice(agents) if agent_code != "system" else None
            cur.execute(
                "SELECT audit_action_id FROM audit_action_types WHERE action_name = %s",
                (action,),
            )
            action_id = cur.fetchone()[0]
            cur.execute(
                "SELECT audit_status_id FROM audit_statuses WHERE status_name = %s",
                (status,),
            )
            status_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO audit_logs (event_timestamp, action_type_id, audit_status_id, agent_id, user_id, description, reasoning, affected_record_count, metadata, created_at) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, NOW())",
                (
                    action_id,
                    status_id,
                    agent_id,
                    user_map.get(user_email),
                    description,
                    reasoning,
                    affected_records,
                    {"source": "synthetic_seed"},
                ),
            )
        sample_queries = [
            ("Show customers with credit score below 600", "SELECT customer_id, full_name, credit_score, loan_status_id FROM customers WHERE credit_score < 600 ORDER BY credit_score ASC LIMIT 50;", 5, 142, "Found customers below threshold."),
            ("Top defaulters by outstanding amount", "SELECT customer_id, outstanding_amount FROM loan_accounts WHERE loan_status_id = 3 ORDER BY outstanding_amount DESC LIMIT 10;", 3, 98, "Top defaulted loans by balance."),
        ]
        for question, sql_text, row_count, exec_ms, analysis in sample_queries:
            cur.execute(
                "INSERT INTO query_history (user_id, question, sql_text, row_count, execution_time_ms, corrections, analysis, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                (
                    user_map["analyst@enterprise.com"],
                    question,
                    sql_text,
                    row_count,
                    exec_ms,
                    random.randint(0, 1),
                    analysis,
                ),
            )
    conn.commit()


def run_sanity_checks(conn: connect) -> None:
    checks = [
        (
            "Negative account balances",
            "SELECT COUNT(*) FROM accounts WHERE current_balance < 0 AND account_type_id != (SELECT account_type_id FROM account_types WHERE type_name = 'Loan')",
        ),
        (
            "Transactions before account opening",
            "SELECT COUNT(*) FROM transactions t JOIN accounts a ON t.account_id = a.account_id WHERE t.transaction_date < a.opened_date",
        ),
        (
            "Loan payments before origination",
            "SELECT COUNT(*) FROM loan_payment_schedule lps JOIN loan_accounts la ON lps.loan_id = la.loan_id WHERE lps.due_date < la.origination_date",
        ),
        (
            "Credit score outside risk tier",
            "SELECT COUNT(*) FROM credit_reports cr JOIN risk_tiers rt ON cr.risk_tier_id = rt.risk_tier_id WHERE cr.credit_score < rt.min_score OR cr.credit_score > rt.max_score",
        ),
        (
            "Defaulted loans with recent payments",
            "SELECT COUNT(DISTINCT la.loan_id) FROM loan_accounts la JOIN loan_payment_schedule lps ON la.loan_id = lps.loan_id WHERE la.loan_status_id = (SELECT loan_status_id FROM loan_statuses WHERE status_name = 'Defaulted') AND lps.paid_date > CURRENT_DATE - INTERVAL '90 days'",
        ),
    ]
    print("Running sanity checks:")
    with conn.cursor() as cur:
        for label, query in checks:
            cur.execute(query)
            count = cur.fetchone()[0]
            print(f"- {label}: {count}")


def main() -> None:
    print("Connecting to database:", DATABASE_URL)
    with connect(DATABASE_URL) as conn:
        role_map = get_lookup_map(conn, "roles", "role_name", "role_id")
        status_map = get_lookup_map(conn, "customer_status", "status_name", "status_id")
        account_type_map = get_lookup_map(conn, "account_types", "type_name", "account_type_id")
        account_status_map = get_lookup_map(conn, "account_statuses", "status_name", "account_status_id")
        loan_type_map = get_lookup_map(conn, "loan_types", "loan_type_name", "loan_type_id")
        loan_status_map = get_lookup_map(conn, "loan_statuses", "status_name", "status_id")
        payment_status_map = get_lookup_map(conn, "payment_statuses", "status_name", "payment_status_id")
        transaction_type_map = get_lookup_map(conn, "transaction_types", "type_name", "transaction_type_id")
        risk_tier_map = get_lookup_map(conn, "risk_tiers", "tier_name", "risk_tier_id")

        truncate_data(conn)
        user_map = insert_users(conn, role_map)
        customers = generate_customers(conn, status_map, count=1000)
        customer_accounts = insert_accounts(conn, customers, account_type_map, account_status_map)
        loan_accounts = generate_loan_accounts(
            conn, customers, customer_accounts, loan_type_map, loan_status_map, payment_status_map, account_type_map
        )
        insert_payment_schedule(conn, loan_accounts, payment_status_map)
        insert_transactions(conn, customers, customer_accounts, loan_accounts, transaction_type_map)
        insert_credit_reports(conn, customers, risk_tier_map)
        create_spider_sample(conn)
        insert_audit_and_query_history(conn, user_map, [1, 2, 3])
        run_sanity_checks(conn)

    print("Synthetic data generation complete.")


if __name__ == "__main__":
    main()
