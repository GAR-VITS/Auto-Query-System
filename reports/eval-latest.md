# NexusDB Evaluation Benchmark Report

**Generated:** 2026-11-23T20:31:23Z  
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
| **Latency (p50)** | < 1000ms | **489.8 ms** | ✅ PASS |
| **Latency (p95)** | < 3000ms | **661.5 ms** | ✅ PASS |
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
| `q01` | `simple_aggregation` | How many total customers are registered? | ✅ PASS | 557.3ms |
| `q02` | `simple_aggregation` | What is the total balance across all active accounts? | ✅ PASS | 431.4ms |
| `q03` | `simple_aggregation` | What is the average credit score of customers? | ✅ PASS (Repaired) | 691.3ms |
| `q04` | `simple_aggregation` | How many loans are currently disbursed? | ✅ PASS | 526.0ms |
| `q05` | `simple_aggregation` | What is the maximum principal amount among all loans? | ✅ PASS | 435.1ms |
| `q06` | `multi_table_joins` | Show top 5 branches by loan volume | ✅ PASS | 450.4ms |
| `q07` | `multi_table_joins` | List customer names with their account balances | ✅ PASS | 490.6ms |
| `q08` | `multi_table_joins` | Find total loan principal by branch city | ✅ PASS | 440.1ms |
| `q09` | `multi_table_joins` | List accounts belonging to customers with risk flags | ✅ PASS | 494.8ms |
| `q10` | `multi_table_joins` | Show transaction count per branch | ✅ PASS | 547.6ms |
| `q11` | `multi_table_joins` | List customers who have both savings and current accounts | ✅ PASS | 534.1ms |
| `q12` | `multi_table_joins` | Find top 5 customers with largest total loan principal | ✅ PASS | 497.5ms |
| `q13` | `multi_table_joins` | Show total transactions amount grouped by branch city | ✅ PASS | 539.6ms |
| `q14` | `date_arithmetic` | How many accounts were opened in the last 180 days? | ✅ PASS | 451.3ms |
| `q15` | `date_arithmetic` | Find total repayments due in the year 2026 | ✅ PASS | 432.0ms |
| `q16` | `date_arithmetic` | List transactions that occurred in the last 30 days | ✅ PASS | 508.4ms |
| `q17` | `date_arithmetic` | Count customers registered per month in 2026 | ✅ PASS | 415.0ms |
| `q18` | `date_arithmetic` | Find overdue loan repayments that are more than 30 days past due | ✅ PASS | 430.5ms |
| `q19` | `date_arithmetic` | Find average account age in days | ✅ PASS | 509.1ms |
| `q20` | `business_definitions` | List customers with high risk flag and delinquent loans | ✅ PASS | 625.3ms |
| `q21` | `business_definitions` | Count of NPA loans | ✅ PASS | 617.6ms |
| `q22` | `business_definitions` | List defaulter customers | ✅ PASS | 518.2ms |
| `q23` | `business_definitions` | How many active customers exist? | ✅ PASS | 506.1ms |
| `q24` | `business_definitions` | Count customers in Prime credit tier | ✅ PASS | 485.8ms |
| `q25` | `business_definitions` | Count customers in Subprime credit tier | ✅ PASS (Repaired) | 741.0ms |
| `q26` | `business_definitions` | Total principal for delinquent loans | ✅ PASS | 477.2ms |
| `q27` | `business_definitions` | List accounts on hold | ✅ PASS | 541.1ms |
| `q28` | `edge_cases` | Find transactions for account 9999999 | ✅ PASS | 488.9ms |
| `q29` | `edge_cases` | Show loans with zero principal | ✅ PASS | 524.4ms |
| `q30` | `edge_cases` | Find customers with pending kyc | ✅ PASS | 481.3ms |
| `q31` | `edge_cases` | Calculate loan repayment collection ratio | ✅ PASS | 500.2ms |
| `q32` | `edge_cases` | Count accounts with zero balance | ✅ PASS | 469.8ms |
| `q33` | `ambiguous` | Show performance | ✅ PASS | 277.1ms |
| `q34` | `ambiguous` | Get branch stats | ✅ PASS | 275.7ms |
| `q35` | `ambiguous` | Show risk | ✅ PASS | 243.4ms |
| `q36` | `ambiguous` | Who is the best? | ✅ PASS | 250.0ms |
| `q37` | `reconciliations` | Reconcile daily ledger vs transaction sums for account 10482 | ✅ PASS | 483.1ms |
| `q38` | `reconciliations` | Find all ledger entries with reconciliation mismatches | ✅ PASS | 482.7ms |
| `q39` | `reconciliations` | Show daily ledger summary for account 10482 | ✅ PASS | 659.9ms |
| `q40` | `actions` | Activate account 10482 | ✅ PASS | 282.4ms |
