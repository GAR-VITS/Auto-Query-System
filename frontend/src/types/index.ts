export type UserRole = 'admin' | 'analyst' | 'manager' | 'viewer'

export type AgentType = 'query' | 'analysis' | 'visualization'

export type AgentStatus = 'idle' | 'running' | 'success' | 'error' | 'correcting'

export type AuditActionType =
  | 'query_executed'
  | 'credit_evaluation'
  | 'defaulter_flagged'
  | 'loan_approved'
  | 'status_updated'

export type AuditStatus = 'approved' | 'pending' | 'rejected' | 'auto_executed'

export interface AgentInfo {
  id: AgentType
  name: string
  description: string
  status: AgentStatus
  lastRun?: string
}

export interface QueryResult {
  id: string
  question: string
  sql: string
  rows: Record<string, string | number>[]
  columns: string[]
  rowCount: number
  executionTimeMs: number
  analysis?: string
  corrections?: number
  timestamp: string
}

export interface AuditEntry {
  id: string
  timestamp: string
  action: AuditActionType
  status: AuditStatus
  agent: AgentType | 'system'
  user: string
  description: string
  reasoning: string
  affectedRecords?: number
}

export interface DashboardStat {
  label: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'doughnut'
  title: string
  labels: string[]
  datasets: ChartDataset[]
}

export interface NavItem {
  path: string
  label: string
  icon: string
  description?: string
}

export interface QueryRequest {
  question: string
  voice?: boolean
}

export interface QueryResponse {
  success: boolean
  result?: QueryResult
  error?: string
}
