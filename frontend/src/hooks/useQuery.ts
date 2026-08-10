import { useState } from 'react'
import { submitQuery } from '@/services/api'
import type { QueryResult, AgentStatus } from '@/types'

export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle')

  const executeQuery = async (query: string, _voice?: boolean) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setAgentStatus('running')

    try {
      const response = await submitQuery({ question: query })

      if (response.success && response.result) {
        setResult(response.result)
        setAgentStatus('success')
      } else {
        setError(response.error ?? 'Query failed without a specific error.')
        setAgentStatus('error')
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.'
      setError(message)
      setAgentStatus('error')
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    result,
    agentStatus,
    executeQuery,
  }
}
