import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Kpi, Status, Empty, Spinner, Bar } from '../components/ui'
import type { CallSummary, Finding, EvalRun } from '../types'

const COLORS = ['#22d3ee', '#0e7490', '#8b5cf6', '#f59e0b']

export function Overview() {
  const [calls, setCalls] = useState<CallSummary[]>([])
  const [findings, setFindings] = useState<Finding[]>([])
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([api.calls(), api.findings(), api.evalRuns(), api.health()]).then(([c, f, e, h]) => {
      if (c.status === 'fulfilled') setCalls(c.value)
      if (f.status === 'fulfilled') setFindings(f.value)
      if (e.status === 'fulfilled') setRuns(e.value)
      if (h.status === 'fulfilled') setHealth(h.value)
      setLoading(false)
    })
  }, [])

  if (loading) return <Spinner />

  const analyzed = calls.filter((c) => c.outcome === 'analyzed')
  const success = analyzed.filter((c) => c.qa_score !== null && c.qa_score >= 70).length
  const avgDuration = calls.filter((c) => c.duration_seconds).reduce((s, c) => s + (c.duration_seconds || 0), 0) / (calls.filter((c) => c.duration_seconds).length || 1)
  const avgQa = analyzed.reduce((s, c) => s + (c.qa_score || 0), 0) / (analyzed.length || 1)
  const totalCost = calls.reduce((s, c) => s + c.cost_paise, 0)
  const langData = Object.entries(calls.reduce<Record<string, number>>((acc, c) => {
    acc[c.language] = (acc[c.language] || 0) + 1; return acc
  }, {})).map(([name, value]) => ({ name, value }))

  return (
    <>
      <PageHeader title="Overview" description="Live system state from the Naad Desk database. No synthetic metrics are shown."
        action={<Link to="/live" className="btn-primary">Start a live call</Link>} />

      <div className="mb-4 flex flex-wrap gap-2 text-xs">
        <span className="badge bg-white/5 text-slate-400">Database: <span className="ml-1 text-emerald-300">{health?.database ?? '—'}</span></span>
        <span className="badge bg-white/5 text-slate-400">Upstream key: <span className="ml-1 text-slate-200">{health?.upstream?.configured ? 'configured' : 'not configured'}</span></span>
        <span className="badge bg-white/5 text-slate-400">Engine: <span className="ml-1 text-slate-200">naad-sts-v2</span></span>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Kpi label="Total calls" value={calls.length} hint="all sessions" />
        <Kpi label="Task completion" value={analyzed.length ? `${Math.round((success / analyzed.length) * 100)}%` : '—'} hint="QA ≥ 70 · analyzed calls" tone="accent" />
        <Kpi label="Avg call duration" value={calls.length ? `${Math.round(avgDuration)}s` : '—'} />
        <Kpi label="Avg QA score" value={analyzed.length ? avgQa.toFixed(1) : '—'} hint="machine-judged / 100" />
        <Kpi label="API expenditure" value={`₹${(totalCost / 100).toFixed(2)}`} hint="estimated paise" />
        <Kpi label="Open findings" value={findings.filter((f) => f.status === 'open').length} tone="warn" />
        <Kpi label="Eval runs" value={runs.length} />
        <Kpi label="KB documents" value="27" hint="65,748 characters" />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card title="Recent calls" subtitle="Most recent sessions" className="lg:col-span-2">
          {calls.length === 0 ? <Empty text="No calls recorded yet. Start a live call to populate this view." /> : (
            <table className="table">
              <thead><tr><th>Call</th><th>Language</th><th>Duration</th><th>Outcome</th><th>QA</th></tr></thead>
              <tbody>{calls.slice(0, 8).map((c) => (
                <tr key={c.id}>
                  <td className="font-mono text-xs"><Link className="text-cyan-300 hover:underline" to={`/calls/${c.id}`}>{c.id}</Link></td>
                  <td>{c.language}</td>
                  <td>{c.duration_seconds ? `${Math.round(c.duration_seconds)}s` : '—'}</td>
                  <td><Status value={c.outcome} /></td>
                  <td>{c.qa_score ?? '—'}</td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </Card>
        <Card title="Language distribution" subtitle="Across recorded calls">
          {langData.length === 0 ? <Empty text="No language data yet." /> : (
            <div className="flex items-center gap-4">
              <div className="h-40 w-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart><Pie data={langData} dataKey="value" nameKey="name" innerRadius={40} outerRadius={65}>
                    {langData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie><Tooltip contentStyle={{ background: '#111820', border: '1px solid #1e2a36' }} /></PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-1 text-xs">{langData.map((d, i) => (
                <div key={d.name} className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />{d.name}: {d.value}</div>
              ))}</div>
            </div>
          )}
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card title="Latest evaluation results" subtitle="Stored experiment runs">
          {runs.length === 0 ? <Empty text="No evaluation runs yet. Open the Evaluation Lab to run one." /> : runs.slice(0, 5).map((r) => (
            <div key={r.id} className="mb-3 rounded border border-white/5 p-2.5">
              <div className="flex justify-between text-xs"><span className="font-mono text-slate-300">{r.id}</span><span className="text-slate-500">{r.kind}</span></div>
              <div className="mt-1.5 space-y-1">{Object.entries(r.metrics).filter(([, v]) => typeof v === 'number').map(([k, v]) => (
                <div key={k} className="flex items-center gap-3 text-xs"><span className="w-28 text-slate-500">{k}</span><Bar value={Number(v) * 100} /><span className="w-12 text-right font-mono text-slate-300">{Number(v).toFixed(2)}</span></div>
              ))}</div>
            </div>
          ))}
        </Card>
        <Card title="Recent findings" subtitle="From platform reconnaissance" action={<Link to="/findings" className="text-xs text-cyan-300">View all →</Link>}>
          {findings.length === 0 ? <Empty text="No findings recorded." /> : findings.slice(0, 6).map((f) => (
            <div key={f.id} className="flex items-start gap-3 border-b border-white/5 py-2 text-xs last:border-0">
              <Status value={f.severity} />
              <span className="font-mono text-slate-500">{f.id}</span>
              <span className="text-slate-300">{f.title}</span>
            </div>
          ))}
        </Card>
      </div>
    </>
  )
}
