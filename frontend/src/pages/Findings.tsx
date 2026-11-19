import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Status, Empty, Spinner, Pill } from '../components/ui'
import type { Finding } from '../types'

export function Findings() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [severity, setSeverity] = useState('all')
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState<Finding | null>(null)

  useEffect(() => { api.findings().then(setFindings).finally(() => setLoading(false)) }, [])
  if (loading) return <Spinner />

  const rows = findings.filter((f) => (severity === 'all' || f.severity === severity) && (f.title + f.area).toLowerCase().includes(q.toLowerCase()))

  return (
    <>
      <PageHeader title="Findings" description="Evidence-backed platform observations from reconnaissance. No invented bugs."
        action={<a className="btn-ghost" href={api.exportFindings()} target="_blank" rel="noreferrer">Export Markdown</a>} />
      <div className="mb-4 flex flex-wrap gap-2">
        {['all', 'high', 'medium', 'low', 'suggestion'].map((s) => <Pill key={s} active={severity === s} onClick={() => setSeverity(s)}>{s}</Pill>)}
        <input className="input ml-auto max-w-xs" placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
        <Card title={`${rows.length} findings`}>
          {rows.length === 0 ? <Empty text="No findings match these filters." /> : <div className="space-y-2">
            {rows.map((f) => <button onClick={() => setSelected(f)} key={f.id} className={`w-full rounded border p-3 text-left transition-colors ${selected?.id === f.id ? 'border-accent-soft bg-white/[0.05]' : 'border-white/5 hover:bg-white/[0.03]'}`}>
              <div className="flex items-center gap-2"><Status value={f.severity} /><span className="font-mono text-xs text-slate-500">{f.id}</span><span className="ml-auto text-[11px] text-slate-600">{f.area}</span></div>
              <div className="mt-1.5 text-sm text-slate-200">{f.title}</div>
              <div className="mt-1 text-xs text-slate-500">{f.kind} · {f.status}</div>
            </button>)}
          </div>}
        </Card>
        <Card title={selected ? `${selected.id} · ${selected.title}` : 'Finding details'}>
          {!selected ? <Empty text="Select a finding to see evidence, reproduction steps and suggested fixes." /> : (
            <div className="space-y-4 text-sm">
              <div className="flex gap-2"><Status value={selected.severity} /><Status value={selected.kind} /><Status value={selected.status} /></div>
              {[['Expected', selected.expected], ['Actual', selected.actual], ['Reproduction', selected.reproduction_steps], ['Evidence', selected.evidence_path], ['Suggested fix', selected.suggestion]].map(([label, value]) => (
                <div key={label}><div className="label">{label}</div><div className="whitespace-pre-wrap text-slate-300">{value || '—'}</div></div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
