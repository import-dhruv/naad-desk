import type { CallSummary, CallDetail, Finding, KnowledgeDoc, EvalRun } from '../types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json() as Promise<T>
}

export const api = {
  health: () => get<any>('/health'),
  config: () => get<any>('/config'),
  calls: () => get<CallSummary[]>('/calls'),
  call: (id: string) => get<CallDetail>(`/calls/${id}`),
  analyze: (id: string) => post<any>(`/calls/${id}/analyze`),
  findings: () => get<Finding[]>('/findings'),
  createFinding: (body: Partial<Finding>) => post<Finding>('/findings', body),
  kbDocuments: () => get<KnowledgeDoc[]>('/kb/documents'),
  ingestKb: () => post<any>('/kb/ingest'),
  evalRuns: () => get<EvalRun[]>('/eval/runs'),
  runEval: (kind: string) => post<any>('/eval/run', { kind }),
  exportFindings: () => `${BASE}/findings/export.md`,
}
