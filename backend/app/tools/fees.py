"""Consultation-fee lookup — fees come only from the database (§8.4)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..schemas.tools import FeesArgs, ToolResult
from .availability import resolve_doctor


def get_fees(db: Session, args: FeesArgs, language: str = "hi") -> ToolResult:
    if args.doctor:
        doctor = resolve_doctor(db, args.doctor)
        if doctor is None:
            return ToolResult(ok=False, tool="get_fees", error="Doctor not found.")
        rupees = doctor.fee_paise // 100
        if language == "gu":
            spoken = f"{doctor.name} ની કન્સલ્ટેશન ફી {rupees} રૂપિયા છે."
        elif language == "hi":
            spoken = f"{doctor.name} की परामर्श शुल्क {rupees} रुपये है."
        else:
            spoken = f"The consultation fee for {doctor.name} is {rupees} rupees."
        return ToolResult(ok=True, tool="get_fees",
                          data={"doctor": doctor.name, "fee_paise": doctor.fee_paise},
                          spoken=spoken)

    from ..db.models import Doctor
    doctors = db.query(Doctor).filter(Doctor.active.is_(True)).all()
    lines = [f"{d.name}: {d.fee_paise // 100}" for d in doctors]
    if language == "gu":
        spoken = "કન્સલ્ટેશન ફી: " + ", ".join(lines) + " રૂપિયા."
    elif language == "hi":
        spoken = "परामर्श शुल्क: " + ", ".join(lines) + " रुपये."
    else:
        spoken = "Consultation fees: " + ", ".join(lines) + " rupees."
    return ToolResult(ok=True, tool="get_fees",
                      data={"fees": [{"doctor": d.name, "fee_paise": d.fee_paise} for d in doctors]},
                      spoken=spoken)
