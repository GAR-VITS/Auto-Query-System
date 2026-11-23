import React from 'react';
import { AuditTable } from '../components/AuditTable';
import { ShieldCheck } from 'lucide-react';

export const AuditView: React.FC = () => {
  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* View Header */}
      <div className="space-y-1.5 border-b border-line pb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-accent" />
          <h1 className="font-serif text-3xl sm:text-4xl text-ink font-normal">
            Cryptographic Audit Trail
          </h1>
        </div>
        <p className="text-xs sm:text-sm text-ink-2 font-sans max-w-2xl leading-relaxed">
          Append-only SHA-256 hash-chained immutable ledger. Every query, generated SQL, RBAC check,
          and governed action is cryptographically linked to the preceding entry.
        </p>
      </div>

      {/* Main Audit Table */}
      <AuditTable />
    </div>
  );
};
