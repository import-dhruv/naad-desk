"""End-to-end turn latency analysis from real recorded turns (§11.5)."""
from __future__ import annotations

import json
import statistics
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import EvalRun, EvalSample, Turn  # noqa: E402

from eval.metrics.bootstrap import bootstrap_metric  # noqa: E402


def main() -> None:
    db = SessionLocal()
    turns = db.query(Turn).filter(Turn.t_turn_complete.isnot(None)).all()
    values = sorted(float(t.t_turn_complete) for t in turns)
    if not values:
        print("No recorded turns available. Run live calls first.")
        return
    p50 = statistics.median(values)
    p95 = values[min(len(values) - 1, int(0.95 * len(values)))]
    metrics = {
        "turn_count": len(values),
        "p50_ms": round(p50, 2), "p95_ms": round(p95, 2),
        "mean_ms": round(statistics.mean(values), 2),
        "min_ms": round(values[0], 2), "max_ms": round(values[-1], 2),
        "worst_5_percent": [round(v, 2) for v in values[-max(1, len(values) // 20):]],
        "p50_ci": bootstrap_metric(values, statistic=statistics.median, resamples=10000),
        "vad_floor_ms": 700,
        "note": "Timing comes from server-side turn instrumentation; VAD 700 ms floor included.",
    }
    run_id = f"eval-latency-{uuid.uuid4().hex[:8]}"
    db.add(EvalRun(id=run_id, kind="latency", config_json=json.dumps({
        "source": "turns.t_turn_complete", "vad_floor_ms": 700}),
        metrics_json=json.dumps(metrics),
        git_sha="unknown", finished_at=datetime.now(timezone.utc)))
    for i, value in enumerate(values):
        db.add(EvalSample(run_id=run_id, sample_id=f"turn-{i:04d}", condition="live",
                          metric="turn_latency_ms", value=value))
    db.commit()
    db.close()
    out = ROOT / "eval/reports/latency_results.json"
    out.write_text(json.dumps({"run_id": run_id, "metrics": metrics}, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
