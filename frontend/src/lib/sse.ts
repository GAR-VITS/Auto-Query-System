/**
 * SSE Parser for POST requests in fetch()
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SSECallbacks {
  onStage?: (stage: { n: number; name: string; status: string; ms: number; detail?: string; attempt?: number; sql?: string; error?: string }) => void;
  onAttempt?: (attempt: { n: number; sql: string; error: string }) => void;
  onResult?: (result: { sql: string; columns: string[]; rows: any[][]; row_count: number; truncated: boolean; attempts: any[]; interpretation: string }) => void;
  onAnalysis?: (analysis: { stats: any; insight_text: string; read_as: string; flags: string[] }) => void;
  onViz?: (viz: any) => void;
  onClarify?: (clarify: { question: string }) => void;
  onActionProposal?: (proposal: any) => void;
  onDone?: (done: { request_id: string; total_ms: number; repairs?: number; row_count?: number }) => void;
  onError?: (error: { message: string }) => void;
}

export async function streamQuery(
  question: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  isVoice = false
) {
  const token = localStorage.getItem('nexus_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}/query/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ question, is_voice: isVoice }),
    signal,
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Connection error');
    callbacks.onError?.({ message: `HTTP ${response.status}: ${errText}` });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError?.({ message: 'Readable stream not supported by browser.' });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        if (!frame.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const lines = frame.split('\n');
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.replace('event: ', '').trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.replace('data: ', '').trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsed = JSON.parse(dataStr);
          switch (eventType) {
            case 'stage':
              callbacks.onStage?.(parsed);
              break;
            case 'attempt':
              callbacks.onAttempt?.(parsed);
              break;
            case 'result':
              callbacks.onResult?.(parsed);
              break;
            case 'analysis':
              callbacks.onAnalysis?.(parsed);
              break;
            case 'viz':
              callbacks.onViz?.(parsed);
              break;
            case 'clarify':
              callbacks.onClarify?.(parsed);
              break;
            case 'action_proposal':
              callbacks.onActionProposal?.(parsed);
              break;
            case 'done':
              callbacks.onDone?.(parsed);
              break;
            case 'error':
              callbacks.onError?.(parsed);
              break;
          }
        } catch (e) {
          console.error('Failed to parse SSE frame data', dataStr, e);
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      callbacks.onDone?.({ request_id: 'aborted', total_ms: 0 });
    } else {
      callbacks.onError?.({ message: err.message || 'Stream connection broken.' });
    }
  } finally {
    reader.releaseLock();
  }
}
