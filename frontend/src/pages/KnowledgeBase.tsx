import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card, Status, Empty, Spinner, Pill } from '../components/ui'
import type { KnowledgeDoc } from '../types'

export function KnowledgeBase() {
  const [docs, setDocs] = useState<KnowledgeDoc[]>([])
  const [loading, setLoading] = useState(true)
  const [lang, setLang] = useState('all')
  const [ingesting, setIngesting] = useState(false)
  const [note, setNote] = useState('')

  const load = () => api.kbDocuments().then(setDocs).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  if (loading) return <Spinner />

  const rows = docs.filter((d) => lang === 'all' || d.language === lang)
  const totalChars = docs.reduce((s, d) => s + d.char_count, 0)
  const totalChunks = docs.reduce((s, d) => s + d.chunk_count, 0)

  const ingest = async () => {
    setIngesting(true)
    try { const r = await api.ingestKb(); setNote(`Ingested ${r.ingested}, unchanged ${r.unchanged}, chunks ${r.chunks}`); await load() }
    catch (e: any) { setNote(e.message) }
    setIngesting(false)
  }

  return (
    <>
      <PageHeader title="Knowledge Base" description={`${docs.length} documents · ${totalChars.toLocaleString()} characters · ${totalChunks} chunks`}
        action={<button className="btn-primary" disabled={ingesting} onClick={ingest}>{ingesting ? 'Indexing…' : 'Re-index documents'}</button>} />
      {note && <div className="mb-4 rounded border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">{note}</div>}
      <div className="mb-4 flex gap-2">{['all', 'en', 'hi', 'gu'].map((l) => <Pill key={l} active={lang === l} onClick={() => setLang(l)}>{l}</Pill>)}</div>
      <Card>
        {rows.length === 0 ? <Empty text="No documents indexed. Run re-index." /> : (
          <table className="table"><thead><tr><th>Document</th><th>Language</th><th>Characters</th><th>Chunks</th><th>Status</th><th>Indexed</th></tr></thead>
            <tbody>{rows.map((d) => <tr key={d.id}><td className="font-mono text-xs text-slate-300">{d.id}</td><td>{d.language}</td><td className="font-mono">{d.char_count.toLocaleString()}</td><td className="font-mono">{d.chunk_count}</td><td><Status value={d.status} /></td><td className="text-xs">{d.indexed_at ? new Date(d.indexed_at).toLocaleString() : '—'}</td></tr>)}</tbody>
          </table>
        )}
      </Card>
      <Card title="Retrieval pipeline" className="mt-4" subtitle="Hybrid BM25 + dense embeddings fused with Reciprocal Rank Fusion">
        <div className="grid gap-3 text-xs md:grid-cols-4">
          {[['Chunk size', '300–500 tokens'], ['Overlap', '50 tokens'], ['Fusion', 'RRF (k=60)'], ['Grounding threshold', '0.50']].map(([k, v]) => (
            <div key={k} className="rounded border border-white/5 p-3"><div className="label">{k}</div><div className="text-slate-300">{v}</div></div>
          ))}
        </div>
      </Card>
    </>
  )
}
