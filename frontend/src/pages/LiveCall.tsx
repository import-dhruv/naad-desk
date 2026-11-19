import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff, PhoneOff, Play, Circle, Activity, Zap } from 'lucide-react'
import { PageHeader } from '../components/Layout'
import { Card, Status, Empty, Pill } from '../components/ui'
import { CallSocket } from '../websocket/callSocket'
import { AudioCapture, pcm16ToBase64 } from '../audio/capture'
import { PlaybackScheduler } from '../audio/playback'
import { api } from '../services/api'
import type { Caption, ServerMessage, TurnTiming } from '../types'

type Phase = 'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking' | 'ended'

export function LiveCall() {
  const [language, setLanguage] = useState('hi')
  const [phase, setPhase] = useState<Phase>('idle')
  const [callId, setCallId] = useState<string | null>(null)
  const [captions, setCaptions] = useState<Caption[]>([])
  const [timings, setTimings] = useState<Record<string, number>>({})
  const [retrievals, setRetrievals] = useState<any[]>([])
  const [tools, setTools] = useState<any[]>([])
  const [vad, setVad] = useState<string[]>([])
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState('')
  const [micOn, setMicOn] = useState(true)
  // Ref mirrors the state so the long-lived AudioWorklet callback always sees
  // the current mute value instead of the one captured when start() ran.
  const micOnRef = useRef(true)
  const [config, setConfig] = useState<any>(null)

  const socket = useRef<CallSocket | null>(null)
  const capture = useRef<AudioCapture | null>(null)
  const playback = useRef<PlaybackScheduler | null>(null)
  const captionEnd = useRef<HTMLDivElement>(null)
  const startedAt = useRef(0)
  const seq = useRef(0)

  useEffect(() => { api.config().then(setConfig).catch(() => {}) }, [])
  useEffect(() => { const t = setInterval(() => { if (startedAt.current) setElapsed(Math.floor((Date.now() - startedAt.current) / 1000)) }, 500); return () => clearInterval(t) }, [])
  useEffect(() => { captionEnd.current?.scrollIntoView({ behavior: 'smooth' }) }, [captions])

  const addCaption = (c: Omit<Caption, 'id' | 'time'>) =>
    setCaptions((prev) => [...prev, { ...c, id: Date.now() + Math.random(), time: new Date().toLocaleTimeString() }])

  const handleMessage = (msg: ServerMessage) => {
    const p = msg.payload || {}
    if (msg.type === 'session.ready') {
      setCallId(msg.call_id || null); setPhase('listening'); startedAt.current = Date.now()
      addCaption({ speaker: 'system', text: `Session ready · voice ${p.voice} · ${p.language}`, final: true })
    } else if (msg.type === 'recording.notice') {
      addCaption({ speaker: 'system', text: `Recording notice: ${p.text}`, final: true })
    } else if (msg.type === 'caption') {
      const speaker = p.speaker as 'caller' | 'agent' | 'system'
      setCaptions((prev) => {
        const last = prev[prev.length - 1]
        if (last && last.speaker === speaker && !last.final && !p.final) {
          return [...prev.slice(0, -1), { ...last, text: p.text }]
        }
        return [...prev, { id: Date.now() + Math.random(), speaker, text: p.text, final: p.final, time: new Date().toLocaleTimeString() }]
      })
    } else if (msg.type === 'audio') {
      playback.current?.enqueue(p.data)
    } else if (msg.type === 'state') {
      const value = p.value as Phase
      if (['listening', 'thinking', 'speaking'].includes(value)) setPhase(value)
      setVad((prev) => [...prev.slice(-12), `${new Date().toLocaleTimeString()}: ${value}`])
    } else if (msg.type === 'timing') {
      setTimings((prev) => ({ ...prev, ...p }))
    } else if (msg.type === 'retrieval') {
      setRetrievals((prev) => [...prev.slice(-8), p])
    } else if (msg.type === 'tool') {
      setTools((prev) => [...prev.slice(-8), ...(p.calls || [])])
    } else if (msg.type === 'stop_playback') {
      playback.current?.flush()
      setVad((prev) => [...prev.slice(-12), `${new Date().toLocaleTimeString()}: barge-in (${p.reason})`])
    } else if (msg.type === 'error') {
      setError(p.detail || 'Unknown error')
    } else if (msg.type === 'call.ended') {
      setPhase('ended')
      if (msg.call_id) api.analyze(msg.call_id).catch(() => {})
    }
  }

  const start = async () => {
    setError(''); setCaptions([]); setTimings({}); setVad([]); setRetrievals([]); setTools([])
    setPhase('connecting')
    try {
      playback.current = new PlaybackScheduler()
      await playback.current.ensure()
      const sock = new CallSocket()
      sock.onMessage = handleMessage
      sock.onClose = () => setPhase((p) => p === 'ended' ? p : 'ended')
      await sock.connect(language)
      socket.current = sock
      const cap = new AudioCapture((pcm) => {
        if (socket.current && micOnRef.current) socket.current.send({ v: 1, type: 'audio', data: pcm16ToBase64(pcm), seq: seq.current++ })
      })
      await cap.start()
      capture.current = cap
    } catch (e: any) {
      setError(e.message || 'Could not start call'); setPhase('idle')
    }
  }

  const end = () => {
    socket.current?.close(); socket.current = null
    capture.current?.stop(); capture.current = null
    playback.current?.stop(); playback.current = null
    setPhase('ended')
  }

  const sendText = (text: string) => {
    if (!text.trim()) return
    addCaption({ speaker: 'caller', text, final: true })
    socket.current?.send({ v: 1, type: 'text_input', text })
  }

  const mmss = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
  const estimatedCost = (elapsed / 60) * 0.38

  return (
    <>
      <PageHeader title="Live Calls" description="Real-time, interruptible multilingual voice agent · external_brain mode"
        action={<div className="flex items-center gap-2">
          <span className={`badge ${phase === 'idle' || phase === 'ended' ? 'bg-white/5 text-slate-400' : 'bg-emerald-900/40 text-emerald-300'}`}>
            <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" />{phase}
          </span>
          {phase === 'idle' || phase === 'ended' ? (
            <button className="btn-primary" onClick={start}><Play size={14} /> Start call</button>
          ) : <button className="btn-danger" onClick={end}><PhoneOff size={14} /> End call</button>}
        </div>} />

      {error && <div className="mb-4 rounded border border-rose-900/50 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">{error}</div>}
      {config && !config.upstream_configured && <div className="mb-4 rounded border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">Upstream key is not configured on the server. Set OOGAM_API_KEY in .env and restart the backend.</div>}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="space-y-4">
          <Card title="Conversation" subtitle="Live captions and conversation state">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="label mr-1">Language</span>
              {[['hi', 'Hindi'], ['gu', 'Gujarati'], ['en-in', 'Indian English']].map(([code, label]) => (
                <Pill key={code} active={language === code} onClick={() => { setLanguage(code); socket.current?.send({ v: 1, type: 'set_lang', language: code }) }}>{label}</Pill>
              ))}
              <span className="ml-auto font-mono text-xs text-slate-500">{mmss(elapsed)}</span>
            </div>
            <div className="scroll-thin h-[320px] space-y-3 overflow-y-auto rounded border border-white/5 bg-ink-950/50 p-3 sm:h-[420px]">
              {captions.length === 0 && <Empty text="Press Start call to begin. A recording disclosure is spoken and shown automatically." />}
              {captions.map((c) => (
                <div key={c.id} className={`flex ${c.speaker === 'caller' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${c.speaker === 'caller' ? 'bg-accent-soft/30 text-cyan-100' : c.speaker === 'agent' ? 'bg-white/[0.06] text-slate-200' : 'border border-dashed border-white/10 text-xs text-slate-500'}`}>
                    <div className="mb-0.5 text-[10px] uppercase tracking-wider opacity-60">{c.speaker}{!c.final ? ' · …' : ''}</div>
                    {c.text}
                  </div>
                </div>
              ))}
              <div ref={captionEnd} />
            </div>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <button className={`${micOn ? 'btn-ghost' : 'btn-danger'} shrink-0`} onClick={() => setMicOn((m) => {
                micOnRef.current = !m
                return !m
              })}>
                {micOn ? <Mic size={14} /> : <MicOff size={14} />}{micOn ? 'Mic on' : 'Mic muted'}
              </button>
              <form className="flex flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); const input = e.currentTarget.elements.namedItem('text') as HTMLInputElement; sendText(input.value); input.value = '' }}>
                <input name="text" className="input" placeholder="Type a message (scenario replay)…" />
                <button className="btn-ghost" type="submit">Send</button>
              </form>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Call state" subtitle="Realtime instrumentation">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><div className="muted">Call ID</div><div className="font-mono text-slate-300">{callId || '—'}</div></div>
              <div><div className="muted">Duration</div><div className="font-mono text-slate-300">{mmss(elapsed)}</div></div>
              <div><div className="muted">Stage</div><Status value={phase} /></div>
              <div><div className="muted">Est. cost</div><div className="font-mono text-slate-300">₹{estimatedCost.toFixed(3)}</div></div>
            </div>
          </Card>
          <Card title="Turn timeline" subtitle="Stage durations (ms)">
            {Object.keys(timings).length === 0 ? <Empty text="No turn timings yet." /> : (
              <div className="space-y-2">{Object.entries(timings).map(([k, v]) => (
                <div key={k} className="flex items-center gap-3 text-xs"><span className="w-32 text-slate-500">{k}</span><div className="h-1.5 flex-1 rounded-full bg-white/5"><div className="h-full rounded-full bg-accent-soft" style={{ width: `${Math.min(100, v / 30)}%` }} /></div><span className="w-14 text-right font-mono text-slate-300">{v}</span></div>
              ))}</div>
            )}
          </Card>
          <Card title="VAD & barge-in events"><div className="scroll-thin max-h-32 space-y-1 overflow-y-auto font-mono text-[11px] text-slate-500">
            {vad.length === 0 ? <Empty text="No VAD events yet." /> : vad.map((v, i) => <div key={i}>{v}</div>)}
          </div></Card>
          <Card title="Retrieval chunks">{retrievals.length === 0 ? <Empty text="No retrievals yet." /> : retrievals.map((r, i) => (
            <div key={i} className="mb-2 rounded border border-white/5 p-2 text-xs">
              <div className="flex justify-between"><span className="text-cyan-300">conf {r.confidence}</span><span className="text-slate-500">{r.execution_time_ms} ms</span></div>
              {r.chunks?.slice(0, 3).map((c: any) => <div key={c.id} className="mt-1 truncate text-slate-400">{c.id}</div>)}
            </div>
          ))}</Card>
          <Card title="Tool execution trace">{tools.length === 0 ? <Empty text="No tools called yet." /> : tools.map((t, i) => (
            <div key={i} className="mb-2 rounded border border-white/5 p-2 text-xs"><span className="text-cyan-300">{t.name}</span> <span className={t.ok ? 'text-emerald-400' : 'text-rose-400'}>{t.ok ? 'ok' : 'failed'}</span></div>
          ))}</Card>
        </div>
      </div>
    </>
  )
}
