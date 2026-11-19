# Three-minute demonstration script

**0:00–0:15 — Overview.** Show the dashboard. Point at KPIs bound to real stored
data and the "no synthetic metrics" empty states.

**0:15–1:15 — Gujarati appointment.** Live Calls → start call with Gujarati.
Ask about Dr. Mehta, interrupt the agent mid-sentence (barge-in flushes playback),
then request a booking. Show the read-back and the explicit confirmation step.
The fee spoken is the exact DB value (500), not an LLM guess.

**1:15–1:40 — Hindi retrieval.** Ask a question answered from deep knowledge-base
content (documents to bring / cancellation policy). Show the retrieval chunks
panel and the confidence value.

**1:40–2:15 — Analytics.** Open Call History → the call → transcript, dual-channel
audio players, tool execution history, latency waterfall, QA breakdown and the
three-bullet summary. Note that STT timestamps are labelled estimated.

**2:15–2:45 — Evaluation Lab.** Show the recorded WER by language, 8 kHz / SNR
degradation, latency p50/p95 with bootstrap CIs, and the findings list.

**2:45–3:00 — Retrospective.** What is proven, what remains unverified: Hinglish
WER is high, TTS-streaming and language-switch matrices are not run, consenting
speaker audio is absent. No fabricated measurements.

## Fallback recorded path
If live API or microphone fails, replay the scenario runner output
(`recon/results/scenarios.md`) and the stored evaluation report
(`eval/reports/EVALUATION_REPORT.md`) while driving the dashboard's stored call
detail views. All of those are real recorded results from this repository.
