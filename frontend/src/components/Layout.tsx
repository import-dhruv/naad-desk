import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Phone, History, FlaskConical, Flag, BookOpen, Settings, AudioLines,
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

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-ink-950">
      <aside className="flex w-60 shrink-0 flex-col border-r border-white/[0.07] bg-ink-900">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent-soft text-white"><AudioLines size={18} /></div>
          <div>
            <div className="text-sm font-semibold tracking-tight text-slate-100">Naad Desk</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-600">Voice AI Engineering</div>
          </div>
        </div>
        <nav className="mt-2 flex-1 space-y-0.5 px-3">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${isActive ? 'bg-white/[0.07] text-cyan-300' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}>
              <Icon size={16} />{label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/[0.07] px-5 py-4 text-[11px] text-slate-600">
          <div>Sharma Clinic · Synthetic demo</div>
          <div className="mt-1 font-mono">v1.0.0 · naad-sts-v2</div>
        </div>
      </aside>
      <main className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto max-w-[1500px] px-7 py-7"><Outlet /></div>
      </main>
    </div>
  )
}

export function PageHeader({ title, description, action }: {
  title: string; description?: string; action?: React.ReactNode
}) {
  return (
    <header className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-100">{title}</h1>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {action}
    </header>
  )
}
