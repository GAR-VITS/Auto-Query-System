"""
NexusDB Schema Catalog & Introspector
Extracts tables, columns, types, foreign keys, comments, and low-cardinality sample values.
Computes catalog hash for drift detection.
"""

import hashlib
import json
import sqlite3
from typing import Any
from pydantic import BaseModel, Field
from pathlib import Path

from app.config import get_settings
from app.db.session import is_postgres_available, get_db_connection

settings = get_settings()


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    is_primary_key: bool = False
    is_nullable: bool = True
    comment: str = ""
    sample_values: list[str] = Field(default_factory=list)


class ForeignKeyRelation(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    join_hint: str = ""


class TableMetadata(BaseModel):
    name: str
    schema_name: str = "bank"
    comment: str = ""
    columns: dict[str, ColumnMetadata] = Field(default_factory=dict)
    foreign_keys: list[ForeignKeyRelation] = Field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        return f"{self.schema_name}.{self.name}"

    def to_slice_text(self) -> str:
        col_lines = []
        for c in self.columns.values():
            pk = " [PK]" if c.is_primary_key else ""
            samples = f" (samples: {', '.join(c.sample_values)})" if c.sample_values else ""
            desc = f" - {c.comment}" if c.comment else ""
            col_lines.append(f"  - {c.name}: {c.data_type}{pk}{samples}{desc}")
        
        fk_lines = []
        for fk in self.foreign_keys:
            fk_lines.append(f"  - {fk.join_hint}")

        fk_sec = f"\nForeign Key Joins:\n" + "\n".join(fk_lines) if fk_lines else ""
        return (
            f"Table: {self.name} (Schema: {self.schema_name})\n"
            f"Description: {self.comment or self.name}\n"
            f"Columns:\n" + "\n".join(col_lines) +
            fk_sec
        )


class CatalogSnapshot(BaseModel):
    tables: dict[str, TableMetadata] = Field(default_factory=dict)
    foreign_keys: list[ForeignKeyRelation] = Field(default_factory=list)
    catalog_hash: str = ""

    def has_table(self, table_name: str) -> bool:
        clean = table_name.lower().replace("bank.", "").replace("app.", "").replace("audit.", "")
        return clean in self.tables or table_name.lower() in self.tables

    def has_column(self, table_name: str, column_name: str) -> bool:
        clean_tbl = table_name.lower().replace("bank.", "").replace("app.", "").replace("audit.", "")
        tbl = self.tables.get(clean_tbl) or self.tables.get(table_name.lower())
        if not tbl:
            return False
        return column_name.lower() in tbl.columns


# Core comments dictionary for 16 hand-designed banking tables
CORE_COMMENTS = {
    "branches": {
        "__table__": "Physical banking branch locations across Indian cities",
        "branch_id": "Unique identifier for the branch",
        "name": "Name of the branch office",
        "city": "City where the branch is located",
        "state": "State in India where branch operates",
        "ifsc_prefix": "IFSC routing code prefix for electronic transactions",
    },
    "employees": {
        "__table__": "Bank staff and branch officers",
        "employee_id": "Unique employee identifier",
        "branch_id": "Branch where the employee is posted",
        "name": "Full legal name of the employee",
        "designation": "Job title (e.g. Branch Officer, Loan Manager, Auditor)",
    },
    "customers": {
        "__table__": "Retail and corporate banking customers",
        "customer_id": "Primary customer identification number",
        "full_name": "Full registered customer name",
        "dob": "Customer date of birth",
        "city": "Customer residential or registered city",
        "branch_id": "Home branch of customer",
        "kyc_status": "Know-Your-Customer verification status (VERIFIED, PENDING, REJECTED)",
        "segment": "Customer segment classification (RETAIL, HNI, SME, CORPORATE)",
        "created_at": "Timestamp of customer onboarding",
    },
    "account_types": {
        "__table__": "Categories of deposit and transaction accounts",
        "type_id": "Unique identifier for account type",
        "name": "Name of account tier (SAVINGS, CURRENT, SALARY)",
        "min_balance": "Minimum required balance in INR to avoid maintenance penalties",
    },
    "accounts": {
        "__table__": "Deposit and checking accounts held by customers",
        "account_id": "Unique bank account number",
        "customer_id": "Foreign key to account owner customer",
        "type_id": "Type of account (SAVINGS, CURRENT, SALARY)",
        "branch_id": "Branch holding this account",
        "status": "Account state: ACTIVE, HOLD, FLAGGED, or CLOSED",
        "balance": "Current cleared balance in INR",
        "opened_at": "Account opening timestamp",
    },
    "merchants": {
        "__table__": "Commercial merchants receiving customer payments",
        "merchant_id": "Unique merchant identifier",
        "name": "Registered merchant brand name",
        "category": "Merchant sector (e.g. GROCERY, TRAVEL, DINING, HEALTHCARE)",
        "city": "Settlement city of merchant",
    },
    "transactions": {
        "__table__": "Monetary ledger transactions across all bank accounts",
        "txn_id": "Unique transaction sequence identifier",
        "account_id": "Account transacted",
        "txn_ts": "Timestamp transaction executed",
        "amount": "Amount in INR transacted",
        "direction": "Credit (CR) or Debit (DR) to account balance",
        "channel": "Channel used: UPI, NEFT, IMPS, RTGS, ATM, POS",
        "merchant_id": "Optional merchant identifier for POS/UPI merchant payments",
        "balance_after": "Account balance in INR immediately after transaction posted",
    },
    "cards": {
        "__table__": "Debit and credit payment cards linked to customer accounts",
        "card_id": "Unique identifier for the card",
        "account_id": "Primary account linked to card",
        "network": "Payment network: RUPAY, VISA, MASTERCARD",
        "status": "Card status: ACTIVE, BLOCKED, EXPIRED",
        "credit_limit": "Credit limit in INR for credit cards (0 for debit)",
    },
    "loan_products": {
        "__table__": "Catalog of lending products offered by bank",
        "product_id": "Unique loan product code",
        "name": "Product name (e.g. Home Loan, Personal Loan, Auto Loan, MSME Credit)",
        "base_rate": "Annual percentage benchmark interest rate",
        "max_tenor_months": "Maximum allowed repayment duration in months",
    },
    "loans": {
        "__table__": "Lending contracts issued to customers",
        "loan_id": "Unique loan contract number",
        "customer_id": "Borrower customer identifier",
        "product_id": "Loan product type",
        "principal": "Total principal loan amount disbursed in INR",
        "interest_rate": "Contracted annual interest rate",
        "tenor_months": "Repayment term length in months",
        "status": "Loan status: SANCTIONED, DISBURSED, ACTIVE, DELINQUENT, CLOSED",
        "disbursed_at": "Date loan funds were transferred to borrower",
    },
    "repayments": {
        "__table__": "Monthly loan installment schedules and payment tracking",
        "repayment_id": "Unique repayment schedule record ID",
        "loan_id": "Associated loan contract",
        "due_date": "Scheduled installment due date",
        "paid_date": "Actual date customer paid installment",
        "amount_due": "Installment due amount in INR",
        "amount_paid": "Actual amount in INR paid by borrower",
        "days_past_due": "Number of overdue days (>= 30 delinquent, >= 90 NPA)",
    },
    "credit_tiers": {
        "__table__": "Credit score rating bands from Tier A (Prime) to Tier E (Subprime)",
        "tier_id": "Tier code ID",
        "name": "Letter rating: A, B, C, D, E",
        "min_score": "Minimum credit score for tier",
        "max_score": "Maximum credit score for tier",
    },
    "credit_scores": {
        "__table__": "Historical and latest credit bureau risk ratings for customers",
        "score_id": "Unique scoring record",
        "customer_id": "Evaluated customer",
        "score": "Bureau credit score ranging 300 to 900",
        "tier_id": "Mapped risk tier band",
        "scored_at": "Timestamp of credit score calculation",
    },
    "risk_flags": {
        "__table__": "Operational risk, AML and compliance alert flags placed on accounts",
        "flag_id": "Unique risk flag ID",
        "account_id": "Account targeted by risk flag",
        "flag_type": "Category of flag: AML_SUSPICION, KYC_MISMATCH, OVERDRAFT_DEF, FRAUD_ALERT",
        "severity": "Alert severity: LOW, MEDIUM, HIGH, CRITICAL",
        "reason": "Compliance rationale provided for placing the flag",
        "set_by": "Username or role who authorized flag",
        "set_at": "Timestamp flag was logged",
    },
    "gl_accounts": {
        "__table__": "General ledger chart of accounts for financial reconciliation",
        "gl_id": "General ledger account ID",
        "code": "Standard GL accounting code",
        "name": "General ledger account name (e.g. Retail Deposits, Loan Assets)",
        "type": "Accounting category: ASSET, LIABILITY, REVENUE, EXPENSE, EQUITY",
    },
    "ledger_entries": {
        "__table__": "Double-entry general ledger journal postings for reconciliation",
        "entry_id": "Journal entry primary key",
        "gl_id": "Mapped general ledger account",
        "account_id": "Corresponding customer bank account",
        "entry_date": "Posting date",
        "debit": "Debit amount in INR",
        "credit": "Credit amount in INR",
    },
}


def introspect_catalog() -> CatalogSnapshot:
    """Introspects the active database to generate a comprehensive CatalogSnapshot."""
    tables: dict[str, TableMetadata] = {}
    foreign_keys: list[ForeignKeyRelation] = []

    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        # Fetch all user tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'bank.%' AND name NOT LIKE 'app.%' AND name NOT LIKE 'audit.%';")
        tbl_names = [row[0] for row in cur.fetchall()]

        for tbl_name in tbl_names:
            tbl_comment = CORE_COMMENTS.get(tbl_name, {}).get("__table__", f"Banking table {tbl_name}")
            tbl_meta = TableMetadata(name=tbl_name, schema_name="bank", comment=tbl_comment)

            # Introspect columns via PRAGMA table_info
            cur.execute(f"PRAGMA table_info({tbl_name});")
            for col in cur.fetchall():
                cid, name, col_type, notnull, dflt_value, pk = col
                col_comment = CORE_COMMENTS.get(tbl_name, {}).get(name, "")
                
                # Fetch up to 3 distinct sample values for low-cardinality columns
                sample_vals: list[str] = []
                if any(k in name.lower() for k in ("status", "type", "channel", "network", "segment", "severity", "direction")):
                    try:
                        cur.execute(f"SELECT DISTINCT {name} FROM {tbl_name} WHERE {name} IS NOT NULL LIMIT 3;")
                        sample_vals = [str(r[0]) for r in cur.fetchall()]
                    except Exception:
                        sample_vals = []

                tbl_meta.columns[name.lower()] = ColumnMetadata(
                    name=name,
                    data_type=col_type or "TEXT",
                    is_primary_key=bool(pk),
                    is_nullable=not bool(notnull),
                    comment=col_comment,
                    sample_values=sample_vals,
                )

            # Introspect foreign keys
            cur.execute(f"PRAGMA foreign_key_list({tbl_name});")
            for fk in cur.fetchall():
                # id, seq, table, from, to, on_update, on_delete, match
                _, _, to_tbl, from_col, to_col, _, _, _ = fk
                join_hint = f"Join {tbl_name} to {to_tbl}: {tbl_name}.{from_col} = {to_tbl}.{to_col}"
                fk_rel = ForeignKeyRelation(
                    from_table=tbl_name,
                    from_column=from_col,
                    to_table=to_tbl,
                    to_column=to_col,
                    join_hint=join_hint,
                )
                tbl_meta.foreign_keys.append(fk_rel)
                foreign_keys.append(fk_rel)

            tables[tbl_name.lower()] = tbl_meta

    # Compute deterministic catalog SHA-256 hash
    hasher = hashlib.sha256()
    for tbl in sorted(tables.keys()):
        hasher.update(tbl.encode("utf-8"))
        for col in sorted(tables[tbl].columns.keys()):
            hasher.update(col.encode("utf-8"))
            hasher.update(tables[tbl].columns[col].data_type.encode("utf-8"))
    catalog_hash = hasher.hexdigest()

    return CatalogSnapshot(tables=tables, foreign_keys=foreign_keys, catalog_hash=catalog_hash)


_cached_catalog: CatalogSnapshot | None = None


def get_catalog_snapshot() -> CatalogSnapshot:
    global _cached_catalog
    if _cached_catalog is None:
        _cached_catalog = introspect_catalog()
    return _cached_catalog
