-- PostgreSQL schema for Enterprise Financial Platform
-- Encoding: UTF8
-- Timezone: UTC

-- Lookup tables for normalization and strong referential integrity.

CREATE TABLE customer_status (
  status_id SERIAL PRIMARY KEY,
  status_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE customer_status IS 'Lookup table for customer lifecycle status values.';
COMMENT ON COLUMN customer_status.status_name IS 'Status name such as Active, Inactive, or Closed.';
COMMENT ON COLUMN customer_status.description IS 'Human-readable description for the customer status.';

CREATE TABLE account_types (
  account_type_id SERIAL PRIMARY KEY,
  type_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE account_types IS 'Lookup table for the type of account, such as Savings or Current.';
COMMENT ON COLUMN account_types.type_name IS 'Account type label.';
COMMENT ON COLUMN account_types.description IS 'Explanation of the account type semantics.';

CREATE TABLE account_statuses (
  account_status_id SERIAL PRIMARY KEY,
  status_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE account_statuses IS 'Lookup table for account lifecycle statuses.';
COMMENT ON COLUMN account_statuses.status_name IS 'Account status label such as Active, Frozen, or Closed.';
COMMENT ON COLUMN account_statuses.description IS 'Description of account status behavior.';

CREATE TABLE loan_types (
  loan_type_id SERIAL PRIMARY KEY,
  loan_type_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE loan_types IS 'Lookup table defining loan product categories.';
COMMENT ON COLUMN loan_types.loan_type_name IS 'Loan product name such as Personal, Mortgage, or Business.';
COMMENT ON COLUMN loan_types.description IS 'Description of the loan product and typical usage.';

CREATE TABLE loan_statuses (
  loan_status_id SERIAL PRIMARY KEY,
  status_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE loan_statuses IS 'Lookup table for loan lifecycle states.';
COMMENT ON COLUMN loan_statuses.status_name IS 'Loan status label such as Active, Defaulted, or Review.';
COMMENT ON COLUMN loan_statuses.description IS 'Description of the loan status semantics.';

CREATE TABLE payment_statuses (
  payment_status_id SERIAL PRIMARY KEY,
  status_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE payment_statuses IS 'Lookup table for scheduled loan payment statuses.';
COMMENT ON COLUMN payment_statuses.status_name IS 'Payment status label such as Due, Paid, Late, or Missed.';
COMMENT ON COLUMN payment_statuses.description IS 'Description of payment status meaning.';

CREATE TABLE transaction_types (
  transaction_type_id SERIAL PRIMARY KEY,
  type_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE transaction_types IS 'Lookup table for transaction categories.';
COMMENT ON COLUMN transaction_types.type_name IS 'Transaction type label such as Payment, Disbursement, or Fee.';
COMMENT ON COLUMN transaction_types.description IS 'Description of the transaction type.';

CREATE TABLE risk_tiers (
  risk_tier_id SERIAL PRIMARY KEY,
  tier_name TEXT NOT NULL UNIQUE,
  min_score INT NOT NULL,
  max_score INT NOT NULL,
  description TEXT NOT NULL
);
COMMENT ON TABLE risk_tiers IS 'Lookup table mapping credit score ranges to risk tiers.';
COMMENT ON COLUMN risk_tiers.tier_name IS 'Risk tier label such as Low Risk or High Risk.';
COMMENT ON COLUMN risk_tiers.min_score IS 'Inclusive minimum credit score for this tier.';
COMMENT ON COLUMN risk_tiers.max_score IS 'Inclusive maximum credit score for this tier.';
COMMENT ON COLUMN risk_tiers.description IS 'Explanation of the risk tier and business interpretation.';

CREATE TABLE roles (
  role_id SERIAL PRIMARY KEY,
  role_name TEXT NOT NULL UNIQUE,
  permissions TEXT NOT NULL,
  description TEXT NOT NULL
);
COMMENT ON TABLE roles IS 'Lookup table for user roles and permission groups.';
COMMENT ON COLUMN roles.role_name IS 'User role label such as admin, analyst, manager, or viewer.';
COMMENT ON COLUMN roles.permissions IS 'Comma-separated permission tokens for the role.';
COMMENT ON COLUMN roles.description IS 'Description of role responsibilities and access level.';

CREATE TABLE agents (
  agent_id SERIAL PRIMARY KEY,
  agent_code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  current_status TEXT NOT NULL,
  last_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE agents IS 'Registry table for the AI agents shown in the dashboard.';
COMMENT ON COLUMN agents.agent_code IS 'Stable agent identifier such as query, analysis, or visualization.';
COMMENT ON COLUMN agents.name IS 'Human-readable agent name.';
COMMENT ON COLUMN agents.current_status IS 'Current runtime status label for the agent.';
COMMENT ON COLUMN agents.last_run_at IS 'Timestamp when the agent last executed work.';
COMMENT ON COLUMN agents.created_at IS 'Creation timestamp for the agent record.';

CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  role_id INT NOT NULL REFERENCES roles(role_id),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMPTZ
);
COMMENT ON TABLE users IS 'Table for human users operating the enterprise platform.';
COMMENT ON COLUMN users.email IS 'Unique login email for the user.';
COMMENT ON COLUMN users.full_name IS 'Full descriptive name of the user.';
COMMENT ON COLUMN users.role_id IS 'Foreign key to the roles table for RBAC.';
COMMENT ON COLUMN users.is_active IS 'Flag indicating whether the user account is active.';
COMMENT ON COLUMN users.last_login_at IS 'Last login timestamp for audit and session tracking.';

CREATE TABLE customers (
  customer_id SERIAL PRIMARY KEY,
  customer_code TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  date_of_birth DATE,
  customer_since DATE NOT NULL,
  customer_status_id INT NOT NULL REFERENCES customer_status(status_id),
  preferred_language TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE customers IS 'Customer master table with demographic and status information.';
COMMENT ON COLUMN customers.customer_code IS 'Stable reference code used by the app, such as C-1042.';
COMMENT ON COLUMN customers.customer_status_id IS 'FK to customer_status; ensures customer lifecycle states are normalized.';
COMMENT ON COLUMN customers.created_at IS 'Timestamp when the customer record was first created.';
COMMENT ON COLUMN customers.updated_at IS 'Timestamp when the customer record was last updated.';

CREATE TABLE accounts (
  account_id SERIAL PRIMARY KEY,
  account_number TEXT NOT NULL UNIQUE,
  customer_id INT NOT NULL REFERENCES customers(customer_id),
  account_type_id INT NOT NULL REFERENCES account_types(account_type_id),
  account_status_id INT NOT NULL REFERENCES account_statuses(account_status_id),
  currency TEXT NOT NULL DEFAULT 'INR',
  opened_date DATE NOT NULL,
  closed_date DATE,
  current_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
  available_balance NUMERIC(18,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE accounts IS 'Financial account table used for linked deposit, savings, and loan accounts.';
COMMENT ON COLUMN accounts.account_number IS 'Unique account identifier visible to users and agents.';
COMMENT ON COLUMN accounts.customer_id IS 'FK to customers identifying the account owner.';
COMMENT ON COLUMN accounts.current_balance IS 'Current ledger balance of the account.';
COMMENT ON COLUMN accounts.available_balance IS 'Balance available for withdrawal or settlement.';

CREATE TABLE loan_accounts (
  loan_id SERIAL PRIMARY KEY,
  loan_number TEXT NOT NULL UNIQUE,
  customer_id INT NOT NULL REFERENCES customers(customer_id),
  account_id INT REFERENCES accounts(account_id),
  loan_type_id INT NOT NULL REFERENCES loan_types(loan_type_id),
  loan_status_id INT NOT NULL REFERENCES loan_statuses(loan_status_id),
  principal_amount NUMERIC(18,2) NOT NULL,
  outstanding_amount NUMERIC(18,2) NOT NULL,
  interest_rate NUMERIC(5,2) NOT NULL,
  term_months INT NOT NULL,
  payment_frequency TEXT NOT NULL,
  origination_date DATE NOT NULL,
  next_payment_date DATE,
  maturity_date DATE NOT NULL,
  default_date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE loan_accounts IS 'Loan account table linking customers to loan products and balances.';
COMMENT ON COLUMN loan_accounts.loan_number IS 'Unique external loan identifier such as LA-9918.';
COMMENT ON COLUMN loan_accounts.loan_status_id IS 'FK to loan_statuses; e.g. 1=Active, 3=Defaulted.';
COMMENT ON COLUMN loan_accounts.principal_amount IS 'Original loan principal amount.';
COMMENT ON COLUMN loan_accounts.outstanding_amount IS 'Outstanding balance remaining on the loan.';
COMMENT ON COLUMN loan_accounts.payment_frequency IS 'Payment cadence such as Monthly or Quarterly.';

CREATE TABLE loan_payment_schedule (
  schedule_id SERIAL PRIMARY KEY,
  loan_id INT NOT NULL REFERENCES loan_accounts(loan_id),
  payment_number INT NOT NULL,
  due_date DATE NOT NULL,
  amount_due NUMERIC(18,2) NOT NULL,
  principal_due NUMERIC(18,2) NOT NULL,
  interest_due NUMERIC(18,2) NOT NULL,
  balance_remaining NUMERIC(18,2) NOT NULL,
  payment_status_id INT NOT NULL REFERENCES payment_statuses(payment_status_id),
  paid_date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE loan_payment_schedule IS 'Amortization schedule items for loan repayment tracking.';
COMMENT ON COLUMN loan_payment_schedule.payment_status_id IS 'FK to payment_statuses; helps classify due, paid, late, or missed payments.';

CREATE TABLE transactions (
  transaction_id SERIAL PRIMARY KEY,
  transaction_code TEXT NOT NULL UNIQUE,
  account_id INT NOT NULL REFERENCES accounts(account_id),
  loan_id INT REFERENCES loan_accounts(loan_id),
  transaction_type_id INT NOT NULL REFERENCES transaction_types(transaction_type_id),
  transaction_date TIMESTAMPTZ NOT NULL,
  amount NUMERIC(18,2) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'INR',
  balance_after NUMERIC(18,2),
  reference TEXT,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE transactions IS 'Ledger of financial transactions including payments, fees, and adjustments.';
COMMENT ON COLUMN transactions.transaction_code IS 'Unique reference code for the transaction.';
COMMENT ON COLUMN transactions.loan_id IS 'Optional FK to loan_accounts for loan-related transactions.';
COMMENT ON COLUMN transactions.transaction_type_id IS 'FK to transaction_types normalizing transaction categories.';

CREATE TABLE credit_reports (
  credit_report_id SERIAL PRIMARY KEY,
  customer_id INT NOT NULL REFERENCES customers(customer_id),
  bureau_name TEXT NOT NULL,
  credit_score INT NOT NULL,
  risk_tier_id INT NOT NULL REFERENCES risk_tiers(risk_tier_id),
  report_date DATE NOT NULL,
  report_summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE credit_reports IS 'Customer credit score snapshots and risk tier assignments.';
COMMENT ON COLUMN credit_reports.credit_score IS 'Numeric credit score value from the bureau.';
COMMENT ON COLUMN credit_reports.risk_tier_id IS 'FK to risk_tiers giving a business risk label to the score.';

CREATE TABLE audit_action_types (
  action_type_id SERIAL PRIMARY KEY,
  action_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE audit_action_types IS 'Lookup table for audit event actions.';
COMMENT ON COLUMN audit_action_types.action_name IS 'Action label such as query_executed or loan_approved.';

CREATE TABLE audit_statuses (
  audit_status_id SERIAL PRIMARY KEY,
  status_name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL
);
COMMENT ON TABLE audit_statuses IS 'Lookup table for audit event statuses.';
COMMENT ON COLUMN audit_statuses.status_name IS 'Audit status label such as approved or auto_executed.';

CREATE TABLE audit_logs (
  audit_id SERIAL PRIMARY KEY,
  event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  action_type_id INT NOT NULL REFERENCES audit_action_types(action_type_id),
  audit_status_id INT NOT NULL REFERENCES audit_statuses(audit_status_id),
  agent_id INT REFERENCES agents(agent_id),
  user_id INT REFERENCES users(user_id),
  description TEXT NOT NULL,
  reasoning TEXT NOT NULL,
  affected_record_count INT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE audit_logs IS 'Record of system, agent, and user actions for compliance and traceability.';
COMMENT ON COLUMN audit_logs.metadata IS 'Optional JSON metadata for audit events, such as query context or external references.';

CREATE TABLE query_history (
  query_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id),
  question TEXT NOT NULL,
  sql_text TEXT NOT NULL,
  row_count INT,
  execution_time_ms INT,
  corrections INT,
  analysis TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE query_history IS 'History of natural language queries and their SQL executions.';
COMMENT ON COLUMN query_history.corrections IS 'Number of self-corrections applied by the query agent.';

-- Seed lookup values for status and reference data.

INSERT INTO customer_status (status_name, description) VALUES
  ('Active', 'Customer has an active relationship with the enterprise.'),
  ('Inactive', 'Customer record exists but is not currently active.'),
  ('Closed', 'Customer relationship has been closed.');

INSERT INTO account_types (type_name, description) VALUES
  ('Savings', 'Interest-bearing savings account.'),
  ('Current', 'Non-interest-bearing current account used for payments.'),
  ('Loan', 'Loan-linked account used to settle debt.');

INSERT INTO account_statuses (status_name, description) VALUES
  ('Active', 'Account is open and can be used.'),
  ('Frozen', 'Account is temporarily restricted.'),
  ('Closed', 'Account has been closed.');

INSERT INTO loan_types (loan_type_name, description) VALUES
  ('Personal', 'Unsecured personal loan.'),
  ('Mortgage', 'Secured loan backed by real estate.'),
  ('Business', 'Business working capital or term loan.');

INSERT INTO loan_statuses (status_name, description) VALUES
  ('Active', 'Loan is current and being serviced.'),
  ('Paid Off', 'Loan has been fully repaid.'),
  ('Defaulted', 'Loan is in default status.'),
  ('Review', 'Loan requires manual review.'),
  ('Closed', 'Loan account has been closed.');

INSERT INTO payment_statuses (status_name, description) VALUES
  ('Due', 'Payment is scheduled but not yet paid.'),
  ('Paid', 'Payment has been received.'),
  ('Late', 'Payment is overdue but not yet defaulted.'),
  ('Missed', 'Payment was missed and not recorded as paid.');

INSERT INTO transaction_types (type_name, description) VALUES
  ('Payment', 'Customer payment against a loan or account balance.'),
  ('Disbursement', 'Loan funds released to the customer.'),
  ('Fee', 'Service fee, penalty, or charge.'),
  ('Adjustment', 'Balance adjustment or correction.');

INSERT INTO risk_tiers (tier_name, min_score, max_score, description) VALUES
  ('Low Risk', 720, 850, 'Strong credit profile with low default probability.'),
  ('Medium Risk', 650, 719, 'Moderate credit profile with some risk.'),
  ('High Risk', 600, 649, 'Weak credit profile with elevated risk.'),
  ('Critical', 0, 599, 'Very low credit score and high default risk.');

INSERT INTO roles (role_name, permissions, description) VALUES
  ('admin', 'read,write,approve,audit', 'Full system administrator role.'),
  ('analyst', 'read,write', 'Data analyst role with query and reporting privileges.'),
  ('manager', 'read,approve', 'Manager role with review and approval authority.'),
  ('viewer', 'read', 'Read-only role for auditing and monitoring.');

INSERT INTO agents (agent_code, name, description, current_status) VALUES
  ('query', 'Query Agent', 'Translates natural language into SQL and self-corrects errors.', 'idle'),
  ('analysis', 'Analysis Agent', 'Evaluates results and generates plain-English summaries.', 'idle'),
  ('visualization', 'Visualization Agent', 'Builds charts and visual narratives from query output.', 'idle');

INSERT INTO audit_action_types (action_name, description) VALUES
  ('query_executed', 'Natural language SQL query execution logged.'),
  ('credit_evaluation', 'Automated credit evaluation event.'),
  ('defaulter_flagged', 'Customer flagged as high-risk or defaulter.'),
  ('loan_approved', 'Loan approval event recorded.'),
  ('status_updated', 'Status change or workflow transition logged.');

INSERT INTO audit_statuses (status_name, description) VALUES
  ('approved', 'Action was approved.'),
  ('pending', 'Action is pending review.'),
  ('rejected', 'Action was rejected.'),
  ('auto_executed', 'Action was executed automatically by the system.');

-- Spider benchmark support tables for NL-to-SQL training and evaluation.

CREATE TABLE spider_databases (
  spider_db_id SERIAL PRIMARY KEY,
  database_name TEXT NOT NULL UNIQUE,
  domain TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE spider_databases IS 'Registry of Spider benchmark databases included for NL2SQL evaluation.';
COMMENT ON COLUMN spider_databases.database_name IS 'Unique benchmark database name.';
COMMENT ON COLUMN spider_databases.domain IS 'Domain classification such as finance, travel, or education.';
COMMENT ON COLUMN spider_databases.description IS 'Description of the benchmark database and its schema focus.';

CREATE TABLE spider_tables (
  spider_table_id SERIAL PRIMARY KEY,
  spider_db_id INT NOT NULL REFERENCES spider_databases(spider_db_id),
  table_name TEXT NOT NULL,
  description TEXT NOT NULL
);
COMMENT ON TABLE spider_tables IS 'Tables that belong to a Spider benchmark database schema.';
COMMENT ON COLUMN spider_tables.table_name IS 'Name of a Spider schema table.';
COMMENT ON COLUMN spider_tables.description IS 'Description of the table and the data it contains.';

CREATE TABLE spider_columns (
  spider_column_id SERIAL PRIMARY KEY,
  spider_table_id INT NOT NULL REFERENCES spider_tables(spider_table_id),
  column_name TEXT NOT NULL,
  data_type TEXT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  is_foreign BOOLEAN NOT NULL DEFAULT FALSE,
  description TEXT NOT NULL
);
COMMENT ON TABLE spider_columns IS 'Columns and schema metadata for Spider benchmark tables.';
COMMENT ON COLUMN spider_columns.data_type IS 'Data type of the column used in the benchmark schema.';
COMMENT ON COLUMN spider_columns.is_primary IS 'Indicates if this column is the table primary key.';
COMMENT ON COLUMN spider_columns.is_foreign IS 'Indicates if this column references another table.';

CREATE TABLE spider_queries (
  spider_query_id SERIAL PRIMARY KEY,
  spider_db_id INT NOT NULL REFERENCES spider_databases(spider_db_id),
  natural_language TEXT NOT NULL,
  sql_query TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE spider_queries IS 'Natural language questions paired with SQL queries for Spider benchmark evaluation.';
COMMENT ON COLUMN spider_queries.difficulty IS 'Difficulty level of the Spider query such as easy, medium, or hard.';

-- Performance tuning for AI-generated queries.

ALTER TABLE accounts
  ADD COLUMN overdraft_limit NUMERIC(18,2) NOT NULL DEFAULT 0,
  ADD CONSTRAINT accounts_balance_check CHECK (current_balance >= -overdraft_limit),
  ADD CONSTRAINT accounts_available_balance_check CHECK (available_balance >= 0 AND available_balance <= current_balance + overdraft_limit);
COMMENT ON COLUMN accounts.overdraft_limit IS 'Approved overdraft allowance that permits negative current_balance up to this limit.';

ALTER TABLE accounts
  ADD CONSTRAINT accounts_current_balance_check CHECK (current_balance >= -5000);
ALTER TABLE loan_accounts
  ADD CONSTRAINT loan_principal_nonnegative CHECK (principal_amount >= 0),
  ADD CONSTRAINT loan_outstanding_nonnegative CHECK (outstanding_amount >= 0),
  ADD CONSTRAINT loan_interest_nonnegative CHECK (interest_rate >= 0),
  ADD CONSTRAINT loan_term_positive CHECK (term_months > 0),
  ADD CONSTRAINT loan_dates_consistent CHECK (maturity_date >= origination_date);
ALTER TABLE transactions
  ADD CONSTRAINT transaction_amount_nonnegative CHECK (amount >= 0);
ALTER TABLE credit_reports
  ADD CONSTRAINT credit_score_range CHECK (credit_score BETWEEN 300 AND 850);

CREATE INDEX idx_customers_status ON customers(customer_status_id);
CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_accounts_opened_date ON accounts(opened_date);
CREATE INDEX idx_accounts_status ON accounts(account_status_id);
CREATE INDEX idx_loan_customer ON loan_accounts(customer_id);
CREATE INDEX idx_loan_status ON loan_accounts(loan_status_id);
CREATE INDEX idx_loan_outstanding ON loan_accounts(outstanding_amount);
CREATE INDEX idx_loan_origination_date ON loan_accounts(origination_date);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_loan ON transactions(loan_id);
CREATE INDEX idx_transactions_date_amount ON transactions(transaction_date, amount);
CREATE INDEX idx_credit_customer ON credit_reports(customer_id);
CREATE INDEX idx_credit_score ON credit_reports(credit_score);
CREATE INDEX idx_audit_event_time ON audit_logs(event_timestamp);
CREATE INDEX idx_audit_action_status ON audit_logs(action_type_id, audit_status_id);
CREATE INDEX idx_query_user ON query_history(user_id);

CREATE VIEW comprehensive_client_view AS
SELECT
  c.customer_id,
  c.customer_code,
  c.first_name,
  c.last_name,
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
  la.outstanding_amount,
  la.default_date,
  cr.credit_score,
  rt.tier_name AS credit_risk_tier
FROM loan_accounts la
JOIN customers c ON la.customer_id = c.customer_id
LEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id
LEFT JOIN risk_tiers rt ON cr.risk_tier_id = rt.risk_tier_id
WHERE la.loan_status_id = (SELECT loan_status_id FROM loan_statuses WHERE status_name = 'Defaulted');

