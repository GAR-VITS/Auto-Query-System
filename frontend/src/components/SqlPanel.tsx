import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check, Wrench } from 'lucide-react';
import type { AttemptInfo } from '../store/query';

interface SqlPanelProps {
  sql: string;
  ms?: number;
  attempts?: AttemptInfo[];
  repairs?: number;
}

export const SqlPanel: React.FC<SqlPanelProps> = ({ sql, ms, attempts = [], repairs = 0 }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'sql' | 'diff'>('sql');
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const hasRepairs = (repairs > 0 || attempts.length > 0) && attempts.some((a) => a.error);

  return (
    <div className="w-full border border-line rounded-lg overflow-hidden bg-surface text-ink text-sm transition-all duration-150">
      {/* Header bar / Disclosure trigger */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4 text-ink-3" />
          ) : (
            <ChevronRight className="w-4 h-4 text-ink-3" />
          )}
          <span className="font-mono text-xs uppercase tracking-wider text-ink-2 font-medium">
            SQL Query {ms ? `(${ms}ms)` : ''}
          </span>
          {hasRepairs && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-500/10 text-warn border border-warn/20">
              <Wrench className="w-2.5 h-2.5" />
              Repaired ({repairs || attempts.length} attempt{(repairs || attempts.length) > 1 ? 's' : ''})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 transition-colors font-mono"
            title="Copy SQL"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-ok" />
                <span className="text-[11px] text-ok">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-ink-3" />
                <span className="text-[11px]">Copy</span>
              </>
            )}
          </button>
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className="border-t border-line">
          {hasRepairs && (
            <div className="flex border-b border-line px-4 bg-black/[0.02] dark:bg-white/[0.02]">
              <button
                type="button"
                onClick={() => setActiveTab('sql')}
                className={`py-2 px-3 text-xs font-mono border-b-2 -mb-px transition-colors ${
                  activeTab === 'sql'
                    ? 'border-accent text-accent font-semibold'
                    : 'border-transparent text-ink-3 hover:text-ink'
                }`}
              >
                Executed SQL
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('diff')}
                className={`py-2 px-3 text-xs font-mono border-b-2 -mb-px transition-colors flex items-center gap-1.5 ${
                  activeTab === 'diff'
                    ? 'border-accent text-accent font-semibold'
                    : 'border-transparent text-ink-3 hover:text-ink'
                }`}
              >
                <Wrench className="w-3 h-3 text-warn" />
                Reflection Diff
              </button>
            </div>
          )}

          {activeTab === 'sql' || !hasRepairs ? (
            <div className="p-4 bg-black/[0.03] dark:bg-black/40 overflow-x-auto">
              <pre className="font-mono text-xs text-ink leading-relaxed whitespace-pre-wrap break-all">
                <code>{sql}</code>
              </pre>
            </div>
          ) : (
            <div className="p-4 space-y-3 bg-black/[0.02] dark:bg-black/30">
              <div className="text-xs text-ink-2">
                Self-correction loop triggered:{' '}
                <span className="font-semibold text-ink">
                  {attempts.length} repair round(s)
                </span>{' '}
                before clean execution.
              </div>

              {attempts.map((att, idx) => (
                <div
                  key={idx}
                  className="rounded border border-line overflow-hidden font-mono text-xs"
                >
                  <div className="px-3 py-1.5 bg-black/5 dark:bg-white/5 border-b border-line flex items-center justify-between text-[11px]">
                    <span className="font-bold text-ink-2">
                      Attempt #{att.n || idx + 1}
                    </span>
                    {att.error ? (
                      <span className="text-err font-medium">Failed</span>
                    ) : (
                      <span className="text-ok font-medium">Succeeded</span>
                    )}
                  </div>

                  {att.error && (
                    <div className="px-3 py-2 bg-red-500/10 dark:bg-red-950/30 border-b border-line text-[11px] text-err">
                      <span className="font-bold">Error:</span> {att.error}
                    </div>
                  )}

                  <div className={`p-3 ${att.error ? 'bg-red-500/[0.04]' : 'bg-emerald-500/[0.04]'}`}>
                    <pre className="whitespace-pre-wrap break-all leading-relaxed">
                      <code>{att.sql}</code>
                    </pre>
                  </div>
                </div>
              ))}

              <div className="pt-2">
                <div className="text-[11px] font-mono uppercase text-ink-3 tracking-wider mb-1">
                  Final Validated Query
                </div>
                <div className="p-3 bg-emerald-500/10 border border-ok/20 rounded font-mono text-xs">
                  <pre className="whitespace-pre-wrap break-all leading-relaxed text-ink">
                    <code>{sql}</code>
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
