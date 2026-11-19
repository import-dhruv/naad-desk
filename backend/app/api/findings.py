"""Findings management and export (§12)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import Finding

router = APIRouter()


class FindingIn(BaseModel):
    title: str
    severity: str = "medium"
    area: str = "general"
    expected: str = ""
    actual: str = ""
    reproduction_steps: str = ""
    evidence_path: str = ""
    suggestion: str = ""
    status: str = "open"
    kind: str = "observation"


def _serialize(f: Finding) -> dict:
    return {
        "id": f.id, "title": f.title, "severity": f.severity, "area": f.area,
        "expected": f.expected, "actual": f.actual,
        "reproduction_steps": f.reproduction_steps, "evidence_path": f.evidence_path,
        "suggestion": f.suggestion, "status": f.status, "kind": f.kind,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get("/api/findings")
def list_findings(severity: str | None = None, area: str | None = None,
                  db: Session = Depends(get_db)):
    q = db.query(Finding)
    if severity:
        q = q.filter(Finding.severity == severity)
    if area:
        q = q.filter(Finding.area == area)
    return [_serialize(f) for f in q.order_by(Finding.created_at.desc()).all()]


@router.post("/api/findings", status_code=201)
def create_finding(body: FindingIn, db: Session = Depends(get_db)):
    fid = f"F-{uuid.uuid4().hex[:6]}"
    f = Finding(id=fid, **body.model_dump())
    db.add(f)
    db.commit()
    return _serialize(f)


@router.patch("/api/findings/{fid}")
def update_finding(fid: str, patch: dict, db: Session = Depends(get_db)):
    f = db.get(Finding, fid)
    if f is None:
        raise HTTPException(404, "finding not found")
    for key, value in patch.items():
        if hasattr(f, key):
            setattr(f, key, value)
    db.commit()
    return _serialize(f)


@router.get("/api/findings/export.md", response_class=PlainTextResponse)
def export_findings(db: Session = Depends(get_db)):
    findings = db.query(Finding).order_by(Finding.severity, Finding.id).all()
    lines = ["# Naad Desk — Findings Report", ""]
    for f in findings:
        lines += [f"## {f.id} — {f.title}", "",
                  f"- **Severity:** {f.severity}  ",
                  f"- **Area:** {f.area}  ",
                  f"- **Kind:** {f.kind}  ",
                  f"- **Status:** {f.status}", "",
                  f"**Expected:** {f.expected}", "",
                  f"**Actual:** {f.actual}", "",
                  f"**Reproduction:** {f.reproduction_steps}", "",
                  f"**Evidence:** `{f.evidence_path}`", "",
                  f"**Suggested fix:** {f.suggestion}", ""]
    return "\n".join(lines)
