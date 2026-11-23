-- =============================================================================
-- NexusDB PostgreSQL 16 Schema Definition
-- Schemas: bank, app, audit
-- Roles: nexus_owner, nexus_reader, nexus_writer
-- =============================================================================

-- Create Roles if they do not exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexus_reader') THEN
        CREATE ROLE nexus_reader WITH LOGIN PASSWORD 'reader_secret';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexus_writer') THEN
        CREATE ROLE nexus_writer WITH LOGIN PASSWORD 'writer_secret';
    END IF;
END
$$;

-- Create Schemas
CREATE SCHEMA IF NOT EXISTS bank;
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS audit;

-- =============================================================================
-- Schema: bank (16 Core Banking Tables)
-- =============================================================================

-- 1. branches
CREATE TABLE IF NOT EXISTS bank.branches (
    branch_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    ifsc_prefix VARCHAR(11) NOT NULL UNIQUE
);
COMMENT ON TABLE bank.branches IS 'Physical banking branch locations across Indian cities';
COMMENT ON COLUMN bank.branches.branch_id IS 'Unique identifier for the branch';
COMMENT ON COLUMN bank.branches.name IS 'Name of the branch office';
COMMENT ON COLUMN bank.branches.city IS 'City where the branch is located';
COMMENT ON COLUMN bank.branches.state IS 'State in India where branch operates';
COMMENT ON COLUMN bank.branches.ifsc_prefix IS 'IFSC routing code prefix for electronic transactions';

-- 2. employees
CREATE TABLE IF NOT EXISTS bank.employees (
    employee_id SERIAL PRIMARY KEY,
    branch_id INT NOT NULL REFERENCES bank.branches(branch_id),
    name VARCHAR(120) NOT NULL,
    designation VARCHAR(80) NOT NULL
);
COMMENT ON TABLE bank.employees IS 'Bank staff and branch officers';
COMMENT ON COLUMN bank.employees.employee_id IS 'Unique employee identifier';
COMMENT ON COLUMN bank.employees.branch_id IS 'Branch where the employee is posted';
COMMENT ON COLUMN bank.employees.name IS 'Full legal name of the employee';
COMMENT ON COLUMN bank.employees.designation IS 'Job title (e.g. Branch Officer, Loan Manager, Auditor)';

-- 3. customers
CREATE TABLE IF NOT EXISTS bank.customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    dob DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    branch_id INT NOT NULL REFERENCES bank.branches(branch_id),
    kyc_status VARCHAR(20) NOT NULL DEFAULT 'VERIFIED',
    segment VARCHAR(50) NOT NULL DEFAULT 'RETAIL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bank.customers IS 'Retail and corporate banking customers';
COMMENT ON COLUMN bank.customers.customer_id IS 'Primary customer identification number';
COMMENT ON COLUMN bank.customers.full_name IS 'Full registered customer name';
COMMENT ON COLUMN bank.customers.dob IS 'Customer date of birth';
COMMENT ON COLUMN bank.customers.city IS 'Customer residential or registered city';
COMMENT ON COLUMN bank.customers.branch_id IS 'Home branch of customer';
COMMENT ON COLUMN bank.customers.kyc_status IS 'Know-Your-Customer verification status (VERIFIED, PENDING, REJECTED)';
COMMENT ON COLUMN bank.customers.segment IS 'Customer segment classification (RETAIL, HNI, SME, CORPORATE)';
COMMENT ON COLUMN bank.customers.created_at IS 'Timestamp of customer onboarding';

-- 4. account_types
CREATE TABLE IF NOT EXISTS bank.account_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    min_balance NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);
COMMENT ON TABLE bank.account_types IS 'Categories of deposit and transaction accounts';
COMMENT ON COLUMN bank.account_types.type_id IS 'Unique identifier for account type';
COMMENT ON COLUMN bank.account_types.name IS 'Name of account tier (SAVINGS, CURRENT, SALARY)';
COMMENT ON COLUMN bank.account_types.min_balance IS 'Minimum required balance in INR to avoid maintenance penalties';

-- 5. accounts
CREATE TABLE IF NOT EXISTS bank.accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES bank.customers(customer_id),
    type_id INT NOT NULL REFERENCES bank.account_types(type_id),
    branch_id INT NOT NULL REFERENCES bank.branches(branch_id),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bank.accounts IS 'Deposit and checking accounts held by customers';
