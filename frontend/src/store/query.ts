/**
 * Zustand Query & Pipeline State Store
 */

import { create } from 'zustand';
import { streamQuery } from '../lib/sse';

export interface StageInfo {
  n: number;
  name: string;
  status: 'pending' | 'start' | 'done' | 'error';
  ms: number;
  detail?: string;
}

export interface AttemptInfo {
  n: number;
  sql: string;
  error: string;
}

export interface QueryTurn {
  id: string;
  question: string;
  stages: StageInfo[];
  attempts: AttemptInfo[];
  result?: {
    sql: string;
    columns: string[];
    rows: any[][];
    row_count: number;
    truncated: boolean;
    interpretation: string;
  };
  analysis?: {
    stats: any;
    insight_text: string;
    read_as: string;
    flags: string[];
  };
  viz?: any;
  clarify?: string;
  actionProposal?: any;
  error?: string;
  totalMs?: number;
  repairs?: number;
}

interface QueryStoreState {
  history: QueryTurn[];
  activeTurnId: string | null;
  isStreaming: boolean;
  liveStageN: number;
  liveStageLabel: string;
  abortController: AbortController | null;

  askQuestion: (question: string, isVoice?: boolean) => Promise<void>;
  cancelRequest: () => void;
  clearHistory: () => void;
}

export const useQueryStore = create<QueryStoreState>((set, get) => ({
  history: [],
  activeTurnId: null,
  isStreaming: false,
  liveStageN: 1,
  liveStageLabel: 'Initiating...',
  abortController: null,

  askQuestion: async (question: string, isVoice = false) => {
    if (!question.trim() || get().isStreaming) return;

    const turnId = `turn_${Date.now()}`;
    const controller = new AbortController();

    const newTurn: QueryTurn = {
      id: turnId,
      question: question.trim(),
      stages: Array.from({ length: 11 }, (_, i) => ({
        n: i + 1,
        name: getStageName(i + 1),
        status: i === 0 ? 'start' : 'pending',
        ms: 0,
      })),
      attempts: [],
    };

    set((state) => ({
      history: [...state.history, newTurn],
      activeTurnId: turnId,
      isStreaming: true,
      liveStageN: 1,
      liveStageLabel: 'Query received...',
      abortController: controller,
    }));

    await streamQuery(
      question,
      {
        onStage: (st) => {
          set((state) => {
            const hist = state.history.map((t) => {
              if (t.id !== turnId) return t;
              const updatedStages = t.stages.map((s) => {
                if (s.n === st.n) {
                  return { ...s, status: st.status as any, ms: st.ms, detail: st.detail || s.detail };
                }
                return s;
              });
              return { ...t, stages: updatedStages };
            });

            const label = st.name + (st.attempt ? ` (Attempt ${st.attempt})` : '');
            return {
              history: hist,
              liveStageN: st.n,
              liveStageLabel: label,
            };
          });
        },

        onAttempt: (att) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, attempts: [...t.attempts, att] } : t
            ),
          }));
        },

        onResult: (res) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, result: res } : t
            ),
          }));
        },

        onAnalysis: (an) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, analysis: an } : t
            ),
          }));
        },

        onViz: (viz) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, viz } : t
            ),
          }));
        },

        onClarify: (cl) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, clarify: cl.question } : t
            ),
          }));
        },

        onActionProposal: (prop) => {
          set((state) => ({
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, actionProposal: prop } : t
            ),
          }));
        },

        onDone: (d) => {
          set((state) => ({
            isStreaming: false,
            abortController: null,
            liveStageLabel: 'Complete',
            history: state.history.map((t) =>
              t.id === turnId
                ? {
                    ...t,
                    totalMs: d.total_ms,
                    repairs: d.repairs || t.attempts.length,
                    stages: t.stages.map((s) => ({ ...s, status: s.status === 'pending' ? 'done' : s.status })),
                  }
                : t
            ),
          }));
        },

        onError: (err) => {
          set((state) => ({
            isStreaming: false,
            abortController: null,
            liveStageLabel: 'Error',
            history: state.history.map((t) =>
              t.id === turnId ? { ...t, error: err.message } : t
            ),
          }));
        },
      },
      controller.signal,
      isVoice
    );
  },

  cancelRequest: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
      set({ isStreaming: false, abortController: null });
    }
  },

  clearHistory: () => {
    set({ history: [], activeTurnId: null, isStreaming: false });
  },
}));

function getStageName(n: number): string {
  const names: Record<number, string> = {
    1: 'Query received (text or voice)',
    2: 'Transcription on the client',
    3: 'Gateway and token auth',
    4: 'Schema retrieval (ChromaDB)',
    5: 'SQL drafting (LLM)',
    6: 'Reflection loop',
    7: 'Analysis (Pandas)',
    8: 'Visualization',
    9: 'Action module (RBAC)',
    10: 'Audit trail write',
    11: 'Delivery to client',
  };
  return names[n] || `Stage ${n}`;
}
