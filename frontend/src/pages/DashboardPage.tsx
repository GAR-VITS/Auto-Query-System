import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, Zap } from 'lucide-react'
import { StatCard } from '@/components/dashboard/StatCard'
import { AgentStatusPanel } from '@/components/dashboard/AgentStatusPanel'
import { RecentQueries } from '@/components/dashboard/RecentQueries'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { dashboardStats as initialStats, agents as initialAgents, recentQueries as initialQueries } from '@/data/mockData'
import { fetchDashboardStats, fetchAgents, fetchRecentQueries } from '@/services/api'
import { APP_TAGLINE } from '@/constants/navigation'
import type { DashboardStat, AgentInfo, QueryResult } from '@/types'

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStat[]>(initialStats)
  const [agentList, setAgentList] = useState<AgentInfo[]>(initialAgents)
  const [queries, setQueries] = useState<QueryResult[]>(initialQueries)

  useEffect(() => {
    let active = true

    const loadLiveData = async () => {
      try {
        const [liveStats, liveAgents, liveQueries] = await Promise.all([
          fetchDashboardStats(),
          fetchAgents(),
          fetchRecentQueries(),
        ])
        if (active) {
          if (liveStats && liveStats.length > 0) setStats(liveStats)
          if (liveAgents && liveAgents.length > 0) setAgentList(liveAgents)
          if (liveQueries && liveQueries.length > 0) setQueries(liveQueries)
        }
      } catch {
        // use initial mock states
      }
    }

    loadLiveData()

    return () => {
      active = false
    }
  }, [])

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
        {stats.map((stat, i) => (
          <StatCard key={stat.label} stat={stat} index={i} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <AgentStatusPanel agents={agentList} />
        </div>
        <div className="lg:col-span-3">
          <RecentQueries queries={queries} />
        </div>
      </div>

      <Card>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Project Architecture & Pipeline
        </h3>
        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { phase: 'Natural Language Engine', title: 'NL-to-SQL Agent Pipeline', status: 'Connected', desc: 'Gemini 2.5 Flash + PostgreSQL & SQLite local database' },
            { phase: 'Self-Correction Loop', title: 'Error-Driven Reflection', status: 'Connected', desc: 'Autonomous multi-turn SQL error recovery and validation' },
            { phase: 'Enterprise Compliance', title: 'Audit Trail & RBAC', status: 'Active', desc: 'Read-only safety guardrails and autonomous action logging' },
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
                  className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-medium text-emerald-400"
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
