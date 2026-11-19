/**
 * Gapless playback scheduler for 24 kHz PCM16 agent audio.
 * Frames are scheduled on the AudioContext clock back-to-back; the queue can be
 * flushed instantly for barge-in. Played audio is kept for analytics.
 */
export class PlaybackScheduler {
  private ctx: AudioContext | null = null
  private nextTime = 0
  private queued = 0
  recorded: Int16Array[] = []

  async ensure(): Promise<AudioContext> {
    if (!this.ctx || this.ctx.state === 'closed') {
      this.ctx = new AudioContext({ sampleRate: 24000, latencyHint: 'interactive' })
      this.nextTime = this.ctx.currentTime + 0.02
    }
    if (this.ctx.state === 'suspended') await this.ctx.resume()
    return this.ctx
  }

  /** Convert a base64-encoded PCM16 24 kHz frame and schedule it. */
  async enqueue(base64: string): Promise<void> {
    const ctx = await this.ensure()
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))
    const pcm = new Int16Array(bytes.buffer, bytes.byteOffset, bytes.length / 2)
    this.recorded.push(pcm)
    const float = new Float32Array(pcm.length)
    for (let i = 0; i < pcm.length; i++) float[i] = pcm[i] / 32768
    const buffer = ctx.createBuffer(1, float.length, 24000)
    buffer.copyToChannel(float, 0)
    const source = ctx.createBufferSource()
    source.buffer = buffer
    source.connect(ctx.destination)
    const start = Math.max(this.nextTime, ctx.currentTime + 0.005)
    source.start(start)
    this.nextTime = start + buffer.duration
    this.queued++
    source.onended = () => { this.queued = Math.max(0, this.queued - 1) }
  }

  /** Immediate barge-in: stop everything scheduled or playing. */
  flush(): void {
    if (this.ctx) {
      this.nextTime = this.ctx.currentTime + 0.01
      this.queued = 0
    }
  }

  async stop(): Promise<void> {
    this.flush()
    if (this.ctx && this.ctx.state !== 'closed') await this.ctx.close()
    this.ctx = null
  }

  get pendingFrames(): number { return this.queued }
}
