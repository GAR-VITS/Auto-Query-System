import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { StageInfo } from '../store/query';

interface PipelineRailProps {
  stages: StageInfo[];
  isStreaming?: boolean;
  totalMs?: number;
  repairs?: number;
  liveLabel?: string;
  currentStageN?: number;
  liveStageN?: number;
  liveStageLabel?: string;
}

export const PipelineRail: React.FC<PipelineRailProps> = ({
  stages,
  isStreaming = false,
  totalMs,
  repairs = 0,
  liveLabel,
  currentStageN,
  liveStageN,
  liveStageLabel,
}) => {
  const [expanded, setExpanded] = useState(false);
  const activeStageN = liveStageN ?? currentStageN ?? 1;
  const currentLabel = liveStageLabel ?? liveLabel;

  // If streaming is complete, collapse to summary bar unless user expanded
  if (!isStreaming) {
    const durationSec = totalMs ? (totalMs / 1000).toFixed(1) : '0.8';
    const repairText = repairs > 0 ? `${repairs} repair${repairs > 1 ? 's' : ''}` : '0 repairs';

    return (
      <div className="w-full my-2 text-[12px] text-ink-3 font-mono">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 hover:text-ink transition-colors focus:outline-none cursor-pointer"
        >
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-ok"></span>
            11 stages, {durationSec}s, {repairText}
          </span>
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>

        {expanded && (
          <div className="mt-2.5 space-y-1.5 rounded-lg border border-line bg-surface p-3 text-xs font-sans">
            {stages.map((st) => (
              <div key={st.n} className="flex items-center justify-between text-ink-2">
                <span className="flex items-center gap-2">
                  <span className="font-mono text-ink-3">[{st.n}]</span>
                  <span>{st.name}</span>
                </span>
                <span className="font-mono text-ink-3">{st.ms ? `${st.ms}ms` : 'ok'}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Active streaming state: 11 dots with connecting line
  return (
    <div className="w-full my-3 space-y-2">
      {/* 11 Dots Rail */}
      <div className="relative flex items-center justify-between px-1">
        {/* Connecting hairline */}
        <div className="absolute left-2 right-2 top-1/2 -translate-y-1/2 h-[1px] bg-line z-0" />

        {stages.map((st) => {
          const isDone = st.status === 'done' || st.n < activeStageN;
          const isCurrent = st.n === activeStageN;
          const isError = st.status === 'error';

          return (
            <div
              key={st.n}
              className="relative z-10 flex flex-col items-center group cursor-default"
              title={`${st.n}. ${st.name} (${st.status})`}
            >
              <div
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  isError
                    ? 'bg-err scale-125 ring-2 ring-err/30'
                    : isCurrent
                    ? 'bg-accent scale-150 ring-4 ring-accent/20 animate-pulse'
                    : isDone
                    ? 'bg-ok'
                    : 'bg-line'
                }`}
              />
            </div>
          );
        })}
      </div>

      {/* Live status label */}
      <div className="flex items-center justify-between text-[11px] font-mono text-ink-3">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-ping" />
          <span className="text-ink-2 font-medium">
            Stage {activeStageN}/11: {currentLabel || stages[activeStageN - 1]?.name || 'Processing...'}
          </span>
        </span>
        {totalMs !== undefined && <span>{totalMs}ms</span>}
      </div>
    </div>
  );
};
