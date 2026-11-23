import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

export function Input({ label, className = '', id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-slate-400">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`rounded-xl border border-surface-600 bg-surface-800/80 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20 ${className}`}
        {...props}
      />
    </div>
  )
}
