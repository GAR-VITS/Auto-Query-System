import { motion } from 'framer-motion'
import { TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { Card } from '@/components/common/Card'
import type { DashboardStat } from '@/types'

interface StatCardProps {
  stat: DashboardStat
  index: number
}

export function StatCard({ stat, index }: StatCardProps) {
  const TrendIcon =
    stat.trend === 'up' ? TrendingUp : stat.trend === 'down' ? TrendingDown : Minus

  const trendColor =
    stat.trend === 'up'
      ? 'text-emerald-400'
      : stat.trend === 'down'
        ? 'text-red-400'
        : 'text-slate-500'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="relative overflow-hidden">
        <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-accent-500/5" />
        <p className="text-sm font-medium text-slate-400">{stat.label}</p>
        <p className="mt-2 text-3xl font-bold tracking-tight text-slate-100">{stat.value}</p>
        {stat.change && (
          <div className={`mt-2 flex items-center gap-1 text-xs font-medium ${trendColor}`}>
            <TrendIcon className="h-3.5 w-3.5" />
            {stat.change}
          </div>
        )}
      </Card>
    </motion.div>
  )
}
