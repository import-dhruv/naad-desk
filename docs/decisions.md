# Engineering Decision Log (ADR-style)

| ID | Decision | Rationale | Consequence |
|---|---|---|---|
| D-01 | Use Oogam v2 model ids + `?v=2` WS opt-in | Live `/models` serves `-v2`; PRD's `-v1` observations are a starting baseline. Verified 2026-11-19. | Defensive parser handles both envelope shapes; no hard dependency on `event_id`. |
| D-02 | `external_brain` mode for all calls | PRD requires deterministic control of booking/figures; engine tool-calling is preview. | Backend owns LLM, retrieval, tools; speech engine owns VAD/STT/TTS. |
| D-03 | Server-minted session token for browser; key never in client | Oogam docs explicitly advise this; PRD mandates backend-only key. | `POST /api/calls/{id}/token` mints short-lived token. |
| D-04 | SQLite + SQLAlchemy with `BEGIN IMMEDIATE` + UNIQUE(slot_id) | MVP scale, transaction safety for concurrent booking (§8.6). | Only one of N concurrent bookings succeeds. |
| D-05 | Confirmation enforced as a backend state machine | §8.1: "enforced in backend code, not merely through prompting." | `PendingBooking` requires explicit `confirm` token before commit. |
| D-06 | Dense embeddings: multilingual-e5-small when available, deterministic labelled TF-IDF fallback | Heavy torch dep not installed; must stay runnable. Interface is identical. | Hybrid retrieval always works; fallback clearly labelled in API output. |
| D-07 | BM25 + dense fused with Reciprocal Rank Fusion, top-4, threshold gate | §7.2/7.4. | `confidence` below threshold → "no information" + handoff, never guess. |
| D-08 | Asia/Kolkata for all date resolution; ambiguous → clarify | §8.5. | No silent assumptions; tests cover 4 languages. |
| D-09 | All exact figures returned by tools, never by LLM; deterministic templates | §8.4 100% figure accuracy. | Sutra produces intent/entities only; numbers injected from DB post-generation. |
| D-10 | Batch STT timings always labelled estimated; no diarization claim | Verified `timestampsEstimated:true`. | Analytics UI shows "estimated" badge. |
| D-11 | Voice pin `f1`/`m2`; language pin short codes each turn | Verified realtime catalog + docs "do not leave on auto for turn 1." | Language switch re-sends `set_lang`. |
| D-12 | Cost is an estimate from published rates; authoritative value only when `X-Naad-Cost-Paise` present | No wallet-read endpoint; avoid fabricated spend. | Dashboard labels estimates; spend guard uses ceiling. |
| D-13 | Findings must be evidence-backed; no invented bugs | PRD §12/24. | 15 genuine findings sourced from recon; gaps documented, not padded. |
| D-14 | SaaS-style dark dashboard, real data only, explicit empty states | §15/16. | No fake graphs; Recharts bound to DB/eval records. |
