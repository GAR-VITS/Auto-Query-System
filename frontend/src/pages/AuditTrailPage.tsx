import { AuditLogTable } from '@/components/audit/AuditLogTable'
import { Card } from '@/components/common/Card'
import { auditEntries } from '@/data/mockData'
import { ShieldCheck, FileText, Lock } from 'lucide-react'

export function AuditTrailPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { icon: ShieldCheck, label: 'Total Events', value: auditEntries.length, color: 'text-emerald-400' },
          { icon: FileText, label: 'Pending Approvals', value: 1, color: 'text-amber-400' },
          { icon: Lock, label: 'RBAC Violations', value: 0, color: 'text-cyan-400' },
        ].map(({ icon: Icon, label, value, color }) => (
          <Card key={label} className="flex items-center gap-4">
            <div className={`rounded-xl bg-surface-700/50 p-3 ${color}`}>
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs text-slate-500">{label}</p>
              <p className="text-2xl font-bold text-slate-100">{value}</p>
            </div>
          </Card>
        ))}
      </div>

      <AuditLogTable entries={auditEntries} />
    </div>
  )
}
