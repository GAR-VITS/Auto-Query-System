import { motion, AnimatePresence } from 'framer-motion'
import { AlertCircle } from 'lucide-react'
import { QueryInput } from '@/components/query/QueryInput'
import { SuggestedQueries } from '@/components/query/SuggestedQueries'
import { SqlPreview } from '@/components/results/SqlPreview'
import { DataTable } from '@/components/results/DataTable'
import { AnalysisPanel } from '@/components/results/AnalysisPanel'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useQuery } from '@/hooks/useQuery'
import { SUGGESTED_QUERIES } from '@/constants/navigation'

export function QueryWorkspacePage() {
  const { loading, error, result, agentStatus, executeQuery } = useQuery()

  const handleSuggestedSelect = (query: string) => {
    executeQuery(query)
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <QueryInput onSubmit={executeQuery} loading={loading} agentStatus={agentStatus} />

      {!loading && !result && (
        <SuggestedQueries suggestions={SUGGESTED_QUERIES} onSelect={handleSuggestedSelect} />
      )}

      <AnimatePresence mode="wait">
        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex justify-center py-12"
          >
            <LoadingSpinner
              size="lg"
              label={
                agentStatus === 'correcting'
                  ? 'Self-correcting query via agentic loop...'
                  : 'Agents processing your query...'
              }
            />
          </motion.div>
        )}

        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
          >
            <AlertCircle className="h-5 w-5 shrink-0" />
            {error}
          </motion.div>
        )}

        {result && !loading && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <SqlPreview sql={result.sql} corrections={result.corrections} />
            <DataTable
              columns={result.columns}
              rows={result.rows}
              rowCount={result.rowCount}
              executionTimeMs={result.executionTimeMs}
            />
            {result.analysis && <AnalysisPanel analysis={result.analysis} />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
