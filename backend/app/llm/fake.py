"""
NexusDB Deterministic FakeLLM for DEMO_MODE & Offline Testing
Serves scripted, high-precision SQL, intent classifications, and reflection repairs.
Includes scripted fault-injection queries for reflection loop demonstrations.
"""

import re
from typing import Any
from app.llm.base import IntentClassification, GeneratedSql, NarrativeResult


class FakeLLM:
    def __init__(self):
        self.call_count: int = 0
        self.repair_count: int = 0

    async def classify_intent(self, question: str) -> IntentClassification:
        q_lower = question.lower().strip()

        # Action: Put account on hold / set account status
        if any(kw in q_lower for kw in ("put account", "hold", "flag account", "close account", "update account status", "set account")):
            acc_match = re.search(r'account\s+(?:id\s+)?(\d+)', q_lower)
            acc_id = int(acc_match.group(1)) if acc_match else 10482

            new_status = "HOLD"
            if "active" in q_lower:
                new_status = "ACTIVE"
            elif "flagged" in q_lower or "flag" in q_lower:
                new_status = "FLAGGED"

            reason = "Suspicious activity detected"
            if "reason:" in q_lower:
                reason = question.split("reason:")[-1].strip()
            elif "reason" in q_lower:
                reason = question.split("reason")[-1].strip(" :")

            return IntentClassification(
                intent="action",
                action_name="SET_ACCOUNT_STATUS",
                parameters={"account_id": acc_id, "new_status": new_status, "reason": reason},
                confidence=0.98,
            )

        # Action: Set risk flag
        if "risk flag" in q_lower or "flag for aml" in q_lower:
            acc_match = re.search(r'account\s+(?:id\s+)?(\d+)', q_lower)
            acc_id = int(acc_match.group(1)) if acc_match else 10482
            return IntentClassification(
                intent="action",
                action_name="SET_RISK_FLAG",
                parameters={
                    "account_id": acc_id,
                    "flag_type": "AML_SUSPICION",
                    "severity": "HIGH",
                    "reason": "High frequency cross-border transaction pattern"
                },
                confidence=0.96,
            )

        # Clarify: Ambiguous question
        if q_lower in ("show me the report", "show reports", "report for last month", "show details", "data"):
            return IntentClassification(
                intent="clarify",
                clarify_question="Which specific report would you like: Loan Disbursements, Transaction Volume, or Delinquency Summary?",
                confidence=0.95,
            )

        return IntentClassification(intent="query", confidence=0.99)

    async def generate_sql(self, question: str, context: Any) -> GeneratedSql:
        self.call_count += 1
        q_lower = question.lower()

        # Scripted Fault Injection for Reflection Loop:
        # User asks for credit score below 600 or mentions credit score
        if "credit score below 600" in q_lower or "score below 600" in q_lower or "customers with credit score" in q_lower:
            # Deliberate failure on attempt 1: referencing non-existent column 'c.credit_score' on customers table
            return GeneratedSql(
                sql="SELECT c.customer_id, c.full_name, c.credit_score, a.account_id, a.status FROM bank.customers c JOIN bank.accounts a ON a.customer_id = c.customer_id WHERE c.credit_score < 600 AND a.status = 'ACTIVE' ORDER BY c.customer_id LIMIT 10",
                rationale="Attempting to filter customers and active accounts with credit score below 600.",
                assumptions=["c.credit_score is directly available on customers table"],
                confidence=0.75,
            )

        # Chip 1: "Which branches have the highest loan delinquency this quarter?"
        if "highest loan delinquency" in q_lower or "delinquency this quarter" in q_lower or "delinquen" in q_lower:
            return GeneratedSql(
                sql="""SELECT b.name AS branch_name,
       COUNT(DISTINCT l.loan_id) AS total_loans,
       COUNT(DISTINCT CASE WHEN r.days_past_due >= 30 THEN l.loan_id END) AS delinquent_loans,
       ROUND(CAST(COUNT(DISTINCT CASE WHEN r.days_past_due >= 30 THEN l.loan_id END) * 100.0 / NULLIF(COUNT(DISTINCT l.loan_id), 0) AS NUMERIC), 2) AS delinquency_rate_pct
FROM bank.branches b
JOIN bank.customers c ON c.branch_id = b.branch_id
JOIN bank.loans l ON l.customer_id = c.customer_id
JOIN bank.repayments r ON r.loan_id = l.loan_id
GROUP BY b.branch_id, b.name
ORDER BY delinquency_rate_pct DESC
LIMIT 10""",
                rationale="Aggregates loans and repayments with days_past_due >= 30 grouped by branch location.",
                assumptions=["Delinquent means days_past_due >= 30 per business glossary."],
                confidence=0.98,
            )

        # Chip 2: "Show the monthly repayment rate for the last 12 months"
        if "monthly repayment" in q_lower or "repayment rate" in q_lower:
            return GeneratedSql(
                sql="""SELECT SUBSTR(due_date, 1, 7) AS repayment_month,
       ROUND(SUM(amount_due), 2) AS total_due,
       ROUND(SUM(amount_paid), 2) AS total_paid,
       ROUND(CAST(SUM(amount_paid) * 100.0 / NULLIF(SUM(amount_due), 0) AS NUMERIC), 2) AS collection_rate_pct
FROM bank.repayments
GROUP BY SUBSTR(due_date, 1, 7)
ORDER BY repayment_month DESC
LIMIT 12""",
                rationale="Groups repayment collection efficiency by calendar month over the past 12 months.",
                assumptions=["Repayment rate is calculated as total paid vs total due."],
                confidence=0.97,
            )

        # Chip 3: "Credit tier distribution of active customers"
        if "credit tier" in q_lower or "tier distribution" in q_lower:
            return GeneratedSql(
                sql="""SELECT ct.name AS tier_name,
       COUNT(DISTINCT c.customer_id) AS customer_count
FROM bank.credit_tiers ct
JOIN bank.credit_scores cs ON cs.tier_id = ct.tier_id
JOIN bank.customers c ON c.customer_id = cs.customer_id
JOIN bank.accounts a ON a.customer_id = c.customer_id
WHERE a.status = 'ACTIVE'
GROUP BY ct.tier_id, ct.name
ORDER BY ct.tier_id ASC
LIMIT 10""",
                rationale="Counts active customers across credit tiers A through E.",
                assumptions=["Active customer defined as having at least one active account."],
                confidence=0.99,
            )

        # Reconciliation: Mismatch between ledger and account balance
        if "reconciliation" in q_lower or "mismatch" in q_lower or "discrepancy" in q_lower:
            return GeneratedSql(
                sql="""SELECT a.account_id,
       c.full_name AS customer_name,
       a.balance AS account_balance,
       le.credit AS ledger_balance,
       ROUND(CAST(a.balance - le.credit AS NUMERIC), 2) AS variance
FROM bank.accounts a
JOIN bank.customers c ON c.customer_id = a.customer_id
JOIN bank.ledger_entries le ON le.account_id = a.account_id
WHERE ABS(a.balance - le.credit) > 0.01
ORDER BY ABS(a.balance - le.credit) DESC
LIMIT 15""",
                rationale="Identifies customer accounts with variance between current balance and general ledger credits.",
                assumptions=["Reconciliation threshold set to 1 paisa (0.01 INR)."],
                confidence=0.98,
            )

        # Generic Fallback: Active customers and accounts listing
        return GeneratedSql(
            sql="""SELECT c.customer_id,
       c.full_name,
       c.city,
       a.account_id,
       a.status AS account_status,
       a.balance
FROM bank.customers c
JOIN bank.accounts a ON a.customer_id = c.customer_id
WHERE a.status = 'ACTIVE'
ORDER BY a.balance DESC
LIMIT 10""",
            rationale="Retrieves highest-balance active customer accounts.",
            assumptions=["Sorted by account balance descending."],
            confidence=0.92,
        )

    async def repair_sql(self, question: str, context: Any, attempts: list[Any]) -> GeneratedSql:
        self.repair_count += 1
        q_lower = question.lower()

        # Repaired query for the credit score below 600 prompt:
        # Replaces c.credit_score with JOIN bank.credit_scores cs ON cs.customer_id = c.customer_id
        return GeneratedSql(
            sql="""SELECT c.customer_id,
       c.full_name,
       cs.score AS credit_score,
       a.account_id,
       a.status AS account_status
FROM bank.customers c
JOIN bank.accounts a ON a.customer_id = c.customer_id
JOIN bank.credit_scores cs ON cs.customer_id = c.customer_id
WHERE cs.score < 600 AND a.status = 'ACTIVE'
ORDER BY cs.score ASC
LIMIT 10""",
            rationale="Repaired schema reference: joined credit_scores table on customer_id instead of accessing c.credit_score.",
            assumptions=["Credit scores are tracked in credit_scores table linked by customer_id."],
            confidence=0.99,
        )

    async def narrate(self, question: str, stats: dict[str, Any]) -> NarrativeResult:
        row_count = stats.get("row_count", 0)
        q_lower = question.lower()

        if "delinquen" in q_lower:
            return NarrativeResult(
                insight_text="Portfolio analysis reveals elevated delinquency concentrated in Tier-2 urban branches, with peak non-performing rates exceeding 8.4%. Priority remediation workflows recommended for commercial accounts.",
                read_as="Ranked branch offices by proportion of loan repayments overdue 30+ days.",
                flags=["HIGH_DELINQUENCY_ALERT"]
            )
        elif "repayment" in q_lower:
            return NarrativeResult(
                insight_text="Collection rates remained resilient across the preceding 12 months, maintaining an average recovery velocity of 91.2% with marginal dips in festive quarters.",
                read_as="Aggregated monthly collection efficiency and total installments paid versus due.",
                flags=[]
            )
        elif "tier" in q_lower:
            return NarrativeResult(
                insight_text="Prime and Good credit tiers (A and B) represent 64% of active customer relationships, indicating strong aggregate portfolio creditworthiness.",
                read_as="Distribution of verified customers across credit risk rating bands A to E.",
                flags=[]
            )
        elif "reconciliation" in q_lower:
            return NarrativeResult(
                insight_text="Discrepancy audit identified ledger variance on designated test accounts. Sub-ledger balances require adjustment against posting journals.",
                read_as="Accounts where core banking balance differs from general ledger liability postings.",
                flags=["RECONCILIATION_MISMATCH"]
            )

        return NarrativeResult(
            insight_text=f"Query successfully returned {row_count} matching records meeting the specified criteria.",
            read_as="Evaluated natural language filters against primary banking schemas.",
            flags=[]
        )
