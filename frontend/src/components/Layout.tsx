import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Phone, History, FlaskConical, Flag, BookOpen, Settings, AudioLines, Menu, X,
} from 'lucide-react'

const NAV = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/live', label: 'Live Calls', icon: Phone },
  { to: '/calls', label: 'Call History', icon: History },
  { to: '/eval', label: 'Evaluation Lab', icon: FlaskConical },
  { to: '/findings', label: 'Findings', icon: Flag },
  { to: '/kb', label: 'Knowledge Base', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-accent-soft text-white"><AudioLines size={18} /></div>
      <div className="min-w-0">
        <div className="truncate text-sm font-semibold tracking-tight text-slate-100">Naad Desk</div>
        <div className="truncate text-[10px] uppercase tracking-wider text-slate-600">Voice AI Engineering</div>
      </div>
    </div>
  )
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      <div className="flex items-center justify-between px-5 py-5 lg:justify-start">
        <Brand />
        <button className="btn-ghost p-1.5 lg:hidden" onClick={onNavigate} aria-label="Close menu">
          <X size={18} />
        </button>
      </div>
      <nav className="mt-2 flex-1 space-y-0.5 overflow-y-auto px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} onClick={onNavigate} className={({ isActive }) =>
            `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors lg:py-2 ${isActive ? 'bg-white/[0.07] text-cyan-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}>
            <Icon size={16} className="shrink-0" /><span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/[0.07] px-5 py-4 text-[11px] text-slate-600">
        <div>Sharma Clinic · Synthetic demo</div>
        <div className="mt-1 font-mono">v1.0.0 · naad-sts-v2</div>
      </div>
    </>
  )
}

export function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  useEffect(() => { setOpen(false) }, [location.pathname])

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-ink-950">
      {open && <button className="fixed inset-0 z-40 bg-black/65 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu" />}

      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[280px] max-w-[85vw] shrink-0 flex-col border-r border-white/[0.07] bg-ink-900 transition-transform duration-200 lg:static lg:z-auto lg:w-60 lg:max-w-none lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <Sidebar onNavigate={() => setOpen(false)} />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center gap-3 border-b border-white/[0.07] bg-ink-900 px-4 py-3 lg:hidden">
          <button className="btn-ghost p-1.5" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={18} /></button>
          <Brand />
        </header>
        <main className="scroll-thin min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1500px] px-4 py-5 sm:px-7 sm:py-7"><Outlet /></div>
        </main>
      </div>
    </div>
  )
}

export function PageHeader({ title, description, action }: {
  title: string; description?: string; action?: React.ReactNode
}) {
  return (
    <header className="mb-5 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
      <div className="min-w-0">
        <h1 className="text-lg font-semibold tracking-tight text-slate-100 sm:text-xl">{title}</h1>
        {description && <p className="mt-1 text-xs leading-relaxed text-slate-500 sm:text-sm">{description}</p>}
      </div>
      {action && <div className="flex flex-wrap items-center gap-2">{action}</div>}
    </header>
  )
}
