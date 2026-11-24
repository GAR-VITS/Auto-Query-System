import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, ShieldCheck, AlertOctagon } from 'lucide-react';
import { confirmAction } from '../lib/api';
import { useSessionStore } from '../store/session';

export interface ActionProposal {
  action_name: 'SET_ACCOUNT_STATUS' | 'SET_RISK_FLAG' | 'CLEAR_RISK_FLAG';
  target_id: string | number;
  before_state: any;
  after_state: any;
  confirmation_token: string;
  expires_at: number; // Unix timestamp in seconds
  reason: string;
  acting_role: string;
  affected_rows?: number;
}

interface ActionConfirmProps {
  proposal: ActionProposal;
  onSuccess?: (auditHash: string) => void;
  onCancel?: () => void;
}

export const ActionConfirm: React.FC<ActionConfirmProps> = ({
  proposal,
  onSuccess,
  onCancel,
}) => {
  const { user } = useSessionStore();
  const [reason, setReason] = useState(proposal.reason || 'User confirmed write-back');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedHash, setConfirmedHash] = useState<string | null>(null);
  const [isCancelled, setIsCancelled] = useState(false);

  // 120s countdown calculation
  const [secondsRemaining, setSecondsRemaining] = useState<number>(() => {
    if (proposal.expires_at) {
      const nowSec = Date.now() / 1000;
      const diff = Math.floor(proposal.expires_at - nowSec);
      return Math.max(0, diff);
    }
    return 120;
  });

  useEffect(() => {
    if (confirmedHash || isCancelled || secondsRemaining <= 0) return;
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [confirmedHash, isCancelled, secondsRemaining]);

  const isExpired = secondsRemaining <= 0;

  // Authorization check based on RBAC rules
  const isAuthorized = (() => {
    const role: string = user.role;
    if (role === 'admin') return true;
    if (role === 'viewer') return false;
    if (proposal.action_name === 'SET_ACCOUNT_STATUS') {
      return role === 'branch_officer' || role === 'admin';
    }
    if (proposal.action_name === 'SET_RISK_FLAG' || proposal.action_name === 'CLEAR_RISK_FLAG') {
      return role === 'credit_manager' || role === 'admin';
    }
    return false;
  })();

  const handleConfirm = async () => {
    if (!isAuthorized || isExpired || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const idempotencyKey = `idem_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      
      // Build parameters according to action_name
      let params: Record<string, any> = { reason };
      if (proposal.action_name === 'SET_ACCOUNT_STATUS') {
        params = {
          account_id: proposal.target_id,
          new_status: proposal.after_state?.status || 'ACTIVE',
          reason,
        };
      } else if (proposal.action_name === 'SET_RISK_FLAG' || proposal.action_name === 'CLEAR_RISK_FLAG') {
        params = {
          customer_id: proposal.target_id,
          risk_flag: proposal.action_name === 'SET_RISK_FLAG',
          reason,
        };
      }

      const res = await confirmAction(
        proposal.action_name,
        params,
        proposal.confirmation_token,
        idempotencyKey
      );
      const auditHash = res.audit_hash || res.hash || 'recorded';
      setConfirmedHash(auditHash);
      if (onSuccess) onSuccess(auditHash);
    } catch (err: any) {
      setError(err?.message || 'Failed to execute governed action.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setIsCancelled(true);
    if (onCancel) onCancel();
  };

  if (isCancelled) {
    return (
      <div className="w-full border border-line rounded-lg p-3.5 bg-surface text-ink-3 text-xs font-mono flex items-center justify-between">
        <span>Proposed action cancelled by user.</span>
      </div>
    );
  }

  if (confirmedHash) {
    return (
      <div className="w-full border border-ok/30 bg-emerald-500/5 rounded-lg p-4 text-xs font-mono space-y-1.5">
        <div className="flex items-center gap-2 text-ok font-semibold">
          <CheckCircle2 className="w-4 h-4" />
          <span>Action executed & verified into cryptographically chained audit log.</span>
        </div>
        <div className="text-[11px] text-ink-2 truncate">
          Audit Entry Hash:{' '}
          <span className="font-mono text-ink select-all">{confirmedHash}</span>
        </div>
      </div>
    );
  }

  // Quiet denial block if unauthorized
  if (!isAuthorized) {
    return (
      <div className="w-full border border-amber-500/30 bg-amber-500/5 rounded-lg p-4 text-xs space-y-2">
        <div className="flex items-center gap-2 text-warn font-medium font-sans">
          <AlertOctagon className="w-4 h-4" />
          <span>Action Blocked: Insufficient Permissions</span>
        </div>
        <p className="text-ink-2 leading-relaxed">
          Your current role (<span className="font-mono font-bold">{user.role}</span>) is
          not authorized to execute write-backs for{' '}
          <span className="font-mono font-bold">{proposal.action_name}</span>. Switch demo role to{' '}
          <span className="font-semibold text-ink">
            {proposal.action_name === 'SET_ACCOUNT_STATUS'
              ? 'Branch Officer'
              : 'Credit Manager'}
          </span>{' '}
          or Admin to approve.
        </p>
      </div>
    );
  }

  // Countdown circle calculation (120s basis)
  const totalDuration = 120;
  const progressPercent = Math.max(0, (secondsRemaining / totalDuration) * 100);
  const strokeDashoffset = 100 - progressPercent;

  const beforeStr =
    proposal.before_state?.status ||
    (proposal.before_state?.risk_flag !== undefined
      ? `risk_flag: ${proposal.before_state.risk_flag}`
      : JSON.stringify(proposal.before_state));

  const afterStr =
    proposal.after_state?.status ||
    (proposal.after_state?.risk_flag !== undefined
      ? `risk_flag: ${proposal.after_state.risk_flag}`
      : JSON.stringify(proposal.after_state));

  return (
    <div className="w-full border-2 border-accent/40 rounded-lg p-4 bg-surface shadow-xs space-y-3">
      {/* Header with Title and Countdown */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-accent" />
          <span className="font-mono text-xs uppercase tracking-wider font-bold text-accent">
            Governed Write-Back Proposal
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-black/5 dark:bg-white/5 text-ink-2 border border-line">
            Role: {user.role}
          </span>
        </div>

        {/* 2-minute countdown ring */}
        <div className="flex items-center gap-2 text-xs font-mono text-ink-3">
          <div className="relative w-5 h-5 flex items-center justify-center">
            <svg className="w-5 h-5 -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-line"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={secondsRemaining < 20 ? 'text-err' : 'text-accent'}
                strokeDasharray="100, 100"
                strokeDashoffset={strokeDashoffset}
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
          </div>
          <span>
            {Math.floor(secondsRemaining / 60)}:
            {(secondsRemaining % 60).toString().padStart(2, '0')}
          </span>
        </div>
      </div>

      {/* Target and Before -> After on one line */}
      <div className="p-3 bg-black/[0.02] dark:bg-white/[0.02] rounded border border-line flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
        <div className="text-ink-2">
          <span className="text-ink-3 uppercase text-[10px] mr-1.5">Action:</span>
          <span className="font-bold text-ink">{proposal.action_name}</span> on target #
          <span className="font-bold text-ink">{proposal.target_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-black/5 dark:bg-white/5 line-through text-ink-3">
            {beforeStr}
          </span>
          <span className="text-accent font-bold">→</span>
          <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-bold">
            {afterStr}
          </span>
        </div>
      </div>

      {/* Editable Reason Field */}
      <div>
        <label className="block text-[11px] font-mono uppercase tracking-wider text-ink-3 mb-1">
          Audit Justification / Reason:
        </label>
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          disabled={isSubmitting || isExpired}
          className="w-full px-3 py-1.5 text-xs bg-surface border border-line rounded focus:outline-none focus:border-accent text-ink font-sans transition-colors"
          placeholder="Enter justification for audit log..."
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="text-xs text-err font-mono flex items-center gap-1.5">
          <XCircle className="w-3.5 h-3.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={handleCancel}
          disabled={isSubmitting}
          className="px-3 py-1.5 text-xs font-mono rounded border border-line text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={isSubmitting || isExpired || !reason.trim()}
          className="px-4 py-1.5 text-xs font-mono font-medium rounded bg-accent text-white hover:opacity-90 disabled:opacity-40 transition-all cursor-pointer flex items-center gap-1.5"
        >
          {isSubmitting ? (
            <span>Executing...</span>
          ) : (
            <>
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Confirm & Write ({secondsRemaining}s)</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
