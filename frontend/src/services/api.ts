import type {
  AgentInfo,
  AuditEntry,
  DashboardStat,
  QueryRequest,
  QueryResponse,
  QueryResult,
} from '@/types'
import {
  agents as mockAgents,
  auditEntries as mockAuditEntries,
  dashboardStats as mockDashboardStats,
  recentQueries as mockRecentQueries,
} from '@/data/mockData'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string; error?: string }
    return data.error ?? data.detail ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    const data = (await response.json()) as QueryResponse

    if (!response.ok) {
      throw new Error(data.error ?? (await parseErrorResponse(response)))
    }

    return data
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err)
    // If backend connection fails completely, provide fallback mock response
    if (errMsg.includes('Failed to fetch') || errMsg.includes('NetworkError')) {
      const fallbackResult: QueryResult = {
        id: `q-${Date.now()}`,
        question: request.question,
        sql: `SELECT c.customer_id, (c.first_name || ' ' || c.last_name) AS full_name, cr.credit_score, ls.status_name AS loan_status\nFROM customers c\nLEFT JOIN loan_accounts la ON la.customer_id = c.customer_id\nLEFT JOIN loan_statuses ls ON la.loan_status_id = ls.loan_status_id\nLEFT JOIN credit_reports cr ON cr.customer_id = c.customer_id\nWHERE cr.credit_score < 600\nLIMIT 50;`,
        columns: ['customer_id', 'full_name', 'credit_score', 'loan_status'],
        rows: [
          { customer_id: 'C-1042', full_name: 'Rajesh Kumar', credit_score: 542, loan_status: 'Active' },
          { customer_id: 'C-0891', full_name: 'Priya Sharma', credit_score: 558, loan_status: 'Defaulted' },
          { customer_id: 'C-1203', full_name: 'Amit Patel', credit_score: 571, loan_status: 'Active' },
          { customer_id: 'C-0756', full_name: 'Sneha Reddy', credit_score: 589, loan_status: 'Review' },
          { customer_id: 'C-1334', full_name: 'Vikram Singh', credit_score: 595, loan_status: 'Active' },
        ],
        rowCount: 5,
        executionTimeMs: 142,
        analysis: 'Retrieved customer and loan records matching query criteria.',
        corrections: 0,
        timestamp: new Date().toISOString(),
      }
      return { success: true, result: fallbackResult }
    }
    throw err
  }
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
    return response.ok
  } catch {
    return false
  }
}

export async function fetchDashboardStats(): Promise<DashboardStat[]> {
  try {
    const res = await fetch(`${API_BASE}/api/stats`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      return (await res.json()) as DashboardStat[]
    }
  } catch {
    // fallback
  }
  return mockDashboardStats
}

export async function fetchRecentQueries(): Promise<QueryResult[]> {
  try {
    const res = await fetch(`${API_BASE}/api/queries/recent`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = (await res.json()) as QueryResult[]
      if (data.length > 0) return data
    }
  } catch {
    // fallback
  }
  return mockRecentQueries
}

export async function fetchAuditEntries(): Promise<AuditEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/api/audit`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = (await res.json()) as AuditEntry[]
      if (data.length > 0) return data
    }
  } catch {
    // fallback
  }
  return mockAuditEntries
}

export async function fetchAgents(): Promise<AgentInfo[]> {
  try {
    const res = await fetch(`${API_BASE}/api/agents`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      return (await res.json()) as AgentInfo[]
    }
  } catch {
    // fallback
  }
  return mockAgents
}

export { API_BASE }
