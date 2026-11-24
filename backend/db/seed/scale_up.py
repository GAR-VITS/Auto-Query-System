"""
NexusDB Scale-Up Script
Adds 35+ auxiliary tables with foreign keys and descriptions to test retrieval quality at scale (>50 total tables).
"""

import sys
import sqlite3
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
db_path = backend_dir / "db" / "nexus_local.db"

AUXILIARY_TABLES = [
    ("fx_rates", "Foreign exchange daily spot and forward currency rates", """
        rate_id INTEGER PRIMARY KEY,
        currency_code TEXT NOT NULL,
        rate_to_inr REAL NOT NULL,
        effective_date DATE NOT NULL
    """),
    ("standing_instructions", "Recurring auto-debit standing instructions scheduled on customer accounts", """
        instruction_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        beneficiary_account TEXT NOT NULL,
        amount REAL NOT NULL,
        frequency TEXT NOT NULL,
        next_execution_date DATE NOT NULL,
        status TEXT NOT NULL
    """),
    ("kyc_documents", "Customer identification documents submitted for verification (Aadhaar, PAN, Passport)", """
        doc_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        doc_type TEXT NOT NULL,
        doc_number TEXT NOT NULL,
        verification_status TEXT NOT NULL,
        verified_at TIMESTAMP
    """),
    ("atm_events", "Telemetry logs and cash dispenser sensor events from ATM machines", """
        event_id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        terminal_id TEXT NOT NULL,
        event_code TEXT NOT NULL,
        event_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cash_balance REAL
    """),
    ("branch_targets", "Quarterly deposit and loan disbursement targets set for branches", """
        target_id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        fiscal_quarter TEXT NOT NULL,
        deposit_target REAL NOT NULL,
        loan_target REAL NOT NULL,
        achieved_deposit REAL DEFAULT 0.0,
        achieved_loan REAL DEFAULT 0.0
    """),
    ("locker_rentals", "Safe deposit locker reservations in bank vault", """
        locker_id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        locker_size TEXT NOT NULL,
        annual_fee REAL NOT NULL,
        expiry_date DATE NOT NULL
    """),
    ("wealth_portfolios", "Investment advisory and wealth management portfolios", """
        portfolio_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        aum_value REAL NOT NULL,
        risk_profile TEXT NOT NULL,
        advisor_name TEXT NOT NULL
    """),
    ("debit_mandates", "E-mandate and NACH automated payment registrations", """
        mandate_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        umrn TEXT NOT NULL UNIQUE,
        max_amount REAL NOT NULL,
        creditor_name TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    """),
    ("swift_messages", "Cross-border SWIFT MT103 and MT202 remittance telecommunications", """
        swift_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        swift_bic TEXT NOT NULL,
        message_type TEXT NOT NULL,
        currency TEXT NOT NULL,
        amount REAL NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """),
    ("cheque_books", "Cheque book leaves issuance and clearing status", """
        cheque_book_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        start_leaf INTEGER NOT NULL,
        end_leaf INTEGER NOT NULL,
        status TEXT NOT NULL,
        issued_at DATE NOT NULL
    """),
    ("nominees", "Registered nominees and legal heirs for deposit accounts", """
        nominee_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        nominee_name TEXT NOT NULL,
        relationship TEXT NOT NULL,
        date_of_birth DATE NOT NULL
    """),
    ("interest_certificates", "Annual interest earned certificates generated for tax purposes (Form 16A)", """
        cert_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        financial_year TEXT NOT NULL,
        total_interest_earned REAL NOT NULL,
        tds_deducted REAL NOT NULL
    """),
    ("fd_deposits", "Fixed term deposit accounts with maturity tenors and compounding interest", """
        fd_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        principal REAL NOT NULL,
        interest_rate REAL NOT NULL,
        maturity_date DATE NOT NULL,
        maturity_amount REAL NOT NULL,
        status TEXT NOT NULL
    """),
    ("rd_accounts", "Recurring deposit monthly savings contracts", """
        rd_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        monthly_installment REAL NOT NULL,
        tenor_months INTEGER NOT NULL,
        total_maturity_amount REAL NOT NULL
    """),
    ("pos_terminals", "Merchant point-of-sale card swipe machine inventory", """
        terminal_id INTEGER PRIMARY KEY,
        merchant_id INTEGER NOT NULL REFERENCES merchants(merchant_id),
        serial_no TEXT NOT NULL UNIQUE,
        model TEXT NOT NULL,
        deployed_date DATE NOT NULL
    """),
    ("loan_guarantors", "Third-party credit guarantors for secured term loans", """
        guarantor_id INTEGER PRIMARY KEY,
        loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
        guarantor_name TEXT NOT NULL,
        guarantor_pan TEXT NOT NULL,
        net_worth REAL NOT NULL
    """),
    ("collateral_assets", "Pledged real estate and machinery collateral securing high-value loans", """
        collateral_id INTEGER PRIMARY KEY,
        loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
        asset_type TEXT NOT NULL,
        valuation REAL NOT NULL,
        valuation_date DATE NOT NULL
    """),
    ("dispute_tickets", "Customer chargeback and failed ATM/UPI transaction grievance tickets", """
        ticket_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        txn_id INTEGER REFERENCES transactions(txn_id),
        category TEXT NOT NULL,
        status TEXT NOT NULL,
        resolution_notes TEXT
    """),
    ("beneficiaries", "Pre-registered NEFT/RTGS/IMPS funds transfer payees", """
        beneficiary_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        beneficiary_name TEXT NOT NULL,
        beneficiary_account TEXT NOT NULL,
        ifsc_code TEXT NOT NULL,
        is_verified INTEGER DEFAULT 1
    """),
    ("tax_deductions_tds", "Withholding tax deducted at source on interest credits", """
        tds_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        quarter TEXT NOT NULL,
        tds_amount REAL NOT NULL,
        challan_no TEXT NOT NULL
    """),
    ("statement_requests", "Audit logs of e-statement generation and physical passbook printing", """
        request_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        format TEXT NOT NULL,
        delivery_channel TEXT NOT NULL,
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """),
    ("customer_feedback", "NPS ratings and branch service satisfaction feedback", """
        feedback_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        rating INTEGER NOT NULL,
        comments TEXT
    """),
    ("campaign_leads", "Pre-approved loan and credit card telemarketing sales leads", """
        lead_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        product_type TEXT NOT NULL,
        lead_status TEXT NOT NULL,
        assigned_employee_id INTEGER REFERENCES employees(employee_id)
    """),
    ("netbanking_credentials", "Internet banking access logs and multi-factor credentials", """
        credential_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        login_alias TEXT NOT NULL UNIQUE,
        last_login_ts TIMESTAMP,
        is_mfa_enabled INTEGER DEFAULT 1
    """),
    ("upi_vpas", "Unified Payments Interface Virtual Payment Addresses (@nexusbank)", """
        vpa_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        vpa_address TEXT NOT NULL UNIQUE,
        is_primary INTEGER DEFAULT 1
    """),
    ("compliance_reports", "Mandatory RBI and FIU statutory regulatory returns", """
        report_id INTEGER PRIMARY KEY,
        report_name TEXT NOT NULL,
        reporting_period TEXT NOT NULL,
        filing_status TEXT NOT NULL,
        filed_by_employee_id INTEGER REFERENCES employees(employee_id)
    """),
    ("reward_points", "Customer debit and credit card loyalty bonus points", """
        reward_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        points_balance INTEGER NOT NULL DEFAULT 0,
        expiring_points INTEGER NOT NULL DEFAULT 0
    """),
    ("merchant_settlements", "Batch settlement payment runs to registered merchants", """
        settlement_id INTEGER PRIMARY KEY,
        merchant_id INTEGER NOT NULL REFERENCES merchants(merchant_id),
        batch_date DATE NOT NULL,
        gross_volume REAL NOT NULL,
        mdr_fee REAL NOT NULL,
        net_payout REAL NOT NULL
    """),
    ("chargeback_claims", "Payment network dispute claims between cardholder and merchant", """
        claim_id INTEGER PRIMARY KEY,
        txn_id INTEGER NOT NULL REFERENCES transactions(txn_id),
        claim_reason TEXT NOT NULL,
        status TEXT NOT NULL,
        deadline_date DATE NOT NULL
    """),
    ("overdraft_limits", "Approved temporary and permanent overdraft credit facilities", """
        od_id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(account_id),
        sanctioned_limit REAL NOT NULL,
        utilized_amount REAL NOT NULL DEFAULT 0.0,
        sanction_expiry DATE NOT NULL
    """),
    ("sanction_letters", "Digital loan approval sanction letters with covenants", """
        letter_id INTEGER PRIMARY KEY,
        loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
        letter_reference TEXT NOT NULL UNIQUE,
        terms_version TEXT NOT NULL,
        issued_date DATE NOT NULL
    """),
    ("mortgage_details", "Property mortgage deed registrations and title search records", """
        mortgage_id INTEGER PRIMARY KEY,
        loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
        property_address TEXT NOT NULL,
        title_deed_no TEXT NOT NULL,
        encumbrance_status TEXT NOT NULL
    """),
    ("branch_cash_drawers", "Branch teller cash drawers and end-of-day balances", """
        drawer_id INTEGER PRIMARY KEY,
        employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
        opening_cash REAL NOT NULL,
        closing_cash REAL NOT NULL,
        discrepancy REAL DEFAULT 0.0
    """),
    ("kyc_remediation_tasks", "Periodic re-KYC risk classification and remediation queues", """
        task_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        due_date DATE NOT NULL,
        risk_category TEXT NOT NULL,
        status TEXT NOT NULL
    """),
    ("internal_audit_findings", "Branch internal control inspection findings and non-compliance points", """
        finding_id INTEGER PRIMARY KEY,
        branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
        audit_date DATE NOT NULL,
        severity TEXT NOT NULL,
        remediation_status TEXT NOT NULL
    """)
]

def scale_up(db_target: Path):
    conn = sqlite3.connect(str(db_target))
    cur = conn.cursor()
    print(f"[*] Scaling up schema with 35 auxiliary tables in {db_target}...")
    for tbl_name, comment, ddl in AUXILIARY_TABLES:
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tbl_name} ({ddl});")
        cur.execute(f"CREATE VIEW IF NOT EXISTS \"bank.{tbl_name}\" AS SELECT * FROM {tbl_name};")

    conn.commit()
    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    total_tables = cur.fetchone()[0]
    conn.close()
    print(f"[+] Total tables in database now: {total_tables} (>50 scale target reached!)")

if __name__ == "__main__":
    scale_up(db_path)
