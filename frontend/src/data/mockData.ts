import type {
  AgentInfo,
  AuditEntry,
  ChartConfig,
  DashboardStat,
  QueryResult,
} from '@/types'

export const dashboardStats: DashboardStat[] = [
  { label: 'Queries Today', value: 247, change: '+18%', trend: 'up' },
  { label: 'Auto-Corrections', value: 12, change: '-3%', trend: 'down' },
  { label: 'Active Loans', value: '14,832', change: '+2.4%', trend: 'up' },
  { label: 'Audit Events', value: 89, change: '+5', trend: 'neutral' },
]

export const agents: AgentInfo[] = [
  {
    id: 'query',
    name: 'Query Agent',
    description: 'Translates NL to SQL & self-corrects syntax errors',
    status: 'idle',
    lastRun: '2 min ago',
  },
  {
    id: 'analysis',
    name: 'Analysis Agent',
    description: 'Evaluates results with Pandas & plain-English summaries',
    status: 'idle',
    lastRun: '5 min ago',
  },
  {
    id: 'visualization',
    name: 'Visualization Agent',
    description: 'Builds interactive charts from query output',
    status: 'idle',
    lastRun: '12 min ago',
  },
]

export const recentQueries: QueryResult[] = [
  {
    id: 'q1',
    question: 'Show customers with credit score below 600',
    sql: `SELECT customer_id, full_name, credit_score, loan_status
FROM customers c
JOIN loan_accounts l ON c.id = l.customer_id
WHERE credit_score < 600
ORDER BY credit_score ASC
LIMIT 50;`,
    columns: ['customer_id', 'full_name', 'credit_score', 'loan_status'],
    rows: [
      { customer_id: 'C-1042', full_name: 'Rajesh Kumar', credit_score: 542, loan_status: 'active' },
      { customer_id: 'C-0891', full_name: 'Priya Sharma', credit_score: 558, loan_status: 'default' },
      { customer_id: 'C-1203', full_name: 'Amit Patel', credit_score: 571, loan_status: 'active' },
      { customer_id: 'C-0756', full_name: 'Sneha Reddy', credit_score: 589, loan_status: 'review' },
      { customer_id: 'C-1334', full_name: 'Vikram Singh', credit_score: 595, loan_status: 'active' },
    ],
    rowCount: 5,
    executionTimeMs: 142,
    analysis:
      'Found 5 customers below the 600 credit threshold. 1 account is in default status and 1 is under review. Recommend flagging C-0891 for immediate follow-up.',
    corrections: 0,
    timestamp: '2026-08-07T09:45:00Z',
  },
  {
    id: 'q2',
    question: 'Top defaulters by outstanding amount',
    sql: `SELECT customer_id, outstanding_amount, days_overdue
FROM loan_accounts
WHERE status = 'default'
ORDER BY outstanding_amount DESC
LIMIT 10;`,
    columns: ['customer_id', 'outstanding_amount', 'days_overdue'],
    rows: [
      { customer_id: 'C-0891', outstanding_amount: 845000, days_overdue: 127 },
      { customer_id: 'C-0445', outstanding_amount: 620000, days_overdue: 89 },
      { customer_id: 'C-2109', outstanding_amount: 510000, days_overdue: 45 },
    ],
    rowCount: 3,
    executionTimeMs: 98,
    corrections: 1,
    timestamp: '2026-08-07T09:30:00Z',
  },
]

export const auditEntries: AuditEntry[] = [
  {
    id: 'a1',
    timestamp: '2026-08-07T09:46:12Z',
    action: 'query_executed',
    status: 'auto_executed',
    agent: 'query',
    user: 'analyst@enterprise.com',
    description: 'NL query: customers with credit score below 600',
    reasoning: 'Read-only SELECT query passed RBAC validation. No write operations detected.',
    affectedRecords: 5,
  },
  {
    id: 'a2',
    timestamp: '2026-08-07T09:40:00Z',
    action: 'defaulter_flagged',
    status: 'approved',
    agent: 'analysis',
    user: 'manager@enterprise.com',
    description: 'Flagged C-0891 as high-risk defaulter',
    reasoning: 'Credit score 558, 127 days overdue, outstanding ₹8.45L. Rule R-042 triggered automatic flag.',
    affectedRecords: 1,
  },
  {
    id: 'a3',
    timestamp: '2026-08-07T09:15:00Z',
    action: 'credit_evaluation',
    status: 'pending',
    agent: 'analysis',
    user: 'system',
    description: 'Automated credit evaluation for loan application LA-9921',
    reasoning: 'Applicant score 612, debt-to-income 0.38. Awaiting manager approval per policy POL-018.',
  },
  {
    id: 'a4',
    timestamp: '2026-08-07T08:55:00Z',
    action: 'loan_approved',
    status: 'approved',
    agent: 'system',
    user: 'admin@enterprise.com',
    description: 'Approved loan LA-9918 for ₹3.2L',
    reasoning: 'All validation rules passed: score 720, income verified, collateral attached.',
    affectedRecords: 1,
  },
  {
    id: 'a5',
    timestamp: '2026-08-07T08:30:00Z',
    action: 'query_executed',
    status: 'auto_executed',
    agent: 'query',
    user: 'analyst@enterprise.com',
    description: 'Self-corrected SQL after syntax error (attempt 2)',
    reasoning: 'Initial query failed on JOIN clause. Agent loop rewrote query using schema context from ChromaDB.',
    affectedRecords: 3,
  },
]

export const chartConfigs: ChartConfig[] = [
  {
    type: 'bar',
    title: 'Loan Distribution by Risk Tier',
    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical'],
    datasets: [
      {
        label: 'Active Loans',
        data: [6200, 4100, 2800, 1732],
        backgroundColor: ['#34d399', '#22d3ee', '#fbbf24', '#f87171'],
      },
    ],
  },
  {
    type: 'line',
    title: 'Monthly Repayment Rate (%)',
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    datasets: [
      {
        label: 'Repayment Rate',
        data: [94.2, 93.8, 95.1, 94.5, 93.2, 94.8, 95.6],
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34, 211, 238, 0.1)',
      },
    ],
  },
  {
    type: 'doughnut',
    title: 'Query Agent Success Rate',
    labels: ['First Attempt', 'Self-Corrected', 'Failed'],
    datasets: [
      {
        label: 'Queries',
        data: [89, 9, 2],
        backgroundColor: ['#34d399', '#fbbf24', '#f87171'],
      },
    ],
  },
]

export function mockQueryResponse(question: string): QueryResult {
  const base = recentQueries[0]
  return {
    ...base,
    id: `q-${Date.now()}`,
    question,
    timestamp: new Date().toISOString(),
    executionTimeMs: Math.floor(Math.random() * 200) + 80,
    corrections: Math.random() > 0.7 ? 1 : 0,
  }
}
