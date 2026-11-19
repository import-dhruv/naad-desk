"""Doctor resolution and slot availability — deterministic, DB-backed (§8)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import Doctor, Slot
from ..schemas.tools import ToolResult
from .date_resolver import format_date_human, normalize

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(settings.timezone)
except Exception:  # pragma: no cover
    from datetime import timezone
    TZ = timezone.utc

POD_RANGES = {
    "morning": (time(0, 0), time(12, 0)),
    "afternoon": (time(12, 0), time(16, 0)),
    "evening": (time(16, 0), time(23, 59)),
}


DOCTOR_ALIASES = {
    "मेहता": "mehta", "મેહતા": "mehta", "पटेल": "patel", "પટેલ": "patel",
    "शाह": "shah", "શાહ": "shah", "राव": "rao", "રાવ": "rao",
}


def normalize_doctor_name(name: str) -> str:
    t = normalize(name)
    for prefix in ("dr", "doctor", "डॉक्टर", "ડૉક્ટર", "डॉ", "ડૉ"):
        t = t.replace(prefix, " ")
    tokens = [" ".join(DOCTOR_ALIASES.get(tok, tok) for tok in word.split())
              for word in t.split()]
    return " ".join(tokens)


def resolve_doctor(db: Session, name: str | None):
    """Resolve a doctor from free-form speech. Returns None when ambiguous/unknown."""
    if not name or not name.strip():
        return None
    q = normalize_doctor_name(name)
    doctors = db.scalars(select(Doctor).where(Doctor.active.is_(True))).all()
    if not doctors:
        return None
    exact = [d for d in doctors if normalize_doctor_name(d.name) == q]
    if len(exact) == 1:
        return exact[0]
    partial = [d for d in doctors if q and (q in normalize_doctor_name(d.name)
                                            or normalize_doctor_name(d.name) in q)]
    return partial[0] if len(partial) == 1 else None


def doctor_label(doctor, language: str = "hi") -> str:
    # Deterministic spoken name — never authored by the LLM.
    return doctor.name


def format_time_human(dt: datetime, language: str = "hi") -> str:
    hour, minute = dt.hour, dt.minute
    if language in ("en-in", "en"):
        ap = "AM" if hour < 12 else "PM"
        h = hour % 12 or 12
        return f"{h}:{minute:02d} {ap}"
    if language == "gu":
        return f"{hour:02d}:{minute:02d}"
    return f"{hour:02d}:{minute:02d}"


def available_slots(db: Session, doctor_id: int | None, day: date | None,
                    part_of_day: str = "any", limit: int = 5):
    stmt = select(Slot).where(Slot.status == "available")
    if doctor_id is not None:
        stmt = stmt.where(Slot.doctor_id == doctor_id)
    if day is not None:
        start = datetime.combine(day, time(0, 0), tzinfo=TZ)
        end = start + timedelta(days=1)
        stmt = stmt.where(Slot.start_ts >= start, Slot.start_ts < end)
    stmt = stmt.order_by(Slot.start_ts).limit(limit * 4)
    slots = list(db.scalars(stmt).all())
    if part_of_day in POD_RANGES:
        lo, hi = POD_RANGES[part_of_day]
        slots = [s for s in slots if lo <= s.start_ts.timetz().replace(tzinfo=None) <= hi]
    return slots[:limit]


def search_availability(db: Session, doctor: str | None = None, date_iso: str | None = None,
                        part_of_day: str = "any", language: str = "hi", limit: int = 3) -> ToolResult:
    d = None
    if doctor:
        d = resolve_doctor(db, doctor)
        if d is None:
            return ToolResult(ok=False, tool="search_availability",
                              error=f"Doctor not found: {doctor}")
    day = None
    if date_iso:
        try:
            day = date.fromisoformat(date_iso)
        except ValueError:
            return ToolResult(ok=False, tool="search_availability", error="Invalid date")

    slots = available_slots(db, d.id if d else None, day, part_of_day, limit)
    if not slots:
        spoken = ("આ સમયે કોઈ ઉપલબ્ધ સ્લોટ નથી. હું તમને માનવ એજન્ટ સાથે જોડી શકું છું." if language == "gu"
                  else "इस समय कोई उपलब्ध स्लॉट नहीं है. मैं आपको मानव एजेंट से जोड़ सकता हूँ." if language == "hi"
                  else "No slots are available then. I can connect you with a human agent.")
        return ToolResult(ok=True, tool="search_availability",
                          data={"slots": []}, spoken=spoken)

    options = []
    for s in slots:
        doc = db.get(Doctor, s.doctor_id)
        options.append({
            "slot_id": s.id,
            "doctor": doc.name,
            "date": s.start_ts.date().isoformat(),
            "date_spoken": format_date_human(s.start_ts.date(), language),
            "time": s.start_ts.strftime("%H:%M"),
            "time_spoken": format_time_human(s.start_ts, language),
        })

    if language == "gu":
        joined = ", ".join(f"{o['doctor']} ને {o['date_spoken']} ના {o['time_spoken']}" for o in options)
        spoken = f"ઉપલબ્ધ સમય: {joined}. તમને કયો સમય યોગ્ય છે?"
    elif language == "hi":
        joined = ", ".join(f"{o['doctor']} के {o['date_spoken']} को {o['time_spoken']}" for o in options)
        spoken = f"उपलब्ध समय: {joined}. आपको कौन-सा समय उपयुक्त है?"
    else:
        joined = ", ".join(f"{o['doctor']} on {o['date_spoken']} at {o['time_spoken']}" for o in options)
        spoken = f"Available times: {joined}. Which one works for you?"
    return ToolResult(ok=True, tool="search_availability", data={"slots": options}, spoken=spoken)
