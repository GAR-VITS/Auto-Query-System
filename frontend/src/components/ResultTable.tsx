import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, ChevronDown, ChevronUp } from 'lucide-react';
import { formatNumber, isNumeric } from '../lib/format';

interface ResultTableProps {
  columns: string[];
  rows: any[][];
  rowCount?: number;
  truncated?: boolean;
}

export const ResultTable: React.FC<ResultTableProps> = ({
  columns = [],
  rows = [],
  rowCount,
  truncated = false,
}) => {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [showAll, setShowAll] = useState(false);

  const totalRows = rowCount ?? rows.length;

  const handleSort = (colIndex: number) => {
    if (sortCol === colIndex) {
      if (sortDir === 'asc') {
        setSortDir('desc');
      } else {
        setSortCol(null);
        setSortDir('asc');
      }
    } else {
      setSortCol(colIndex);
      setSortDir('asc');
    }
  };

  const sortedRows = useMemo(() => {
    if (sortCol === null) return rows;
    const sorted = [...rows].sort((a, b) => {
      const valA = a[sortCol];
      const valB = b[sortCol];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDir === 'asc' ? valA - valB : valB - valA;
      }
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      return sortDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
    return sorted;
  }, [rows, sortCol, sortDir]);

  const displayedRows = showAll ? sortedRows : sortedRows.slice(0, 10);

  const downloadCsv = () => {
    if (!columns.length || !rows.length) return;
    const escapeCsv = (val: any) => {
      if (val === null || val === undefined) return '';
      const str = String(val).replace(/"/g, '""');
      return str.includes(',') || str.includes('\n') || str.includes('"') ? `"${str}"` : str;
    };

    const header = columns.map(escapeCsv).join(',');
    const body = rows.map((r) => r.map(escapeCsv).join(',')).join('\n');
    const blob = new Blob([`${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `nexusdb_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!columns.length || !rows.length) {
    return (
      <div className="py-6 text-center text-xs font-mono text-ink-3 border border-line rounded-lg">
        0 rows returned
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      {/* Table Action Bar */}
      <div className="flex items-center justify-between text-xs text-ink-2 px-1">
        <span className="font-mono text-[11px] uppercase tracking-wider">
          Showing {displayedRows.length} of {totalRows} row{totalRows !== 1 ? 's' : ''}
          {truncated && ' (capped at 1,000)'}
        </span>
        <button
          type="button"
          onClick={downloadCsv}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded border border-line hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer text-ink font-mono"
        >
          <Download className="w-3.5 h-3.5 text-ink-3" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Scrollable Container with Sticky Header */}
      <div className="w-full border border-line rounded-lg overflow-hidden bg-surface">
        <div className="max-h-[420px] overflow-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-surface z-10 border-b border-line shadow-xs">
              <tr>
                {columns.map((col, idx) => (
                  <th
                    key={idx}
                    onClick={() => handleSort(idx)}
                    className="py-2.5 px-3 text-[11px] font-mono uppercase tracking-wider text-ink-2 font-medium cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 select-none transition-colors border-r border-line last:border-r-0 whitespace-nowrap"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span>{col}</span>
                      <span className="text-ink-3">
                        {sortCol === idx ? (
                          sortDir === 'asc' ? (
                            <ArrowUp className="w-3 h-3 text-accent" />
                          ) : (
                            <ArrowDown className="w-3 h-3 text-accent" />
                          )
                        ) : (
                          <ArrowUpDown className="w-2.5 h-2.5 opacity-40 hover:opacity-100" />
                        )}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {displayedRows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors"
                >
                  {row.map((cell, cIdx) => {
                    const isNum = isNumeric(cell);
                    return (
                      <td
                        key={cIdx}
                        className={`py-2 px-3 border-r border-line last:border-r-0 whitespace-nowrap ${
                          isNum ? 'text-right font-mono text-ink' : 'text-left text-ink-2'
                        }`}
                      >
                        {formatNumber(cell)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer Expand Button if > 10 rows */}
        {rows.length > 10 && (
          <div className="p-2 border-t border-line bg-black/[0.01] dark:bg-white/[0.01] flex justify-center">
            <button
              type="button"
              onClick={() => setShowAll(!showAll)}
              className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-mono text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 rounded transition-colors cursor-pointer"
            >
              {showAll ? (
                <>
                  <ChevronUp className="w-3.5 h-3.5" />
                  <span>Collapse to 10 rows</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-3.5 h-3.5" />
                  <span>Show all {totalRows} rows</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
