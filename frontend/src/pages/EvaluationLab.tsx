import { useEffect, useState } from 'react'
import { BarChart, Bar as RBar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Empty, Spinner, Pill, Bar } from '../components/ui'
import type { EvalRun } from '../types'

export function EvaluationLab() {
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState('')
  const [note, setNote] = useState('')

  const load = () => api.evalRuns().then(setRuns).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const run = async (kind: string) => {
    setRunning(kind); setNote('')
    try { const r = await api.runEval(kind); setNote(`Started ${r.id} · ${JSON.stringify(r.metrics)}`); await load() }
    catch (e: any) { setNote(e.message) }
    setRunning('')
  }

  if (loading) return <Spinner />
  const retrievalRuns = runs.filter((r) => r.kind === 'retrieval')
  const latest = retrievalRuns[0]
  const metricData = latest ? Object.entries(latest.metrics).filter(([, v]) => typeof v === 'number').map(([k, v]) => ({ k, v: Number(v) })) : []

  return (
    <>
      <PageHeader title="Evaluation Lab" description="Reproducible experiments. Charts are generated only from stored experiment records."
        action={<div className="flex gap-2"><button className="btn-ghost" disabled={!!running} onClick={() => run('retrieval')}>{running === 'retrieval' ? 'Running…' : 'Run retrieval eval'}</button><button className="btn-ghost" disabled={!!running} onClick={() => run('wer')}>{running === 'wer' ? 'Running…' : 'Queue WER run'}</button></div>} />
      {note && <div className="mb-4 rounded border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">{note}</div>}

      <div className="grid gap-4 xl:grid-cols-3">
        <Card title="Metric distribution" subtitle={latest ? `Run ${latest.id}` : 'No runs yet'} className="xl:col-span-2">
          {metricData.length === 0 ? <Empty text="Run the retrieval evaluation to generate real metrics." /> : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={metricData}><XAxis dataKey="k" tick={{ fill: '#64748b', fontSize: 10 }} /><YAxis domain={[0, 1]} tick={{ fill: '#64748b', fontSize: 10 }} /><Tooltip contentStyle={{ background: '#111820', border: '1px solid #1e2a36' }} /><RBar dataKey="v" fill="#0e7490" radius={[3, 3, 0, 0]} /></BarChart>
            </ResponsiveContainer>
          )}
        </Card>
        <Card title="Latest metrics" subtitle="From stored run">
          {!latest ? <Empty text="No metrics." /> : <div className="space-y-2">{Object.entries(latest.metrics).map(([k, v]) => (
            <div key={k}><div className="flex justify-between text-xs"><span className="text-slate-400">{k}</span><span className="font-mono text-slate-300">{String(v)}</span></div>{typeof v === 'number' && <Bar value={Number(v) * 100} />}</div>
          ))}<div className="pt-2 text-[11px] text-slate-600">git {latest.git_sha} · {latest.sample_count} samples</div></div>}
        </Card>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Card title="WER by language"><Empty text="WER results appear here after running the WER experiment scripts on the evaluation dataset (240 utterances)." /></Card>
        <Card title="8 kHz / SNR degradation"><Empty text="Degradation results appear here after running the telephone-band experiment. No measurements are fabricated." /></Card>
        <Card title="Latency distribution"><Empty text="Turn-level latency percentiles appear here after collecting ≥100 live turns." /></Card>
        <Card title="TTS streaming comparison"><Empty text="Streaming vs buffered TTFB trials appear here after running the TTS experiment." /></Card>
        <Card title="Language switch matrix"><Empty text="Six language pairs × 5 trials populate this matrix after the switching experiment." /></Card>
        <Card title="Bootstrap confidence intervals"><Empty text="95% CIs are computed by eval/metrics/bootstrap.py from utterance-level values." /></Card>
      </div>

      <Card title="Experiment runs" className="mt-4" subtitle={`${runs.length} stored runs`}>
        {runs.length === 0 ? <Empty text="No experiment runs stored." /> : (
          <table className="table"><thead><tr><th>ID</th><th>Kind</th><th>Started</th><th>Samples</th><th>Git SHA</th><th>Metrics</th></tr></thead>
            <tbody>{runs.map((r) => <tr key={r.id}><td className="font-mono text-xs text-cyan-300">{r.id}</td><td>{r.kind}</td><td className="text-xs">{r.started_at ? new Date(r.started_at).toLocaleString() : '—'}</td><td>{r.sample_count}</td><td className="font-mono text-xs">{r.git_sha}</td><td className="text-xs">{JSON.stringify(r.metrics).slice(0, 90)}</td></tr>)}</tbody>
          </table>
        )}
      </Card>
    </>
  )
}
