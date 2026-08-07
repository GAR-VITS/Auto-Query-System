import { useCallback, useState } from 'react'
import { submitQuery } from '@/services/api'
import type { AgentStatus, QueryResult } from '@/types'

export function useQuery() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle')

  const executeQuery = useCallback(async (question: string, voice = false) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setAgentStatus('running')

    try {
      setAgentStatus('correcting')
      await new Promise((r) => setTimeout(r, 400))
      setAgentStatus('running')

      const response = await submitQuery({ question, voice })

      if (response.success && response.result) {
        setResult(response.result)
        setAgentStatus(response.result.corrections ? 'correcting' : 'success')
      } else {
        setError(response.error ?? 'Query failed')
        setAgentStatus('error')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setAgentStatus('error')
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setAgentStatus('idle')
  }, [])

  return { loading, error, result, agentStatus, executeQuery, reset }
}
