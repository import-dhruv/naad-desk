import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Status, Empty, Spinner, Bar } from '../components/ui'
import type { CallDetail as Detail } from '../types'

export function CallDetail() {
  const { id } = useParams()
  const [call, setCall] = useState<Detail | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

  const load = () => api.call(id!).then(setCall).finally(() => setLoading(false))
  useEffect(() => { load() }, [id])

  if (loading) return <Spinner />
  if (!call) return <Empty text="Call not found." />

  const analytics = call.analytics
  const qa = analytics?.qa
  const extraction = analytics?.extraction

  const analyze = async () => { setAnalyzing(true); await api.analyze(id!); await load(); setAnalyzing(false) }

  return (
    <>
      <PageHeader title={`Call ${call.id}`} description={`${new Date(call.started_at).toLocaleString()} · ${call.language}`}
        action={<button className="btn-ghost" onClick={analyze} disabled={analyzing}>{analyzing ? 'Analyzing…' : 'Re-run analysis'}</button>} />
      <div className="mb-4 flex flex-wrap gap-2 text-xs">
        <Status value={call.outcome} />
        <span className="badge bg-white/5 text-slate-400">QA <span className="ml-1 text-slate-200">{call.qa_score ?? '—'}</span></span>
        <span className="badge bg-white/5 text-slate-400">Cost <span className="ml-1 text-slate-200">₹{(call.cost_paise / 100).toFixed(2)}</span></span>
        <span className="badge bg-white/5 text-slate-400">Duration <span className="ml-1 text-slate-200">{call.duration_seconds ? `${Math.round(call.duration_seconds)}s` : '—'}</span></span>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Transcript" subtitle="Called turns as stored">
          {call.turns.length === 0 ? <Empty text="No turns recorded." /> : <div className="scroll-thin max-h-96 space-y-2 overflow-y-auto">
            {call.turns.map((t) => <div key={t.idx} className={`rounded p-2 text-sm ${t.speaker === 'caller' ? 'bg-accent-soft/20 text-cyan-100' : 'bg-white/5 text-slate-300'}`}>
              <span className="mr-2 text-[10px] uppercase tracking-wider opacity-60">{t.speaker} #{t.idx}</span>{t.text}
            </div>)}
          </div>}
        </Card>
        <Card title="Three-bullet summary" subtitle={analytics ? 'Generated in the primary language' : 'Not yet analyzed'}>
          {analytics?.summary ? <pre className="whitespace-pre-wrap font-sans text-sm text-slate-300">{analytics.summary}</pre> : <Empty text="Run analysis to generate a summary." />}
        </Card>

        <Card title="Recordings" subtitle="Dual-channel, lossless WAV">
          <div className="space-y-3">
            {(['caller', 'agent'] as const).map((ch) => (
              <div key={ch}>
                <div className="label">{ch} channel · {ch === 'caller' ? '16 kHz' : '24 kHz'}</div>
                <audio controls className="w-full" src={`/api/calls/${call.id}/recording/${ch}`} />
              </div>
            ))}
          </div>
        </Card>
        <Card title="QA breakdown" subtitle="Machine-judged rubric">
          {qa ? <div className="space-y-3">{Object.entries(qa.breakdown).map(([k, v]: any) => (
            <div key={k}><div className="flex justify-between text-xs"><span className="text-slate-400">{k.replace(/_/g, ' ')}</span><span className="font-mono text-slate-300">{v.score}/{v.max} <span className="text-slate-600">· {v.judge}</span></span></div><Bar value={v.score} max={v.max} /></div>
          ))}<div className="pt-2 text-sm font-semibold text-cyan-300">Total {qa.total}/100</div></div> : <Empty text="No QA scores yet." />}
        </Card>

        <Card title="Extracted JSON"><pre className="scroll-thin max-h-80 overflow-auto rounded bg-ink-950 p-3 text-[11px] text-slate-400">{JSON.stringify(extraction || {}, null, 2)}</pre></Card>
        <Card title="Merged transcript" subtitle="Timestamps are ESTIMATED (no diarization)">
          {analytics?.merged_transcript?.length ? <div className="scroll-thin max-h-80 space-y-1 overflow-y-auto font-mono text-xs">{analytics.merged_transcript.map((t: any) => (
            <div key={t.idx}><span className="text-slate-600">[{t.start}–{t.end} est]</span> <span className={t.speaker === 'caller' ? 'text-cyan-300' : 'text-slate-300'}>{t.speaker}:</span> {t.text}</div>
          ))}</div> : <Empty text="No merged transcript yet." />}
        </Card>

        <Card title="Tool execution history">{call.tool_calls.length === 0 ? <Empty text="No tools called." /> : call.tool_calls.map((t, i) => (
          <div key={i} className="mb-2 rounded border border-white/5 p-2 text-xs"><span className="text-cyan-300">{t.name}</span><pre className="mt-1 text-slate-500">{JSON.stringify(t.result).slice(0, 200)}</pre></div>
        ))}</Card>
        <Card title="Retrieved knowledge chunks">{call.retrievals.length === 0 ? <Empty text="No retrievals." /> : call.retrievals.map((r, i) => (
          <div key={i} className="mb-2 rounded border border-white/5 p-2 text-xs">conf {r.confidence.toFixed(2)} · {r.execution_time_ms} ms · {r.chunk_ids.length} chunks</div>
        ))}</Card>

        <Card title="Latency waterfall" className="xl:col-span-2">{call.turns.length === 0 ? <Empty text="No timing data." /> : (
          <div className="table-wrap"><table className="table"><thead><tr><th>Turn</th><th>Speaker</th>{Object.keys(call.turns[0].timings || {}).map((k) => <th key={k}>{k.replace('t_', '')}</th>)}</tr></thead>
            <tbody>{call.turns.map((t) => <tr key={t.idx}><td>{t.idx}</td><td>{t.speaker}</td>{Object.keys(call.turns[0].timings || {}).map((k) => <td key={k} className="font-mono">{t.timings?.[k] ?? '—'}</td>)}</tr>)}</tbody>
          </table></div>
        )}</Card>
      </div>
    </>
  )
}
