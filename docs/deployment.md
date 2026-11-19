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

### Known limitation: ephemeral storage
Vercel Functions have a read-only filesystem except `/tmp`. The backend therefore
defaults to `sqlite:////tmp/naad_desk.db` on Vercel. Consequences:

- Call history, analytics and evaluation runs reset on a cold start.
- Recordings written under `/tmp` are not durable.
- `GET /api/health` reports `storage: "ephemeral (/tmp SQLite) — data is reset on cold start"`
  so this is visible at runtime rather than hidden.

This is intentional for the showcase MVP (no paid infrastructure). To make it
production-durable, set `DATABASE_URL` to a managed PostgreSQL instance and switch
the models to portable SQLAlchemy types; see the tracked enhancement issue on
GitHub. The local/Docker deployment uses a persistent SQLite file and retains all
data.

### WebSocket duration
Vercel Functions cap connection lifetime (300 s on Hobby by default). The browser
client implements reconnect with 1 s / 2 s / 4 s back-off; long calls should resume
against the in-memory state, but a reconnect to a different instance cannot restore
process-local state. This is a platform constraint, documented rather than hidden.

## Docker / local
`docker compose up --build` mounts a named volume at `/app/data` and sets
`DATABASE_URL=sqlite:////app/data/naad_desk.db`, giving persistent storage and no
connection-duration limit. This is the recommended way to see accumulated call
history and analytics.
