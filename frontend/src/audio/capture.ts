/**
 * Microphone capture with AudioWorklet, TRUE resampling to 16 kHz mono and
 * PCM16 encoding in ~20 ms frames. Silence is streamed continuously.
 */
export class AudioCapture {
  private ctx: AudioContext | null = null
  private stream: MediaStream | null = null
  private node: AudioWorkletNode | null = null
  private source: MediaStreamAudioSourceNode | null = null
  private leftover: Float32Array = new Float32Array(0)
  private targetRate = 16000
  private frameSamples = 320 // 20 ms at 16 kHz
  recorded: Int16Array[] = []

  constructor(private onFrame: (pcm: Int16Array) => void) {}

  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: false, channelCount: 1 },
    })
    this.ctx = new AudioContext({ latencyHint: 'interactive' })
    await this.ctx.audioWorklet.addModule('/pcm-worklet.js')
    this.source = this.ctx.createMediaStreamSource(this.stream)
    this.node = new AudioWorkletNode(this.ctx, 'pcm-processor', { numberOfInputs: 1, numberOfOutputs: 0 })
    this.node.port.onmessage = (e) => this.onWorkletBlock(e.data as Float32Array)
    this.source.connect(this.node)
  }

  /** Linear-interpolation resampling — not a metadata-only sample-rate change. */
  private resample(input: Float32Array, from: number, to: number): Float32Array {
    if (from === to) return input
    const ratio = from / to
    const outLength = Math.max(1, Math.floor(input.length / ratio))
    const out = new Float32Array(outLength)
    for (let i = 0; i < outLength; i++) {
      const pos = i * ratio
      const i0 = Math.floor(pos)
      const i1 = Math.min(i0 + 1, input.length - 1)
      const frac = pos - i0
      out[i] = input[i0] * (1 - frac) + input[i1] * frac
    }
    return out
  }

  private onWorkletBlock(block: Float32Array): void {
    if (!this.ctx) return
    const resampled = this.resample(block, this.ctx.sampleRate, this.targetRate)
    const merged = new Float32Array(this.leftover.length + resampled.length)
    merged.set(this.leftover, 0)
    merged.set(resampled, this.leftover.length)
    let offset = 0
    while (offset + this.frameSamples <= merged.length) {
      const frame = merged.subarray(offset, offset + this.frameSamples)
      const pcm = new Int16Array(this.frameSamples)
      for (let i = 0; i < frame.length; i++) {
        const s = Math.max(-1, Math.min(1, frame[i]))
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff
      }
      this.recorded.push(pcm)
      this.onFrame(pcm)
      offset += this.frameSamples
    }
    this.leftover = merged.slice(offset)
  }

  async stop(): Promise<void> {
    this.node?.disconnect()
    this.source?.disconnect()
    this.stream?.getTracks().forEach((t) => t.stop())
    if (this.ctx && this.ctx.state !== 'closed') await this.ctx.close()
    this.ctx = null
  }
}

export function pcm16ToBase64(pcm: Int16Array): string {
  const bytes = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}
