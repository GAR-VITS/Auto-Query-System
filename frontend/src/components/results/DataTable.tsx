import { Download, Table2 } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'

interface DataTableProps {
  columns: string[]
  rows: Record<string, string | number>[]
  rowCount: number
  executionTimeMs: number
}

function formatCell(value: string | number): string {
  if (typeof value === 'number' && value > 999) {
    return value.toLocaleString('en-IN')
  }
  return String(value)
}

export function DataTable({ columns, rows, rowCount, executionTimeMs }: DataTableProps) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="flex items-center justify-between border-b border-surface-600/40 px-5 py-3">
        <div className="flex items-center gap-2">
          <Table2 className="h-4 w-4 text-accent-400" />
          <span className="text-sm font-semibold text-slate-300">Query Results</span>
          <span className="text-xs text-slate-500">
            {rowCount} rows · {executionTimeMs}ms
          </span>
        </div>
        <Button variant="ghost" icon={<Download className="h-4 w-4" />} className="!py-1.5 !px-3">
          Export
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-600/40 bg-surface-800/50">
              {columns.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400"
                >
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-surface-600/20 transition hover:bg-surface-700/30"
              >
                {columns.map((col) => (
                  <td key={col} className="whitespace-nowrap px-4 py-3 text-slate-300">
                    {formatCell(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
