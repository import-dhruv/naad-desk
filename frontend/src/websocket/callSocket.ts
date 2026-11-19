import type { ServerMessage } from '../types'

const STORAGE_KEY = 'naad-desk-active-call'
const BACKOFF_MS = [1000, 2000, 4000]

/** Thin browser WebSocket client for /ws/call with bounded reconnect/resume. */
export class CallSocket {
  private ws: WebSocket | null = null
  private intentionalClose = false
  private retries = 0
  onMessage: (msg: ServerMessage) => void = () => {}
  onClose: (reason: string) => void = () => {}

  async connect(language: string, voice?: string, resume = false): Promise<void> {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws/call`
    this.intentionalClose = false
    this.ws = new WebSocket(url)

    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as ServerMessage
        if (msg.type === 'session.ready' && msg.call_id) {
          sessionStorage.setItem(STORAGE_KEY, msg.call_id)
        }
        this.onMessage(msg)
      } catch { /* ignore malformed frames */ }
    }

    this.ws.onclose = (e) => {
      if (this.intentionalClose || this.retries >= BACKOFF_MS.length) {
        if (this.intentionalClose) sessionStorage.removeItem(STORAGE_KEY)
        this.onClose(e.reason || 'closed')
        return
      }
      const delay = BACKOFF_MS[this.retries++]
      const resumeId = sessionStorage.getItem(STORAGE_KEY)
      window.setTimeout(() => {
        this.connect(language, voice, Boolean(resumeId)).catch(() => this.onClose('reconnect failed'))
      }, delay)
    }

    await new Promise<void>((resolve, reject) => {
      if (!this.ws) return reject(new Error('socket init failed'))
      this.ws.onopen = () => {
        const resume_call_id = resume ? sessionStorage.getItem(STORAGE_KEY) : null
        this.send({ v: 1, type: 'start', language, voice: voice ?? null,
                    disclosure_ack: true, resume_call_id })
        resolve()
      }
      this.ws.onerror = () => reject(new Error('websocket error'))
    })
  }

  send(msg: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(msg))
  }

  close(reason = 'caller_hangup'): void {
    this.intentionalClose = true
    this.retries = 0
    this.send({ v: 1, type: 'end', reason })
    this.ws?.close()
    this.ws = null
  }
}
