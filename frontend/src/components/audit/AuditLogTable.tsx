import { Shield, Clock, User, Bot } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import type { AuditEntry } from '@/types'

interface AuditLogTableProps {
  entries: AuditEntry[]
}

const actionLabels: Record<AuditEntry['action'], string> = {
  query_executed: 'Query Executed',
  credit_evaluation: 'Credit Evaluation',
  defaulter_flagged: 'Defaulter Flagged',
  loan_approved: 'Loan Approved',
  status_updated: 'Status Updated',
}

const statusVariant: Record<AuditEntry['status'], 'success' | 'warning' | 'danger' | 'info'> = {
  approved: 'success',
  pending: 'warning',
  rejected: 'danger',
  auto_executed: 'info',
}

export function AuditLogTable({ entries }: AuditLogTableProps) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="flex items-center gap-2 border-b border-surface-600/40 px-5 py-4">
        <Shield className="h-5 w-5 text-emerald-400" />
        <h3 className="text-sm font-semibold text-slate-200">Compliance Audit Trail</h3>
        <span className="ml-auto text-xs text-slate-500">{entries.length} events</span>
      </div>

      <div className="divide-y divide-surface-600/30">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="px-5 py-4 transition hover:bg-surface-800/40"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant={statusVariant[entry.status]}>
                  {entry.status.replace('_', ' ')}
                </Badge>
                <span className="text-sm font-medium text-slate-200">
                  {actionLabels[entry.action]}
                </span>
              </div>
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Clock className="h-3 w-3" />
                {new Date(entry.timestamp).toLocaleString()}
              </div>
            </div>

            <p className="mt-2 text-sm text-slate-400">{entry.description}</p>

            <div className="mt-3 rounded-lg border border-surface-600/30 bg-surface-900/50 p-3">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Agent Reasoning
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-400">{entry.reasoning}</p>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Bot className="h-3 w-3" />
                {entry.agent} agent
              </span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {entry.user}
              </span>
              {entry.affectedRecords !== undefined && (
                <span>{entry.affectedRecords} record(s) affected</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
