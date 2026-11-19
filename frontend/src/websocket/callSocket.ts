import type { ServerMessage } from '../types'

/** Thin browser WebSocket client for /ws/call. */
export class CallSocket {
  private ws: WebSocket | null = null
  onMessage: (msg: ServerMessage) => void = () => {}
  onClose: (reason: string) => void = () => {}

  async connect(language: string, voice?: string): Promise<void> {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws/call`
    this.ws = new WebSocket(url)
    this.ws.onmessage = (e) => {
      try { this.onMessage(JSON.parse(e.data) as ServerMessage) } catch { /* ignore */ }
    }
    this.ws.onclose = (e) => this.onClose(e.reason || 'closed')
    await new Promise<void>((resolve, reject) => {
      if (!this.ws) return reject(new Error('socket init failed'))
      this.ws.onopen = () => {
        this.send({ v: 1, type: 'start', language, voice: voice ?? null, disclosure_ack: true })
        resolve()
      }
      this.ws.onerror = () => reject(new Error('websocket error'))
    })
  }

  send(msg: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(msg))
  }

  close(reason = 'caller_hangup'): void {
    this.send({ v: 1, type: 'end', reason })
    this.ws?.close()
    this.ws = null
  }
}
