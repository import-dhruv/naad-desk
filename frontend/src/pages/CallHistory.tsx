import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter } from 'lucide-react'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Status, Empty, Spinner, Pill } from '../components/ui'
import type { CallSummary } from '../types'

export function CallHistory() {
  const [calls, setCalls] = useState<CallSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [lang, setLang] = useState('all')

  useEffect(() => { api.calls().then(setCalls).finally(() => setLoading(false)) }, [])
  if (loading) return <Spinner />

  const langs = Array.from(new Set(calls.map((c) => c.language)))
  const rows = calls.filter((c) => (lang === 'all' || c.language === lang) && c.id.toLowerCase().includes(q.toLowerCase()))

  return (
    <>
      <PageHeader title="Call History" description={`${calls.length} recorded sessions`} />
      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative flex-1"><Search className="absolute left-2.5 top-2.5 text-slate-600" size={14} /><input className="input pl-8" placeholder="Search call ID…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
          <Filter size={14} className="text-slate-600" />
          <Pill active={lang === 'all'} onClick={() => setLang('all')}>All</Pill>
          {langs.map((l) => <Pill key={l} active={lang === l} onClick={() => setLang(l)}>{l}</Pill>)}
        </div>
        {rows.length === 0 ? <Empty text="No calls match these filters." /> : (
          <table className="table">
            <thead><tr><th>Call ID</th><th>Date</th><th>Language</th><th>Duration</th><th>Outcome</th><th>QA score</th><th>API cost</th></tr></thead>
            <tbody>{rows.map((c) => (
              <tr key={c.id} className="hover:bg-white/[0.03]">
                <td className="font-mono text-xs"><Link className="text-cyan-300 hover:underline" to={`/calls/${c.id}`}>{c.id}</Link></td>
                <td className="text-xs">{new Date(c.started_at).toLocaleString()}</td>
                <td>{c.language}</td>
                <td className="font-mono">{c.duration_seconds ? `${Math.round(c.duration_seconds)}s` : '—'}</td>
                <td><Status value={c.outcome} /></td>
                <td>{c.qa_score ?? '—'}</td>
                <td className="font-mono">₹{(c.cost_paise / 100).toFixed(2)}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </Card>
    </>
  )
}
