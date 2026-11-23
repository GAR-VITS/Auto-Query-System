import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { Card } from '@/components/common/Card'
import type { ChartConfig } from '@/types'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#94a3b8', font: { size: 11 } },
    },
  },
  scales: {
    x: {
      ticks: { color: '#64748b', font: { size: 10 } },
      grid: { color: 'rgba(51, 65, 85, 0.3)' },
    },
    y: {
      ticks: { color: '#64748b', font: { size: 10 } },
      grid: { color: 'rgba(51, 65, 85, 0.3)' },
    },
  },
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: { color: '#94a3b8', font: { size: 11 }, padding: 16 },
    },
  },
}

interface ChartPanelProps {
  config: ChartConfig
}

export function ChartPanel({ config }: ChartPanelProps) {
  const data = {
    labels: config.labels,
    datasets: config.datasets.map((ds) => ({
      ...ds,
      borderWidth: config.type === 'line' ? 2 : 1,
      fill: config.type === 'line',
      tension: 0.4,
    })),
  }

  return (
    <Card>
      <h4 className="mb-4 text-sm font-semibold text-slate-300">{config.title}</h4>
      <div className="h-64">
        {config.type === 'bar' && <Bar data={data} options={chartOptions} />}
        {config.type === 'line' && <Line data={data} options={chartOptions} />}
        {config.type === 'doughnut' && <Doughnut data={data} options={doughnutOptions} />}
      </div>
    </Card>
  )
}
