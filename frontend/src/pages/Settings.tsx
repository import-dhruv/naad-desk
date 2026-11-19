import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { PageHeader } from '../components/Layout'
import { Card } from '../components/ui'

export function Settings() {
  const [config, setConfig] = useState<any>(null)
  const [health, setHealth] = useState<any>(null)
  useEffect(() => { api.config().then(setConfig).catch(() => {}); api.health().then(setHealth).catch(() => {}) }, [])

  const rows = [
    ['Upstream key', config?.upstream_configured ? 'Configured (server-side only)' : 'Not configured'],
    ['REST base', health?.upstream?.rest_base || '—'],
    ['Realtime endpoint', health?.upstream?.ws_url || '—'],
    ['Default voice', config?.voice || '—'],
    ['Default language', config?.language || '—'],
    ['VAD end silence', '700 ms'],
    ['Retrieval backend', config?.retrieval_backend || '—'],
    ['Timezone', 'Asia/Kolkata'],
    ['Database', health?.database || '—'],
    ['Spend ceiling', '5,000 paise per run'],
    ['Recording consent', 'Disclosed at call start · training opt-in DENIED'],
    ['Phone masking', 'Last four digits only'],
  ]

  return (
    <>
      <PageHeader title="Settings" description="Runtime configuration. Secrets are never exposed to the browser." />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Runtime configuration">
          <table className="table"><tbody>{rows.map(([k, v]) => <tr key={k}><td className="text-slate-500">{k}</td><td className="font-mono text-slate-300">{v}</td></tr>)}</tbody></table>
        </Card>
        <Card title="Security & reliability">
          <ul className="space-y-2 text-sm text-slate-400">
            <li>• API key is read from environment variables on the backend only.</li>
            <li>• Browser connects to the backend WebSocket; the key never reaches the client.</li>
            <li>• A spend guard stops new upstream requests at the configured ceiling.</li>
            <li>• Reconnect uses 1s / 2s / 4s back-off with a bounded retry loop.</li>
            <li>• Wallet-empty (4402) and language-capacity errors are surfaced explicitly.</li>
            <li>• All patient data is synthetic; phone numbers are hashed and masked.</li>
          </ul>
        </Card>
      </div>
    </>
  )
}
