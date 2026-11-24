import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, ChevronRight, X, RefreshCw, KeyRound } from 'lucide-react';
import { fetchAuditLogs, verifyAuditChain } from '../lib/api';

export interface AuditEntry {
  sequence: number;
  timestamp: string;
  request_id: string;
  user_id: string;
  role: string;
  event_type: string;
  status: string;
  payload: any;
  prev_hash: string;
  row_hash: string;
}

export const AuditTable: React.FC = () => {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [selectedRow, setSelectedRow] = useState<AuditEntry | null>(null);

  // Chain verification state
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    valid: boolean;
    entries_verified: number;
    head_hash: string;
  } | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const filters = ['ALL', 'QUERY', 'ACTION_CONFIRMED', 'ACTION_PROPOSED', 'FAILED'];

  const loadLogs = async (filter = selectedFilter) => {
    setLoading(true);
    try {
      const eventType = filter === 'ALL' ? undefined : filter;
      const res = await fetchAuditLogs(50, 0, eventType);
      setLogs(res.logs || res.entries || []);
      setTotalCount(res.total || (res.logs || []).length);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    setVerifyError(null);
    try {
      const res = await verifyAuditChain();
      setVerifyResult(res);
    } catch (err: any) {
      setVerifyError(err?.message || 'Cryptographic chain verification failed.');
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    loadLogs(selectedFilter);
  }, [selectedFilter]);

  return (
    <div className="w-full space-y-4">
      {/* Top Controls: Filter Chips & Chain Verification Button */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-mono text-ink-3 uppercase mr-1">Filter:</span>
          {filters.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setSelectedFilter(f)}
              className={`px-2.5 py-1 text-xs font-mono rounded transition-colors cursor-pointer ${
                selectedFilter === f
                  ? 'bg-accent text-white font-medium'
                  : 'bg-surface border border-line text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              {f}
            </button>
          ))}
          {totalCount > 0 && (
            <span className="text-[11px] font-mono text-ink-3 ml-2">
              ({totalCount} entries)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadLogs(selectedFilter)}
            disabled={loading}
            className="p-1.5 rounded border border-line bg-surface text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
            title="Refresh logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            type="button"
            onClick={handleVerifyChain}
            disabled={verifying}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded border border-line bg-surface hover:bg-black/5 dark:hover:bg-white/5 text-ink transition-colors cursor-pointer"
          >
            <KeyRound className="w-3.5 h-3.5 text-accent" />
            <span>{verifying ? 'Verifying SHA-256...' : 'Verify Chain Integrity'}</span>
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {verifyResult && (
        <div
          className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
            verifyResult.valid
              ? 'bg-emerald-500/10 border-ok/30 text-ok'
              : 'bg-red-500/10 border-err/30 text-err'
          }`}
        >
          <div className="flex items-center gap-2">
            {verifyResult.valid ? (
              <CheckCircle2 className="w-4 h-4 text-ok" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-err" />
            )}
            <span>
              {verifyResult.valid
                ? `Cryptographic Chain Verified: ${verifyResult.entries_verified} entries intact.`
                : 'Tampering Detected: Chain sequence broken!'}
            </span>
          </div>
          <span className="text-[11px] opacity-80 truncate max-w-xs select-all">
            Head: {verifyResult.head_hash?.slice(0, 16)}...
          </span>
        </div>
      )}

      {verifyError && (
        <div className="p-3 rounded-lg border border-err/30 bg-red-500/10 text-xs font-mono text-err flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" />
          <span>{verifyError}</span>
        </div>
      )}

      {/* Main Audit Entries Table */}
      <div className="w-full border border-line rounded-lg overflow-hidden bg-surface">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-black/[0.02] dark:bg-white/[0.02] border-b border-line">
              <tr>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  Seq
                </th>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  Timestamp
                </th>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  Event
                </th>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  Status
                </th>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  User / Role
                </th>
                <th className="py-2.5 px-3 font-mono text-[11px] uppercase tracking-wider text-ink-3 font-medium">
                  Row Hash (SHA-256)
                </th>
                <th className="py-2.5 px-3 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-mono">
              {logs.map((entry) => (
                <tr
                  key={entry.sequence}
                  onClick={() => setSelectedRow(entry)}
                  className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] cursor-pointer transition-colors"
                >
                  <td className="py-2 px-3 text-ink font-medium">#{entry.sequence}</td>
                  <td className="py-2 px-3 text-ink-3 whitespace-nowrap">
                    {new Date(entry.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </td>
                  <td className="py-2 px-3 font-medium">
                    <span
                      className={`inline-block px-1.5 py-0.5 rounded text-[10px] ${
                        entry.event_type.includes('CONFIRMED')
                          ? 'bg-emerald-500/10 text-ok border border-ok/20'
                          : entry.event_type.includes('PROPOSED')
                          ? 'bg-amber-500/10 text-warn border border-warn/20'
                          : entry.event_type === 'FAILED'
                          ? 'bg-red-500/10 text-err border border-err/20'
                          : 'bg-black/5 dark:bg-white/5 text-ink-2'
                      }`}
                    >
                      {entry.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`text-[11px] ${
                        entry.status === 'SUCCESS' || entry.status === 'CONFIRMED'
                          ? 'text-ok'
                          : entry.status === 'DENIED' || entry.status === 'FAILED'
                          ? 'text-err'
                          : 'text-ink-2'
                      }`}
                    >
                      {entry.status}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-ink-2">
                    <span className="text-ink">{entry.user_id}</span>
                    <span className="text-ink-3 ml-1 text-[11px]">({entry.role})</span>
                  </td>
                  <td className="py-2 px-3 text-ink-3 truncate max-w-[120px] select-all">
                    {entry.row_hash?.slice(0, 12)}...
                  </td>
                  <td className="py-2 px-3 text-right text-ink-3">
                    <ChevronRight className="w-4 h-4 inline" />
                  </td>
                </tr>
              ))}
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ink-3">
                    No audit records matching filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Payload Drawer / Detail Modal */}
      {selectedRow && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex justify-end">
          <div className="w-full max-w-lg bg-surface border-l border-line h-full flex flex-col p-6 shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-line mb-4">
              <div>
                <h3 className="font-serif text-xl text-ink">
                  Audit Entry #{selectedRow.sequence}
                </h3>
                <span className="font-mono text-xs text-ink-3">
                  Request: {selectedRow.request_id}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedRow(null)}
                className="p-1 rounded text-ink-3 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded bg-black/[0.02] dark:bg-white/[0.02] border border-line">
                <div>
                  <span className="text-ink-3 text-[10px] uppercase block">Timestamp</span>
                  <span className="text-ink">{selectedRow.timestamp}</span>
                </div>
                <div>
                  <span className="text-ink-3 text-[10px] uppercase block">Event Type</span>
                  <span className="text-ink font-semibold">{selectedRow.event_type}</span>
                </div>
                <div>
                  <span className="text-ink-3 text-[10px] uppercase block">Status</span>
                  <span className="text-ink">{selectedRow.status}</span>
                </div>
                <div>
                  <span className="text-ink-3 text-[10px] uppercase block">Acting User</span>
                  <span className="text-ink">{selectedRow.user_id} ({selectedRow.role})</span>
                </div>
              </div>

              <div>
                <span className="text-ink-3 text-[10px] uppercase block mb-1">
                  Previous Hash (Chained)
                </span>
                <div className="p-2 rounded bg-black/5 dark:bg-white/5 border border-line text-[11px] text-ink break-all select-all">
                  {selectedRow.prev_hash}
                </div>
              </div>

              <div>
                <span className="text-ink-3 text-[10px] uppercase block mb-1">
                  Row SHA-256 Hash
                </span>
                <div className="p-2 rounded bg-black/5 dark:bg-white/5 border border-line text-[11px] text-accent font-bold break-all select-all">
                  {selectedRow.row_hash}
                </div>
              </div>

              <div>
                <span className="text-ink-3 text-[10px] uppercase block mb-1">
                  Event Payload (Canonical JSON)
                </span>
                <div className="p-3 rounded bg-black/[0.03] dark:bg-black/40 border border-line overflow-x-auto">
                  <pre className="text-xs text-ink leading-relaxed">
                    {JSON.stringify(
                      typeof selectedRow.payload === 'string'
                        ? JSON.parse(selectedRow.payload)
                        : selectedRow.payload,
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
