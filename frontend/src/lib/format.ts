/**
 * Formatting Utilities for Indian Currency (INR) and Numbers
 */

export function formatINR(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) return '—';
  const num = Number(val);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(num);
}

export const formatCurrency = formatINR;

export function isNumeric(val: any): boolean {
  if (typeof val === 'number') return true;
  if (typeof val !== 'string') return false;
  return !isNaN(Number(val)) && !isNaN(parseFloat(val)) && val.trim() !== '';
}

export function formatNumber(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) return String(val ?? '');
  const num = Number(val);
  return new Intl.NumberFormat('en-IN').format(num);
}

export function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return ts;
  }
}
