# NexusDB Evaluation Benchmark Report

**Generated:** 2026-11-23T20:11:23Z  
**Harness:** Section 16 Automated Evaluation Engine  
**Dataset:** 40 multi-category banking domain questions (`tests/eval/questions.yaml`)  

---

## 1. Executive Summary

| Metric | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Execution Accuracy** | ≥ 85.0% | **100.0%** (40/40) | ✅ PASS |
| **First-Attempt Accuracy** | ≥ 70.0% | **82.5%** (33/40) | ✅ PASS |
| **Repaired Accuracy** | ≥ 60.0% | **100.0%** (2/2) | ✅ PASS |
| **Overall Repair Rate** | — | **5.0%** | Audited |
| **Latency (p50)** | < 1000ms | **482.4 ms** | ✅ PASS |
| **Latency (p95)** | < 3000ms | **709.4 ms** | ✅ PASS |
| **Context Saved (Semantic Memory)** | ≥ 60.0% | **75.9%** | ✅ PASS |

---

## 2. Category Breakdown

| Category | Total Questions | Passed | Success Rate | Repaired |
| :--- | :---: | :---: | :---: | :---: |
| `simple_aggregation` | 5 | 5 | **100.0%** | 1 |
| `multi_table_joins` | 8 | 8 | **100.0%** | 0 |
| `date_arithmetic` | 6 | 6 | **100.0%** | 0 |
| `business_definitions` | 8 | 8 | **100.0%** | 1 |
| `edge_cases` | 5 | 5 | **100.0%** | 0 |
| `ambiguous` | 4 | 4 | **100.0%** | 0 |
| `reconciliations` | 3 | 3 | **100.0%** | 0 |
| `actions` | 1 | 1 | **100.0%** | 0 |

---

## 3. Individual Test Question Results

| ID | Category | Question | Status | Latency |
| :--- | :--- | :--- | :---: | :---: |
| `q01` | `simple_aggregation` | How many total customers are registered? | ✅ PASS | 709.1ms |
| `q02` | `simple_aggregation` | What is the total balance across all active accounts? | ✅ PASS | 483.8ms |
| `q03` | `simple_aggregation` | What is the average credit score of customers? | ✅ PASS (Repaired) | 761.7ms |
| `q04` | `simple_aggregation` | How many loans are currently disbursed? | ✅ PASS | 515.0ms |
| `q05` | `simple_aggregation` | What is the maximum principal amount among all loans? | ✅ PASS | 516.8ms |
| `q06` | `multi_table_joins` | Show top 5 branches by loan volume | ✅ PASS | 517.6ms |
| `q07` | `multi_table_joins` | List customer names with their account balances | ✅ PASS | 516.1ms |
| `q08` | `multi_table_joins` | Find total loan principal by branch city | ✅ PASS | 500.1ms |
| `q09` | `multi_table_joins` | List accounts belonging to customers with risk flags | ✅ PASS | 481.5ms |
| `q10` | `multi_table_joins` | Show transaction count per branch | ✅ PASS | 506.4ms |
| `q11` | `multi_table_joins` | List customers who have both savings and current accounts | ✅ PASS | 492.0ms |
| `q12` | `multi_table_joins` | Find top 5 customers with largest total loan principal | ✅ PASS | 507.5ms |
| `q13` | `multi_table_joins` | Show total transactions amount grouped by branch city | ✅ PASS | 671.7ms |
| `q14` | `date_arithmetic` | How many accounts were opened in the last 180 days? | ✅ PASS | 487.4ms |
| `q15` | `date_arithmetic` | Find total repayments due in the year 2026 | ✅ PASS | 481.4ms |
| `q16` | `date_arithmetic` | List transactions that occurred in the last 30 days | ✅ PASS | 471.3ms |
| `q17` | `date_arithmetic` | Count customers registered per month in 2026 | ✅ PASS | 433.2ms |
| `q18` | `date_arithmetic` | Find overdue loan repayments that are more than 30 days past due | ✅ PASS | 496.7ms |
| `q19` | `date_arithmetic` | Find average account age in days | ✅ PASS | 471.0ms |
| `q20` | `business_definitions` | List customers with high risk flag and delinquent loans | ✅ PASS | 510.2ms |
| `q21` | `business_definitions` | Count of NPA loans | ✅ PASS | 428.4ms |
| `q22` | `business_definitions` | List defaulter customers | ✅ PASS | 455.2ms |
| `q23` | `business_definitions` | How many active customers exist? | ✅ PASS | 470.6ms |
| `q24` | `business_definitions` | Count customers in Prime credit tier | ✅ PASS | 474.8ms |
| `q25` | `business_definitions` | Count customers in Subprime credit tier | ✅ PASS (Repaired) | 715.3ms |
| `q26` | `business_definitions` | Total principal for delinquent loans | ✅ PASS | 500.2ms |
| `q27` | `business_definitions` | List accounts on hold | ✅ PASS | 519.2ms |
| `q28` | `edge_cases` | Find transactions for account 9999999 | ✅ PASS | 462.4ms |
| `q29` | `edge_cases` | Show loans with zero principal | ✅ PASS | 455.5ms |
| `q30` | `edge_cases` | Find customers with pending kyc | ✅ PASS | 485.4ms |
| `q31` | `edge_cases` | Calculate loan repayment collection ratio | ✅ PASS | 476.1ms |
| `q32` | `edge_cases` | Count accounts with zero balance | ✅ PASS | 433.0ms |
| `q33` | `ambiguous` | Show performance | ✅ PASS | 223.5ms |
| `q34` | `ambiguous` | Get branch stats | ✅ PASS | 220.3ms |
| `q35` | `ambiguous` | Show risk | ✅ PASS | 226.4ms |
| `q36` | `ambiguous` | Who is the best? | ✅ PASS | 228.8ms |
| `q37` | `reconciliations` | Reconcile daily ledger vs transaction sums for account 10482 | ✅ PASS | 478.6ms |
| `q38` | `reconciliations` | Find all ledger entries with reconciliation mismatches | ✅ PASS | 476.2ms |
| `q39` | `reconciliations` | Show daily ledger summary for account 10482 | ✅ PASS | 483.4ms |
| `q40` | `actions` | Activate account 10482 | ✅ PASS | 225.6ms |
