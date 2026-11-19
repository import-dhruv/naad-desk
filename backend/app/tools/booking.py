"""Deterministic appointment booking with backend-enforced confirmation and
transaction-safe slot commitment (PRD §8.1, §8.4, §8.6)."""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from ..db.models import Appointment, Doctor, Slot
from ..db.seed import mask_phone, phone_hash
from ..db.transactions import lock_for_update
from ..schemas.tools import BookAppointmentArgs, ToolResult
from .availability import format_time_human, resolve_doctor
from .confirmation import consume, mint
from .date_resolver import format_date_human

AFFIRMATIVE = {"haan", "haa", "हाँ", "हां", "હા", "yes", "y", "ji", "जी", "ok", "okay",
               "confirm", "sure", "correct", "sahi", "bilkul", "बिलकुल", "हां जी", "ji haan"}


def is_affirmative(text: str) -> bool:
    t = re.sub(r"[.,!?।]", " ", (text or "").lower()).strip()
    return any(word in AFFIRMATIVE for word in t.split())


def _valid_phone(phone: str | None) -> bool:
    return bool(phone and re.fullmatch(r"[+]?[\d\s-]{10,15}", phone)
                and len(re.sub(r"\D", "", phone)) >= 10)


def _lookup_slot(db: Session, args: BookAppointmentArgs):
    if args.slot_id:
        return db.get(Slot, args.slot_id)
    doctors = [resolve_doctor(db, args.doctor)] if args.doctor else []
    q = db.query(Slot).filter(Slot.status == "available")
    if args.doctor:
        d = doctors[0]
        if d is None:
            return None
        q = q.filter(Slot.doctor_id == d.id)
    # Date/time filtering in Python keeps this portable across SQLite/Postgres.
    for slot in q.order_by(Slot.start_ts).all():
        if args.date and slot.start_ts.date().isoformat() != args.date:
            continue
        if args.time and slot.start_ts.strftime("%H:%M") != args.time:
            continue
        return slot
    return None


def _spoken_details(slot: Slot, doctor: Doctor, patient: str, phone_masked: str, language: str) -> str:
    day = format_date_human(slot.start_ts.date(), language)
    tim = format_time_human(slot.start_ts, language)
    if language == "gu":
        return (f"{doctor.name} સાથે {day} ના {tim} ની એપોઇન્ટમેન્ટ, "
                f"દર્દી {patient}, ફોન {phone_masked}. શું આ બરાબર છે?")
    if language == "hi":
        return (f"{doctor.name} के साथ {day} को {tim} की अपॉइंटमेंट, "
                f"मरीज़ {patient}, फ़ोन {phone_masked}. क्या यह सही है?")
    return (f"Appointment with {doctor.name} on {day} at {tim}, patient {patient}, "
            f"phone {phone_masked}. Is that correct?")


def book_appointment(db: Session, call_id: str, args: BookAppointmentArgs,
                     language: str = "hi", caller_confirmed: bool = False) -> ToolResult:
    """Two-phase booking. Phase 1 reads back and mints a token; phase 2 commits."""
    slot = _lookup_slot(db, args)
    if slot is None or slot.status != "available":
        return ToolResult(ok=False, tool="book_appointment", error="Requested slot is not available.")

    doctor = db.get(Doctor, slot.doctor_id)
    patient = (args.patient_name or "").strip()
    if not patient:
        return ToolResult(ok=False, tool="book_appointment",
                          error="Patient name is required before booking.")
    if not _valid_phone(args.phone):
        return ToolResult(ok=False, tool="book_appointment",
                          error="A valid 10-digit phone number is required.")

    payload = {
        "slot_id": slot.id,
        "doctor": doctor.name,
        "date": slot.start_ts.date().isoformat(),
        "time": slot.start_ts.strftime("%H:%M"),
        "patient_name": patient,
        "phone_masked": mask_phone(args.phone),
        "phone_hash": phone_hash(args.phone),
    }

    # Phase 1 — read back and ask for explicit confirmation.
    if not args.confirmed or not caller_confirmed:
        token = mint(db, call_id, "book_appointment", payload)
        return ToolResult(
            ok=True, tool="book_appointment",
            data={"phase": "pending_confirmation", "confirm_token": token, **payload},
            spoken=_spoken_details(slot, doctor, patient, payload["phone_masked"], language),
        )

    # Phase 2 — authenticated commit in a serialized transaction.
    approved = consume(db, call_id, args.confirm_token, "book_appointment")
    if approved is None or approved.get("slot_id") != slot.id:
        return ToolResult(ok=False, tool="book_appointment",
                          error="Confirmation missing or expired. Please confirm again.")
    try:
        lock_for_update(db, Slot, slot.id)
        fresh = db.get(Slot, slot.id)
        if fresh is None or fresh.status != "available":
            db.rollback()
            return ToolResult(ok=False, tool="book_appointment", error="Slot was just taken.")
        fresh.status = "booked"
        appt = Appointment(
            slot_id=fresh.id, patient_name=patient,
            phone_masked=payload["phone_masked"], phone_hash=payload["phone_hash"],
            status="confirmed", created_call_id=call_id,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)
    except Exception as exc:  # unique constraint / DB lock
        db.rollback()
        return ToolResult(ok=False, tool="book_appointment", error=f"Booking failed: {exc}")

    day = format_date_human(fresh.start_ts.date(), language)
    tim = format_time_human(fresh.start_ts, language)
    if language == "gu":
        spoken = f"તમારી એપોઇન્ટમેન્ટ {doctor.name} સાથે {day} ના {tim} ને કન્ફર્મ થઈ ગઈ છે."
    elif language == "hi":
        spoken = f"आपकी अपॉइंटमेंट {doctor.name} के साथ {day} को {tim} की पक्की हो गई है."
    else:
        spoken = f"Your appointment with {doctor.name} is confirmed for {day} at {tim}."
    return ToolResult(ok=True, tool="book_appointment",
                      data={"phase": "committed", "appointment_id": appt.id, **payload},
                      spoken=spoken)
