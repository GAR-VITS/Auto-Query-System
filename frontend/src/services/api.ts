import type { QueryRequest, QueryResponse } from '@/types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string; error?: string }
    return data.error ?? data.detail ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  const data = (await response.json()) as QueryResponse

  if (!response.ok) {
    throw new Error(data.error ?? (await parseErrorResponse(response)))
  }

  return data
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
    return response.ok
  } catch {
    return false
  }
}

export { API_BASE }
