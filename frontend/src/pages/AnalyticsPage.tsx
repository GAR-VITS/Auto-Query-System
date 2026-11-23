import { ChartPanel } from '@/components/charts/ChartPanel'
import { Card } from '@/components/common/Card'
import { chartConfigs } from '@/data/mockData'

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <Card className="border-amber-500/20 bg-amber-500/5">
        <p className="text-sm text-slate-300">
          <span className="font-semibold text-amber-400">Visualization Agent</span> — Charts are
          auto-generated from query results in Phase II. Below are sample enterprise analytics.
        </p>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {chartConfigs.map((config) => (
          <ChartPanel key={config.title} config={config} />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Avg Query Latency', value: '142ms' },
          { label: 'Self-Correction Rate', value: '9.2%' },
          { label: 'Agent Success Rate', value: '98.0%' },
        ].map((metric) => (
          <Card key={metric.label} className="text-center">
            <p className="text-xs uppercase tracking-wider text-slate-500">{metric.label}</p>
            <p className="mt-2 text-2xl font-bold text-accent-400">{metric.value}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
