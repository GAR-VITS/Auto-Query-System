import type { AgentStatus } from '@/types'

interface StatusIndicatorProps {
  status: AgentStatus
  label?: string
}

const statusConfig: Record<AgentStatus, { color: string; label: string }> = {
  idle: { color: 'bg-slate-500', label: 'Idle' },
  running: { color: 'bg-cyan-400', label: 'Running' },
  success: { color: 'bg-emerald-400', label: 'Success' },
  error: { color: 'bg-red-400', label: 'Error' },
  correcting: { color: 'bg-amber-400', label: 'Self-Correcting' },
}

export function StatusIndicator({ status, label }: StatusIndicatorProps) {
  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {status === 'running' || status === 'correcting' ? (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${config.color}`}
          />
        ) : null}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${config.color}`} />
      </span>
      <span className="text-xs font-medium text-slate-400">
        {label ?? config.label}
      </span>
    </div>
  )
}
