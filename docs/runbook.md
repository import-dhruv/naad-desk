# Runbook

## Start / stop
```bash
cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```
Stop with Ctrl-C. Development auto-reload: add `--reload`.

## Health checks
- `GET /api/health` → `status: ok`, `database: ok`, `upstream.configured: true`.
- Dashboard Overview shows the same values live.

## Common failures
| Symptom | Action |
|---|---|
| `upstream_configured: false` | Set `OOGAM_API_KEY` in `.env`, restart. |
| `wallet_empty (4402)` | Top up the Oogam wallet; spend guard will block new requests. |
| `language_at_capacity` | Retry later; the gateway surfaces the error to the UI. |
| `1011 / 1006` close | Gateway retries with 1 s / 2 s / 4 s back-off (bounded). |
| Empty recordings | Check that the browser sent `audio` frames; typed replay makes no caller audio. |
| "No slots available" | Seed data has 30 pre-booked slots; re-run `seed()` only on a fresh DB. |
| Stale KB | `POST /api/kb/ingest` (idempotent, content-hash based). |

## Spend controls
`COST_CEILING_PAISE`, `MONTHLY_BUDGET_PAISE`, `MAX_CALL_SECONDS` in `.env`.
The in-process `SpendGuard` refuses new upstream REST requests once the ceiling
is reached. Cost shown in the UI is an estimate unless `X-Naad-Cost-Paise` was present.

## Fresh clone verification
1. `.venv/bin/python -m pytest -q` → 88 passed.
2. `scripts/smoke_test.py` → seed + ingest + retrieval metrics.
3. Start backend, run `scripts/e2e_socket_test.py` → audio frames + `call.ended`.
4. `scripts/run_scenarios.py` → writes `recon/results/scenarios.{json,md}`.