COMMENT ON COLUMN bank.accounts.account_id IS 'Unique bank account number';
COMMENT ON COLUMN bank.accounts.customer_id IS 'Foreign key to account owner customer';
COMMENT ON COLUMN bank.accounts.type_id IS 'Type of account (SAVINGS, CURRENT, SALARY)';
COMMENT ON COLUMN bank.accounts.branch_id IS 'Branch holding this account';
COMMENT ON COLUMN bank.accounts.status IS 'Account state: ACTIVE, HOLD, FLAGGED, or CLOSED';
COMMENT ON COLUMN bank.accounts.balance IS 'Current cleared balance in INR';
COMMENT ON COLUMN bank.accounts.opened_at IS 'Account opening timestamp';

-- 6. merchants
CREATE TABLE IF NOT EXISTS bank.merchants (
    merchant_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    city VARCHAR(100) NOT NULL
);
COMMENT ON TABLE bank.merchants IS 'Commercial merchants receiving customer payments';
COMMENT ON COLUMN bank.merchants.merchant_id IS 'Unique merchant identifier';
COMMENT ON COLUMN bank.merchants.name IS 'Registered merchant brand name';
COMMENT ON COLUMN bank.merchants.category IS 'Merchant category code / sector (e.g. GROCERY, TRAVEL, DINING, HEALTHCARE)';
COMMENT ON COLUMN bank.merchants.city IS 'Settlement city of merchant';

-- 7. transactions
CREATE TABLE IF NOT EXISTS bank.transactions (
    txn_id BIGSERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES bank.accounts(account_id),
    txn_ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    amount NUMERIC(15, 2) NOT NULL,
    direction VARCHAR(2) NOT NULL CHECK (direction IN ('CR', 'DR')),
    channel VARCHAR(30) NOT NULL,
    merchant_id INT REFERENCES bank.merchants(merchant_id),
    balance_after NUMERIC(15, 2) NOT NULL
);
COMMENT ON TABLE bank.transactions IS 'Monetary ledger transactions across all bank accounts';
COMMENT ON COLUMN bank.transactions.txn_id IS 'Unique transaction sequence identifier';
COMMENT ON COLUMN bank.transactions.account_id IS 'Account transacted';
COMMENT ON COLUMN bank.transactions.txn_ts IS 'Timestamp transaction executed';
COMMENT ON COLUMN bank.transactions.amount IS 'Amount in INR transacted';
COMMENT ON COLUMN bank.transactions.direction IS 'Credit (CR) or Debit (DR) to account balance';
COMMENT ON COLUMN bank.transactions.channel IS 'Channel used: UPI, NEFT, IMPS, RTGS, ATM, POS';
COMMENT ON COLUMN bank.transactions.merchant_id IS 'Optional merchant identifier for POS/UPI merchant payments';
COMMENT ON COLUMN bank.transactions.balance_after IS 'Account balance in INR immediately after transaction posted';

-- 8. cards
CREATE TABLE IF NOT EXISTS bank.cards (
    card_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES bank.accounts(account_id),
    network VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    credit_limit NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);
COMMENT ON TABLE bank.cards IS 'Debit and credit payment cards linked to customer accounts';
COMMENT ON COLUMN bank.cards.card_id IS 'Unique identifier for the card';
COMMENT ON COLUMN bank.cards.account_id IS 'Primary account linked to card';
COMMENT ON COLUMN bank.cards.network IS 'Payment network: RUPAY, VISA, MASTERCARD';
COMMENT ON COLUMN bank.cards.status IS 'Card status: ACTIVE, BLOCKED, EXPIRED';
COMMENT ON COLUMN bank.cards.credit_limit IS 'Credit limit in INR for credit cards (0 for debit)';

-- 9. loan_products
CREATE TABLE IF NOT EXISTS bank.loan_products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    base_rate NUMERIC(5, 2) NOT NULL,
    max_tenor_months INT NOT NULL
);
COMMENT ON TABLE bank.loan_products IS 'Catalog of lending products offered by bank';
COMMENT ON COLUMN bank.loan_products.product_id IS 'Unique loan product code';
COMMENT ON COLUMN bank.loan_products.name IS 'Product name (e.g. Home Loan, Personal Loan, Auto Loan, MSME Credit)';
COMMENT ON COLUMN bank.loan_products.base_rate IS 'Annual percentage benchmark interest rate';
COMMENT ON COLUMN bank.loan_products.max_tenor_months IS 'Maximum allowed repayment duration in months';

