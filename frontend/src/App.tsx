import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Overview } from './pages/Overview'
import { LiveCall } from './pages/LiveCall'
import { CallHistory } from './pages/CallHistory'
import { CallDetail } from './pages/CallDetail'
import { EvaluationLab } from './pages/EvaluationLab'
import { Findings } from './pages/Findings'
import { KnowledgeBase } from './pages/KnowledgeBase'
import { Settings } from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Overview />} />
        <Route path="/live" element={<LiveCall />} />
        <Route path="/calls" element={<CallHistory />} />
        <Route path="/calls/:id" element={<CallDetail />} />
        <Route path="/eval" element={<EvaluationLab />} />
        <Route path="/findings" element={<Findings />} />
        <Route path="/kb" element={<KnowledgeBase />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
