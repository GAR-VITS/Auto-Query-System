import React, { useRef, useEffect } from 'react';
import { useQueryStore } from '../store/query';
import { CommandBar } from '../components/CommandBar';
import { PipelineRail } from '../components/PipelineRail';
import { InsightCard } from '../components/InsightCard';
import { ChartCard } from '../components/ChartCard';
import { ResultTable } from '../components/ResultTable';
import { SqlPanel } from '../components/SqlPanel';
import { ActionConfirm } from '../components/ActionConfirm';
import { HelpCircle, AlertTriangle } from 'lucide-react';

const EXAMPLE_CHIPS = [
  'Show top 5 branches by loan volume',
  'List customers with high risk flag and delinquent loans',
  'Reconcile daily ledger vs transaction sums for account 10482',
  'Activate account 10482',
];

export const AskView: React.FC = () => {
  const { history, isStreaming, liveStageN, liveStageLabel, askQuestion, cancelRequest } =
    useQueryStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new turns
  useEffect(() => {
    if (history.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history.length, isStreaming]);

  const handleChipClick = (chip: string) => {
    if (!isStreaming) {
      askQuestion(chip);
    }
  };

  return (
    <div className="w-full max-w-[720px] mx-auto px-4 py-8 space-y-12">
      {/* Empty State */}
      {history.length === 0 && (
        <div className="pt-16 sm:pt-24 text-center space-y-6">
          <div className="space-y-3">
            <h1 className="font-serif text-5xl sm:text-6xl text-ink font-normal tracking-tight">
              Ask your data.
            </h1>
            <p className="text-sm sm:text-base text-ink-2 font-sans max-w-md mx-auto leading-relaxed">
              Natural language over PostgreSQL. Governed, self-correcting, cryptographically audited.
            </p>
          </div>

          {/* Primary Command Input */}
          <div className="pt-2">
            <CommandBar
              onSend={(q) => {
                askQuestion(q);
              }}
              isStreaming={isStreaming}
              onCancel={cancelRequest}
              placeholder="Ask a question or propose an action..."
            />
          </div>

          {/* 4 Example Chips from Section 15.7 */}
          <div className="pt-4 space-y-2">
            <div className="text-[11px] font-mono uppercase tracking-wider text-ink-3">
              Suggested queries
            </div>
            <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl mx-auto">
              {EXAMPLE_CHIPS.map((chip, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleChipClick(chip)}
                  disabled={isStreaming}
                  className="px-3 py-1.5 text-xs font-mono rounded-full border border-line bg-surface hover:border-accent hover:text-accent transition-all cursor-pointer text-ink-2 shadow-2xs text-left"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Query Turns History */}
      {history.length > 0 && (
        <div className="space-y-12">
          {history.map((turn, tIdx) => {
            const isTurnStreaming = isStreaming && tIdx === history.length - 1;

            return (
              <div
                key={turn.id}
                className="space-y-6 border-b border-line pb-12 last:border-b-0"
              >
                {/* User Prompt */}
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-ink-3">
                      Query #{tIdx + 1}
                    </span>
                    <h2 className="font-serif text-2xl text-ink font-normal">
                      {turn.question}
                    </h2>
                  </div>
                  {turn.totalMs && (
                    <span className="font-mono text-xs text-ink-3 whitespace-nowrap mt-1">
                      {turn.totalMs}ms
                    </span>
                  )}
                </div>

                {/* 11-Stage Pipeline Rail */}
                <PipelineRail
                  stages={turn.stages}
                  isStreaming={isTurnStreaming}
                  totalMs={turn.totalMs}
                  repairs={turn.repairs}
                  liveStageN={isTurnStreaming ? liveStageN : undefined}
                  liveStageLabel={isTurnStreaming ? liveStageLabel : undefined}
                />

                {/* Error Banner if Turn Failed */}
                {turn.error && (
                  <div className="p-4 rounded-lg border border-err/30 bg-red-500/10 text-xs font-mono text-err flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold">Pipeline Error</div>
                      <div className="mt-1 leading-relaxed">{turn.error}</div>
                    </div>
                  </div>
                )}

                {/* Clarification prompt if ambiguous */}
                {turn.clarify && (
                  <div className="p-4 rounded-lg border border-amber-500/30 bg-amber-500/5 text-xs text-ink flex items-start gap-2.5">
                    <HelpCircle className="w-4 h-4 text-warn shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-warn font-mono uppercase text-[11px]">
                        Clarification Needed
                      </div>
                      <div className="mt-1 leading-relaxed text-ink-2 font-serif text-base">
                        {turn.clarify}
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Proposal Card */}
                {turn.actionProposal && (
                  <div className="pt-2">
                    <ActionConfirm proposal={turn.actionProposal} />
                  </div>
                )}

                {/* Answer Anatomy */}
                {turn.result && (
                  <div className="space-y-6 pt-2">
                    {/* 1. Insight Headline */}
                    {turn.analysis && (
                      <InsightCard
                        insightText={turn.analysis.insight_text}
                        readAs={turn.analysis.read_as}
                        flags={turn.analysis.flags}
                      />
                    )}

                    {/* 2. Visual Chart / KPI Card */}
                    {turn.viz && <ChartCard viz={turn.viz} />}

                    {/* 3. Result Table */}
                    <ResultTable
                      columns={turn.result.columns}
                      rows={turn.result.rows}
                      rowCount={turn.result.row_count}
                      truncated={turn.result.truncated}
                    />

                    {/* 4. SQL Panel with Diff Reflection Support */}
                    <SqlPanel
                      sql={turn.result.sql}
                      ms={turn.totalMs}
                      attempts={turn.attempts}
                      repairs={turn.repairs}
                    />
                  </div>
                )}
              </div>
            );
          })}

          {/* Sticky Bottom Command Bar when turns exist */}
          <div className="sticky bottom-6 pt-4 pb-2 bg-gradient-to-t from-bg via-bg to-transparent">
            <CommandBar
              onSend={(q) => {
                askQuestion(q);
              }}
              isStreaming={isStreaming}
              onCancel={cancelRequest}
              placeholder="Ask a follow-up or propose an action..."
            />
          </div>

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
