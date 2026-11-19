"""Evaluation lab endpoints (§11, §14)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import EvalRun, EvalSample
from ..gateway.websocket import get_retriever
from ..retrieval.evaluation import evaluate as evaluate_retrieval

router = APIRouter()


class EvalRequest(BaseModel):
    kind: str = "retrieval"
    config: dict[str, Any] = {}


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


@router.get("/api/eval/runs")
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(EvalRun).order_by(EvalRun.started_at.desc()).all()
    return [{
        "id": r.id, "kind": r.kind,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "config": json.loads(r.config_json or "{}"),
        "metrics": json.loads(r.metrics_json or "{}"),
        "git_sha": r.git_sha,
        "sample_count": db.query(EvalSample).filter(EvalSample.run_id == r.id).count(),
    } for r in runs]


@router.post("/api/eval/run")
def run_eval(body: EvalRequest, db: Session = Depends(get_db)):
    run_id = f"eval-{uuid.uuid4().hex[:10]}"
    run = EvalRun(id=run_id, kind=body.kind,
                  config_json=json.dumps(body.config), git_sha=_git_sha())
    db.add(run)
    db.commit()

    if body.kind == "retrieval":
        metrics = evaluate_retrieval(get_retriever())
        data = {"recall@4": metrics.recall_at_4,
                "groundedness": metrics.groundedness,
                "unanswerable_rejection": metrics.unanswerable_rejection,
                "hinglish_recall_delta": metrics.hinglish_recall_delta}
        for detail in metrics.details:
            db.add(EvalSample(run_id=run_id, sample_id=detail["id"], condition="hybrid",
                              reference="answerable" if detail["hit"] is not None else "unanswerable",
                              hypothesis=json.dumps(detail["chunk_ids"]), metric="grounded",
                              value=float(detail["confidence"])))
    else:
        # Offline metrics are added by the eval lab scripts; never fabricate here.
        data = {"status": "queued", "note": "Run the experiment script to populate samples."}

    run.metrics_json = json.dumps(data)
    run.finished_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": run_id, "kind": body.kind, "metrics": data}