-- 10. loans
CREATE TABLE IF NOT EXISTS bank.loans (
    loan_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES bank.customers(customer_id),
    product_id INT NOT NULL REFERENCES bank.loan_products(product_id),
    principal NUMERIC(15, 2) NOT NULL,
    interest_rate NUMERIC(5, 2) NOT NULL,
    tenor_months INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DISBURSED',
    disbursed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bank.loans IS 'Lending contracts issued to customers';
COMMENT ON COLUMN bank.loans.loan_id IS 'Unique loan contract number';
COMMENT ON COLUMN bank.loans.customer_id IS 'Borrower customer identifier';
COMMENT ON COLUMN bank.loans.product_id IS 'Loan product type';
COMMENT ON COLUMN bank.loans.principal IS 'Total principal loan amount disbursed in INR';
COMMENT ON COLUMN bank.loans.interest_rate IS 'Contracted annual interest rate';
COMMENT ON COLUMN bank.loans.tenor_months IS 'Repayment term length in months';
COMMENT ON COLUMN bank.loans.status IS 'Loan status: SANCTIONED, DISBURSED, ACTIVE, DELINQUENT, CLOSED';
COMMENT ON COLUMN bank.loans.disbursed_at IS 'Date loan funds were transferred to borrower';

-- 11. repayments
CREATE TABLE IF NOT EXISTS bank.repayments (
    repayment_id BIGSERIAL PRIMARY KEY,
    loan_id INT NOT NULL REFERENCES bank.loans(loan_id),
    due_date DATE NOT NULL,
    paid_date DATE,
    amount_due NUMERIC(12, 2) NOT NULL,
    amount_paid NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    days_past_due INT NOT NULL DEFAULT 0
);
COMMENT ON TABLE bank.repayments IS 'Monthly loan installment schedules and payment tracking';
COMMENT ON COLUMN bank.repayments.repayment_id IS 'Unique repayment schedule record ID';
COMMENT ON COLUMN bank.repayments.loan_id IS 'Associated loan contract';
COMMENT ON COLUMN bank.repayments.due_date IS 'Scheduled installment due date';
COMMENT ON COLUMN bank.repayments.paid_date IS 'Actual date customer paid installment';
COMMENT ON COLUMN bank.repayments.amount_due IS 'Installment due amount in INR';
COMMENT ON COLUMN bank.repayments.amount_paid IS 'Actual amount in INR paid by borrower';
COMMENT ON COLUMN bank.repayments.days_past_due IS 'Number of overdue days (>= 30 delinquent, >= 90 NPA)';

-- 12. credit_tiers
CREATE TABLE IF NOT EXISTS bank.credit_tiers (
    tier_id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,
    min_score INT NOT NULL,
    max_score INT NOT NULL
);
COMMENT ON TABLE bank.credit_tiers IS 'Credit score rating bands from Tier A (Prime) to Tier E (Subprime)';
COMMENT ON COLUMN bank.credit_tiers.tier_id IS 'Tier code ID';
COMMENT ON COLUMN bank.credit_tiers.name IS 'Letter rating: A, B, C, D, E';
COMMENT ON COLUMN bank.credit_tiers.min_score IS 'Minimum credit score for tier';
COMMENT ON COLUMN bank.credit_tiers.max_score IS 'Maximum credit score for tier';

-- 13. credit_scores
CREATE TABLE IF NOT EXISTS bank.credit_scores (
    score_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES bank.customers(customer_id),
    score INT NOT NULL,
    tier_id INT NOT NULL REFERENCES bank.credit_tiers(tier_id),
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bank.credit_scores IS 'Historical and latest credit bureau risk ratings for customers';
COMMENT ON COLUMN bank.credit_scores.score_id IS 'Unique scoring record';
COMMENT ON COLUMN bank.credit_scores.customer_id IS 'Evaluated customer';
COMMENT ON COLUMN bank.credit_scores.score IS 'Bureau credit score ranging 300 to 900';
COMMENT ON COLUMN bank.credit_scores.tier_id IS 'Mapped risk tier band';
COMMENT ON COLUMN bank.credit_scores.scored_at IS 'Timestamp of credit score calculation';

-- 14. risk_flags
CREATE TABLE IF NOT EXISTS bank.risk_flags (
    flag_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES bank.accounts(account_id),
    flag_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    set_by VARCHAR(80) NOT NULL,
    set_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bank.risk_flags IS 'Operational risk, AML and compliance alert flags placed on accounts';
COMMENT ON COLUMN bank.risk_flags.flag_id IS 'Unique risk flag ID';
COMMENT ON COLUMN bank.risk_flags.account_id IS 'Account targeted by risk flag';
COMMENT ON COLUMN bank.risk_flags.flag_type IS 'Category of flag: AML_SUSPICION, KY_MISMATCH, OVERDRAFT_DEF, FRAUD_ALERT';
COMMENT ON COLUMN bank.risk_flags.severity IS 'Alert severity: LOW, MEDIUM, HIGH, CRITICAL';
COMMENT ON COLUMN bank.risk_flags.reason IS 'Compliance rationale provided for placing the flag';
COMMENT ON COLUMN bank.risk_flags.set_by IS 'Username or role who authorized flag';
COMMENT ON COLUMN bank.risk_flags.set_at IS 'Timestamp flag was logged';

-- 15. gl_accounts
CREATE TABLE IF NOT EXISTS bank.gl_accounts (
    gl_id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    type VARCHAR(30) NOT NULL
);
COMMENT ON TABLE bank.gl_accounts IS 'General ledger chart of accounts for financial reconciliation';
COMMENT ON COLUMN bank.gl_accounts.gl_id IS 'General ledger account ID';
COMMENT ON COLUMN bank.gl_accounts.code IS 'Standard GL accounting code';
COMMENT ON COLUMN bank.gl_accounts.name IS 'General ledger account name (e.g. Retail Deposits, Loan Assets)';
COMMENT ON COLUMN bank.gl_accounts.type IS 'Accounting category: ASSET, LIABILITY, REVENUE, EXPENSE, EQUITY';

-- 16. ledger_entries
CREATE TABLE IF NOT EXISTS bank.ledger_entries (
    entry_id BIGSERIAL PRIMARY KEY,
    gl_id INT NOT NULL REFERENCES bank.gl_accounts(gl_id),
    account_id INT NOT NULL REFERENCES bank.accounts(account_id),
    entry_date DATE NOT NULL,
    debit NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    credit NUMERIC(15, 2) NOT NULL DEFAULT 0.00
);
COMMENT ON TABLE bank.ledger_entries IS 'Double-entry general ledger journal postings for reconciliation';
COMMENT ON COLUMN bank.ledger_entries.entry_id IS 'Journal entry primary key';
COMMENT ON COLUMN bank.ledger_entries.gl_id IS 'Mapped general ledger account';
COMMENT ON COLUMN bank.ledger_entries.account_id IS 'Corresponding customer bank account';
COMMENT ON COLUMN bank.ledger_entries.entry_date IS 'Posting date';
COMMENT ON COLUMN bank.ledger_entries.debit IS 'Debit amount in INR';
COMMENT ON COLUMN bank.ledger_entries.credit IS 'Credit amount in INR';


-- =============================================================================
-- Schema: app (Users, Roles, Permissions, Action Catalogue)
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.roles (
    role_name VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL REFERENCES app.roles(role_name),
    branch_id INT REFERENCES bank.branches(branch_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.action_catalog (
    action_name VARCHAR(60) PRIMARY KEY,
    description TEXT NOT NULL,
    allowed_roles TEXT[] NOT NULL,
    target_table VARCHAR(60) NOT NULL,
    allowed_columns TEXT[] NOT NULL
);

-- =============================================================================
-- Schema: audit (Tamper-Evident SHA-256 Hash Chained Audit Log)
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit.log (
    seq BIGSERIAL PRIMARY KEY,
    ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    request_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    payload JSONB NOT NULL,
    prev_hash CHAR(64) NOT NULL,
    row_hash CHAR(64) NOT NULL
);

-- Triggers to enforce immutability on audit.log
CREATE OR REPLACE FUNCTION audit.prevent_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit.log is strictly append-only. UPDATE, DELETE and TRUNCATE are prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_no_update ON audit.log;
CREATE TRIGGER trg_audit_no_update
BEFORE UPDATE OR DELETE ON audit.log
FOR EACH ROW EXECUTE FUNCTION audit.prevent_mutation();


-- =============================================================================
-- Role Permissions & Grants
-- =============================================================================

-- Grants for nexus_reader (SELECT only on bank schema)
GRANT USAGE ON SCHEMA bank TO nexus_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA bank TO nexus_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA bank GRANT SELECT ON TABLES TO nexus_reader;
REVOKE ALL ON SCHEMA app FROM nexus_reader;
REVOKE ALL ON SCHEMA audit FROM nexus_reader;

-- Grants for nexus_writer (Column-level UPDATE on action targets, INSERT on audit.log)
GRANT USAGE ON SCHEMA bank TO nexus_writer;
GRANT USAGE ON SCHEMA audit TO nexus_writer;
GRANT SELECT (account_id, branch_id, status) ON bank.accounts TO nexus_writer;
GRANT UPDATE (status) ON bank.accounts TO nexus_writer;
GRANT SELECT, INSERT ON bank.risk_flags TO nexus_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bank TO nexus_writer;
GRANT INSERT, SELECT ON audit.log TO nexus_writer;
GRANT USAGE, SELECT ON SEQUENCE audit.log_seq_seq TO nexus_writer;
