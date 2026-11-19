import type { ReactNode } from 'react'

export function Card({ title, subtitle, action, children, className = '' }: {
  title?: string; subtitle?: string; action?: ReactNode; children: ReactNode; className?: string
}) {
  return (
    <section className={`card p-4 ${className}`}>
      {(title || action) && (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-slate-200">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  )
}

export function Kpi({ label, value, hint, tone = 'default' }: {
  label: string; value: string | number; hint?: string; tone?: 'default' | 'accent' | 'warn'
}) {
  const color = tone === 'accent' ? 'text-cyan-300' : tone === 'warn' ? 'text-amber-300' : 'text-slate-100'
  return (
    <div className="card p-4">
      <div className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`kpi mt-2 ${color}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

export function Status({ value }: { value: string }) {
  const map: Record<string, string> = {
    completed: 'bg-emerald-900/40 text-emerald-300',
    analyzed: 'bg-emerald-900/40 text-emerald-300',
    in_progress: 'bg-cyan-900/40 text-cyan-300',
    safety_escalation: 'bg-rose-900/40 text-rose-300',
    open: 'bg-amber-900/40 text-amber-300',
    high: 'bg-rose-900/40 text-rose-300',
    medium: 'bg-amber-900/40 text-amber-300',
    low: 'bg-sky-900/40 text-sky-300',
    suggestion: 'bg-violet-900/40 text-violet-300',
  }
  return <span className={`badge ${map[value] ?? 'bg-white/5 text-slate-400'}`}>{value}</span>
}

export function Empty({ text }: { text: string }) {
  return <div className="flex min-h-24 items-center justify-center rounded border border-dashed border-white/10 text-sm text-slate-600">{text}</div>
}

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return <div className="flex items-center gap-2 py-8 text-sm text-slate-500"><span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />{label}</div>
}

export function Bar({ value, max = 100, color = 'bg-accent-soft' }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5"><div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} /></div>
}

export function Pill({ children, active, onClick }: { children: ReactNode; active?: boolean; onClick?: () => void }) {
  return <button onClick={onClick} className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${active ? 'bg-accent-soft text-white' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}>{children}</button>
}
