import { mockQueryResponse } from '@/data/mockData'
import type { QueryRequest, QueryResponse } from '@/types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  try {
    const response = await fetch(`${API_BASE}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return (await response.json()) as QueryResponse
  } catch {
    await delay(1200 + Math.random() * 800)
    return {
      success: true,
      result: mockQueryResponse(request.question),
    }
  }
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
    return response.ok
  } catch {
    return false
  }
}
