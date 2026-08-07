import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, Zap } from 'lucide-react'
import { StatCard } from '@/components/dashboard/StatCard'
import { AgentStatusPanel } from '@/components/dashboard/AgentStatusPanel'
import { RecentQueries } from '@/components/dashboard/RecentQueries'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { dashboardStats, agents, recentQueries } from '@/data/mockData'
import { APP_TAGLINE } from '@/constants/navigation'

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-accent-500/20 bg-gradient-to-r from-accent-500/10 via-surface-800/80 to-indigo-500/10 p-6"
      >
        <div className="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Welcome to <span className="gradient-text">NexusDB</span>
            </h1>
            <p className="mt-1 max-w-xl text-sm text-slate-400">{APP_TAGLINE}</p>
          </div>
          <Link to="/query">
            <Button icon={<Zap className="h-4 w-4" />}>
              Start Querying <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
        <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-accent-500/10 blur-3xl" />
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardStats.map((stat, i) => (
          <StatCard key={stat.label} stat={stat} index={i} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <AgentStatusPanel agents={agents} />
        </div>
        <div className="lg:col-span-3">
          <RecentQueries queries={recentQueries} />
        </div>
      </div>

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Project Roadmap
        </h3>
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { phase: 'Phase I', title: 'NL-to-SQL Pipeline', status: 'Active', desc: 'Gemini + LangChain + React dashboard' },
            { phase: 'Phase II', title: 'Multi-Agent Intelligence', status: 'Planned', desc: 'CrewAI agents, self-correction, ChromaDB' },
            { phase: 'Phase III', title: 'Secure Automation', status: 'Planned', desc: 'RBAC, voice input, audit trails' },
          ].map((item) => (
            <div
              key={item.phase}
              className="rounded-xl border border-surface-600/30 bg-surface-800/30 p-4"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-accent-400">
                  {item.phase}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    item.status === 'Active'
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-surface-600/40 text-slate-500'
                  }`}
                >
                  {item.status}
                </span>
              </div>
              <p className="mt-2 text-sm font-semibold text-slate-200">{item.title}</p>
              <p className="mt-1 text-xs text-slate-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
