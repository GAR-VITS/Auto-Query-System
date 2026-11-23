import { Link } from 'react-router-dom'
import { ArrowRight, Clock, Sparkles } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import type { QueryResult } from '@/types'

interface RecentQueriesProps {
  queries: QueryResult[]
}

export function RecentQueries({ queries }: RecentQueriesProps) {
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Recent Queries
        </h3>
        <Link
          to="/query"
          className="flex items-center gap-1 text-xs font-medium text-accent-400 hover:text-accent-300"
        >
          New Query <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="space-y-2">
        {queries.map((query) => (
          <div
            key={query.id}
            className="group rounded-xl border border-surface-600/30 bg-surface-800/30 p-3 transition hover:border-accent-500/30 hover:bg-surface-800/60"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-slate-200 line-clamp-2">
                {query.question}
              </p>
              {query.corrections ? (
                <Badge variant="warning">Corrected</Badge>
              ) : (
                <Badge variant="success">Success</Badge>
              )}
            </div>
            <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {query.executionTimeMs}ms
              </span>
              <span>{query.rowCount} rows</span>
              {query.analysis && (
                <span className="flex items-center gap-1 text-indigo-400">
                  <Sparkles className="h-3 w-3" />
                  Analysis available
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
