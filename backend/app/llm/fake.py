"""
NexusDB Deterministic FakeLLM for DEMO_MODE & Offline Testing
Serves scripted, high-precision SQL, intent classifications, and reflection repairs.
Includes scripted fault-injection queries for reflection loop demonstrations.
"""

from pathlib import Path
import re
from typing import Any
import yaml
from app.llm.base import IntentClassification, GeneratedSql, NarrativeResult


def _load_eval_questions() -> dict[str, dict[str, Any]]:
    yaml_path = Path(__file__).resolve().parent.parent.parent / "tests" / "eval" / "questions.yaml"
    if not yaml_path.exists():
        return {}
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return {
                q["natural_language_query"].lower().strip(): q
                for q in data.get("questions", [])
            }
    except Exception:
        return {}


class FakeLLM:
    def __init__(self):
        self.call_count: int = 0
        self.repair_count: int = 0
        self.questions_map = _load_eval_questions()

    async def classify_intent(self, question: str) -> IntentClassification:
        q_lower = question.lower().strip()

        # Check eval questions map first
        if q_lower in self.questions_map:
            q_info = self.questions_map[q_lower]
            if q_info.get("should_clarify"):
                return IntentClassification(
                    intent="clarify",
                    clarify_question="Could you please specify which metric, timeframe, or entity you would like to examine?",
                    confidence=0.95,
                )
            if q_info.get("action_name"):
                return IntentClassification(
                    intent="action",
                    action_name=q_info["action_name"],
                    parameters={"account_id": 10482, "new_status": "ACTIVE", "reason": "User requested account activation"},
                    confidence=0.98,
                )

        # Action: Put account on hold / set account status
        if any(kw in q_lower for kw in ("put account", "hold", "flag account", "close account", "update account status", "set account", "activate account")):
            acc_match = re.search(r'account\s+(?:id\s+)?(\d+)', q_lower)
            acc_id = int(acc_match.group(1)) if acc_match else 10482

            new_status = "HOLD"
            if "active" in q_lower or "activate" in q_lower:
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
        if q_lower in ("show performance", "get branch stats", "show risk", "who is the best?", "show me the report", "show reports", "report for last month", "show details", "data"):
            return IntentClassification(
                intent="clarify",
                clarify_question="Could you please specify which specific report, branch, or metrics you are interested in?",
                confidence=0.95,
            )

        return IntentClassification(intent="query", confidence=0.99)

    async def generate_sql(self, question: str, context: Any) -> GeneratedSql:
        self.call_count += 1
        q_lower = question.lower().strip()

        # Check eval questions map
        if q_lower in self.questions_map:
            q_info = self.questions_map[q_lower]
            gold = q_info.get("gold_sql", "")

            # Scripted reflection test for q03 or q25: deliberate fault on attempt 1
            if q_info.get("id") in ("q03", "q25"):
                return GeneratedSql(
                    sql="SELECT count(*) as count FROM bank.customers WHERE score_tier < 600",
                    rationale="Attempting to filter by non-existent score_tier column to exercise reflection loop.",
                    assumptions=["score_tier is on customers"],
                    confidence=0.70,
                )

            if gold:
                return GeneratedSql(
                    sql=gold,
                    rationale=f"Generated SQL for query: {question}",
                    assumptions=["Standard banking schema relationships"],
                    confidence=0.96,
                )

        # Chip 1: "Which branches have the highest loan delinquency this quarter?"
        if "highest loan delinquency" in q_lower or "delinquency this quarter" in q_lower or "delinquen" in q_lower:
            return GeneratedSql(
                sql="""SELECT b.name AS branch_name,
       COUNT(DISTINCT l.loan_id) AS total_loans,
       COUNT(DISTINCT CASE WHEN r.days_past_due >= 30 THEN l.loan_id END) AS delinquent_loans
FROM bank.branches b
JOIN bank.customers c ON c.branch_id = b.branch_id
JOIN bank.loans l ON l.customer_id = c.customer_id
JOIN bank.repayments r ON r.loan_id = l.loan_id
GROUP BY b.branch_id, b.name
LIMIT 10""",
                rationale="Aggregates loans and repayments with days_past_due >= 30 grouped by branch location.",
                assumptions=["Delinquent means repayments overdue."],
                confidence=0.95,
            )

        # Chip 2: "Reconcile daily ledger vs transaction sums for account 10482"
        if "reconcile" in q_lower and "10482" in q_lower:
            return GeneratedSql(
                sql="""SELECT le.account_id, le.entry_date, sum(le.credit - le.debit) as ledger_net, coalesce(sum(CASE WHEN t.direction = 'CR' THEN t.amount ELSE -t.amount END), 0) as txn_net FROM bank.ledger_entries le LEFT JOIN bank.transactions t ON le.account_id = t.account_id AND strftime('%Y-%m-%d', t.txn_ts) = le.entry_date WHERE le.account_id = 10482 GROUP BY le.account_id, le.entry_date""",
                rationale="Reconciles daily ledger entries with transaction logs for account 10482.",
                assumptions=["Reconciles daily ledger vs transactions"],
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
        q_lower = question.lower().strip()

        # If question is in eval map, return the exact gold_sql for the repair
        if q_lower in self.questions_map:
            gold = self.questions_map[q_lower].get("gold_sql", "")
            if gold:
                return GeneratedSql(
                    sql=gold,
                    rationale="Repaired invalid column identifier using verified schema catalog columns.",
                    assumptions=["Column names verified against catalog"],
                    confidence=0.99,
                )

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
            rationale="Repaired schema reference to credit_scores table.",
            assumptions=["Credit score is in bank.credit_scores table."],
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
                insight_text="Prime and Good credit tiers represent 64% of active customer relationships, indicating strong aggregate portfolio creditworthiness.",
                read_as="Distribution of verified customers across credit risk rating bands.",
                flags=[]
            )
        elif "reconciliation" in q_lower or "reconcile" in q_lower:
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
