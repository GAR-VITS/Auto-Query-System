import { Bot, Brain, BarChart2 } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { StatusIndicator } from '@/components/common/StatusIndicator'
import { AGENT_COLORS } from '@/constants/navigation'
import type { AgentInfo } from '@/types'

const agentIcons = {
  query: Bot,
  analysis: Brain,
  visualization: BarChart2,
}

interface AgentStatusPanelProps {
  agents: AgentInfo[]
}

export function AgentStatusPanel({ agents }: AgentStatusPanelProps) {
  return (
    <Card>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
        Multi-Agent System
      </h3>
      <div className="space-y-3">
        {agents.map((agent) => {
          const Icon = agentIcons[agent.id]
          const color = AGENT_COLORS[agent.id]

          return (
            <div
              key={agent.id}
              className="flex items-center gap-4 rounded-xl border border-surface-600/30 bg-surface-800/40 p-3 transition hover:border-surface-500/50"
            >
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                style={{ backgroundColor: `${color}20`, color }}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-200">{agent.name}</p>
                <p className="truncate text-xs text-slate-500">{agent.description}</p>
              </div>
              <div className="text-right">
                <StatusIndicator status={agent.status} />
                {agent.lastRun && (
                  <p className="mt-1 text-[10px] text-slate-600">{agent.lastRun}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
