export type ServerMessage = {
  type: string
  call_id?: string
  ts?: number
  payload: Record<string, any>
}

export type TurnTiming = { label: string; ms: number }

export type Caption = {
  id: number
  speaker: 'caller' | 'agent' | 'system'
  text: string
  language?: string
  final: boolean
  time: string
}

export type CallSummary = {
  id: string
  started_at: string
  ended_at: string | null
  language: string
  outcome: string
  qa_score: number | null
  cost_paise: number
  duration_seconds: number | null
}

export type CallDetail = CallSummary & {
  turns: any[]
  tool_calls: any[]
  retrievals: any[]
  analytics: any
  api_calls: any[]
  recordings: { caller: string; agent: string }
}

export type Finding = {
  id: string
  title: string
  severity: string
  area: string
  expected: string
  actual: string
  reproduction_steps: string
  evidence_path: string
  suggestion: string
  status: string
  kind: string
  created_at: string | null
}

export type KnowledgeDoc = {
  id: string
  source: string
  language: string
  title: string
  char_count: number
  chunk_count: number
  indexed_at: string | null
  status: string
}

export type EvalRun = {
  id: string
  kind: string
  started_at: string | null
  config: Record<string, any>
  metrics: Record<string, any>
  git_sha: string
  sample_count: number
}
