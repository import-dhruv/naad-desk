# Deployment notes

## Vercel (current production deployment)

The project deploys as a single Vercel project with two **Services** (beta):

```json
{
  "services": {
    "frontend": { "root": "frontend", "framework": "vite" },
    "backend":  { "root": "backend", "entrypoint": "app.main:app" }
  },
  "rewrites": [
    { "source": "/ws/(.*)", "destination": { "service": "backend" } },
    { "source": "/api/(.*)", "destination": { "service": "backend" } },
    { "source": "/(.*)", "destination": { "service": "frontend" } }
  ]
}
```

- Backend needs to be self-contained: `backend/knowledge/` and
  `backend/app/findings_data.py` are bundled with the service because Vercel only
  includes the service root in the function bundle.
- The API key is a hidden Vercel Secret named `OOGAM_API_KEY`. It is never in the
  repository or browser.
- Both services are exposed through one deployment URL; the browser calls
  relative `/api` and `/ws` paths, so previews work without configuration.

### Persistent storage (Neon Postgres)
`DATABASE_URL` is provided by the Neon Marketplace integration and points to a
serverless Postgres database. The backend normalises `postgresql://` to
`postgresql+psycopg://`, uses dialect-aware writes (`SELECT … FOR UPDATE` on
Postgres, `BEGIN IMMEDIATE` on SQLite), and portable datetime/index definitions.
Confirmation tokens and the spend counter are stored in the database, so they
survive instance switches. Call history, analytics, evaluations and findings now
persist across cold starts.

Recordings still write to `/tmp` (binary audio is not stored in Postgres); they are
durable in the local/Docker deployment, which uses a mounted volume.

`GET /api/health` reports the active storage mode.

### WebSocket duration and reconnect
Vercel Functions cap connection lifetime (300 s on Hobby by default). The browser
client reconnects with 1 s / 2 s / 4 s back-off and sends `resume_call_id`; the
backend restores the conversation snapshot stored in `calls.metadata_json`.
Confirmation tokens and spend counters are DB-backed, so a resume on a different
instance keeps the booking flow and spend guard consistent. Cold-start latency on
the first request remains a platform characteristic.

## Docker / local
`docker compose up --build` mounts a named volume at `/app/data` and sets
`DATABASE_URL=sqlite:////app/data/naad_desk.db`, giving persistent storage and no
connection-duration limit. This is the recommended way to see accumulated call
history and analytics.
