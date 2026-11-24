import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { formatNumber } from '../lib/format';
import { useSessionStore } from '../store/session';

// Register ChartJS plugins
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface VizSpec {
  chart_type: 'bar' | 'line' | 'doughnut' | 'kpi' | 'none';
  title?: string;
  x_axis?: string;
  y_axis?: string;
  series?: Array<{
    name?: string;
    data: any[];
  }>;
  labels?: string[];
  kpi?: {
    value: string | number;
    label: string;
    sublabel?: string;
  };
}

interface ChartCardProps {
  viz: VizSpec;
}

export const ChartCard: React.FC<ChartCardProps> = ({ viz }) => {
  const theme = useSessionStore((s) => s.theme);
  const isDark = theme === 'dark';

  // Palette tokens
  const colors = useMemo(() => {
    if (isDark) {
      return {
        accent: '#D98A94',
        accentSoft: 'rgba(217, 138, 148, 0.25)',
        secondary: '#D9A24A',
        green: '#6FB08F',
        ink: '#F2EEE8',
        ink3: '#6F6A63',
        line: '#2A2724',
        palette: ['#D98A94', '#D9A24A', '#6FB08F', '#A8A29A', '#818CF8', '#38BDF8'],
      };
    }
    return {
      accent: '#7A1F2B',
      accentSoft: 'rgba(122, 31, 43, 0.15)',
      secondary: '#A66A12',
      green: '#2F6B4F',
      ink: '#1A1816',
      ink3: '#9A958D',
      line: '#E7E2DA',
      palette: ['#7A1F2B', '#A66A12', '#2F6B4F', '#5C5852', '#4F46E5', '#0284C7'],
    };
  }, [isDark]);

  if (!viz || viz.chart_type === 'none') {
    return null;
  }

  // 1. KPI Metric Card
  if (viz.chart_type === 'kpi' && viz.kpi) {
    return (
      <div className="w-full border border-line rounded-lg p-6 bg-surface flex flex-col items-center justify-center text-center shadow-xs">
        <span className="font-mono text-xs uppercase tracking-wider text-ink-3 mb-2 font-medium">
          {viz.kpi.label || viz.title || 'Summary Metric'}
        </span>
        <div className="font-serif text-4xl sm:text-5xl font-normal text-ink tracking-tight mb-2">
          {typeof viz.kpi.value === 'number'
            ? formatNumber(viz.kpi.value)
            : viz.kpi.value}
        </div>
        {viz.kpi.sublabel && (
          <span className="text-xs text-ink-2 font-sans">{viz.kpi.sublabel}</span>
        )}
      </div>
    );
  }

  // Common chart options
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: (viz.series && viz.series.length > 1) || viz.chart_type === 'doughnut',
        position: 'top' as const,
        labels: {
          color: colors.ink,
          font: { family: 'Inter', size: 12 },
          boxWidth: 12,
          usePointStyle: true,
        },
      },
      title: {
        display: !!viz.title,
        text: viz.title || '',
        color: colors.ink,
        font: { family: 'Instrument Serif', size: 18, weight: 'normal' as const },
        padding: { bottom: 12 },
      },
      tooltip: {
        backgroundColor: isDark ? '#171513' : '#FFFFFF',
        titleColor: colors.ink,
        bodyColor: colors.ink,
        borderColor: colors.line,
        borderWidth: 1,
        boxPadding: 4,
        padding: 10,
        bodyFont: { family: 'JetBrains Mono', size: 12 },
        titleFont: { family: 'Inter', size: 12, weight: 'bold' as const },
      },
    },
    scales:
      viz.chart_type !== 'doughnut'
        ? {
            x: {
              grid: { color: colors.line, drawBorder: false },
              ticks: { color: colors.ink3, font: { family: 'Inter', size: 11 } },
            },
            y: {
              grid: { color: colors.line, drawBorder: false },
              ticks: { color: colors.ink3, font: { family: 'JetBrains Mono', size: 11 } },
            },
          }
        : undefined,
  };

  // Build chart dataset
  const chartData = {
    labels: viz.labels || [],
    datasets: (viz.series || []).map((s, idx) => ({
      label: s.name || viz.y_axis || 'Value',
      data: s.data,
      backgroundColor:
        viz.chart_type === 'doughnut'
          ? colors.palette
          : viz.chart_type === 'bar'
          ? colors.palette[idx % colors.palette.length]
          : colors.accentSoft,
      borderColor:
        viz.chart_type === 'doughnut'
          ? colors.line
          : colors.palette[idx % colors.palette.length],
      borderWidth: viz.chart_type === 'line' ? 2 : 1,
      pointRadius: viz.chart_type === 'line' ? 3 : undefined,
      pointBackgroundColor: colors.palette[idx % colors.palette.length],
      tension: 0.25,
    })),
  };

  return (
    <div className="w-full border border-line rounded-lg p-4 bg-surface shadow-xs">
      {viz.title && (
        <div className="font-serif text-lg text-ink mb-3 px-1">{viz.title}</div>
      )}
      <div className="w-full h-64 sm:h-72">
        {viz.chart_type === 'bar' && <Bar data={chartData} options={commonOptions} />}
        {viz.chart_type === 'line' && <Line data={chartData} options={commonOptions} />}
        {viz.chart_type === 'doughnut' && (
          <Doughnut data={chartData} options={commonOptions} />
        )}
      </div>
    </div>
  );
};
