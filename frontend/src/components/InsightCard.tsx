import React from 'react';
import { AlertCircle } from 'lucide-react';

interface InsightCardProps {
  insightText: string;
  readAs?: string;
  flags?: string[];
}

export const InsightCard: React.FC<InsightCardProps> = ({ insightText, readAs, flags = [] }) => {
  if (!insightText) return null;

  return (
    <div className="w-full border-l-2 border-accent pl-4 py-1 space-y-2">
      {/* 20px Instrument Serif answer headline (max 3 lines) */}
      <p className="font-serif text-lg sm:text-xl text-ink leading-relaxed font-normal">
        {insightText}
      </p>

      {/* ink-3 takeaway line */}
      {readAs && (
        <p className="text-xs text-ink-3 font-sans italic flex items-center gap-1.5">
          <span>Read as:</span>
          <span className="not-italic text-ink-2 font-medium">{readAs}</span>
        </p>
      )}

      {/* Flags / Anomalies tags */}
      {flags && flags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {flags.map((flag, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono uppercase bg-amber-500/10 text-warn border border-warn/20"
            >
              <AlertCircle className="w-3 h-3 text-warn" />
              <span>{flag}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
