/**
 * AudioWorklet processor: captures raw Float32 mono input at the AudioContext
 * sample rate and forwards fixed-size blocks to the main thread. Resampling to
 * 16 kHz and PCM16 encoding happen in the main thread (capture.ts).
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.block = []
    this.blockSize = 512
  }
  process(inputs) {
    const input = inputs[0]
    if (input && input.length > 0) {
      const channel = input[0]
      for (let i = 0; i < channel.length; i++) {
        this.block.push(channel[i])
        if (this.block.length >= this.blockSize) {
          this.port.postMessage(Float32Array.from(this.block))
          this.block = []
        }
      }
    }
    return true
  }
}
registerProcessor('pcm-processor', PCMProcessor)
