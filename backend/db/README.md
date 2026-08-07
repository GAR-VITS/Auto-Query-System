# PostgreSQL Schema Deployment

This folder contains the enterprise PostgreSQL schema and the database initialization script.

## What is included

- `schema.sql`: Complete relational schema with 3NF design, lookup tables, foreign keys, and detailed column comments.
- `init_db.py`: Helper script that executes `schema.sql` against a PostgreSQL database.

## Recommended schema structure

The schema includes:

- `customers`, `accounts`, `loan_accounts`, `transactions`, `credit_reports`
- Lookup tables such as `loan_statuses`, `transaction_types`, `risk_tiers`, `roles`, `audit_action_types`, and `audit_statuses`
- Strict primary keys and foreign keys for referential integrity
- `audit_logs` and `query_history` for agent and user traceability
- Comments on every column so AI agents can infer meaning from `status_id` values

## PostgreSQL setup

1. Create the database with UTF-8 encoding and UTC timezone.

```sql
CREATE DATABASE enterprise_finance
  WITH ENCODING='UTF8'
       LC_COLLATE='en_US.utf8'
       LC_CTYPE='en_US.utf8'
       TEMPLATE=template0;

ALTER DATABASE enterprise_finance SET timezone = 'UTC';
```

2. Install Python dependencies for database initialization.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Set the `DATABASE_URL` environment variable if needed.

```bash
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_finance
```

4. Run the initialization script.

```bash
cd backend/db
python init_db.py
```

5. Populate synthetic data and Spider benchmark sample content.

```bash
cd backend/db
python populate_synthetic.py
```

6. Run performance analysis for AI queries.

```bash
cd backend/db
python explain_analyze.py
```

If you prefer, you can also deploy the schema directly using `psql`:

```bash
psql "postgresql://postgres:postgres@localhost:5432/enterprise_finance" -f schema.sql
```

## Performance tuning for AI workloads

For a production-like AI testing environment, tune PostgreSQL settings in `postgresql.conf` or your cloud provider config:

- `max_connections = 200`
- `shared_buffers = 1GB`
- `work_mem = 16MB`
- `maintenance_work_mem = 256MB`
- `effective_cache_size = 3GB`
- `wal_buffers = 16MB`
- `checkpoint_completion_target = 0.7`

If you deploy with Docker, set environment variables or mount a custom PostgreSQL config file. These settings help AI agents open bursty connections and execute analytical queries without causing long full table scans.

## Notes

- The schema is designed to support the frontend mock queries and audit concepts in this project.
- `customers` is separate from `loan_accounts` and `transactions` to ensure normalization.
- Lookup tables like `loan_statuses` and `audit_statuses` prevent redundant string values.
- Column comments explicitly describe important business meanings, e.g. `loan_status_id` values.
