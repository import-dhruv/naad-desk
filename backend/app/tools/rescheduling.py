"""Atomic, identity-verified, confirmation-enforced rescheduling (§8.2)."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.models import Appointment, Doctor, Slot
from ..schemas.tools import RescheduleArgs, ToolResult
from .availability import format_time_human
from .cancellation import find_appointment
from .confirmation import consume, mint
from .date_resolver import format_date_human


def _pending_slot(db: Session, args: RescheduleArgs):
    if args.new_slot_id:
        return db.get(Slot, args.new_slot_id)
    q = db.query(Slot).filter(Slot.status == "available")
    if args.new_date:
        q = q.filter(text("date(start_ts) = :d").bindparams(d=args.new_date))
    if args.new_time:
        q = q.filter(text("strftime('%H:%M', start_ts) = :t").bindparams(t=args.new_time))
    return q.order_by(Slot.start_ts).first()


def _spoken_new(slot: Slot, doctor: Doctor, language: str) -> str:
    day = format_date_human(slot.start_ts.date(), language)
    tim = format_time_human(slot.start_ts, language)
    if language == "gu":
        return f"નવો સમય {doctor.name} સાથે {day} ના {tim} છે. શું પુષ્ટિ કરું?"
    if language == "hi":
        return f"नया समय {doctor.name} के साथ {day} को {tim} है. क्या पुष्टि करूँ?"
    return f"The new time is {doctor.name} on {day} at {tim}. Should I confirm?"


def reschedule_appointment(db: Session, call_id: str, args: RescheduleArgs,
                           language: str = "hi", caller_confirmed: bool = False) -> ToolResult:
    appt = find_appointment(db, args.phone, args.appointment_ref)
    if appt is None:
        return ToolResult(ok=False, tool="reschedule_appointment",
                          error="No matching appointment found for that phone number.")
    new_slot = _pending_slot(db, args)
    if new_slot is None or new_slot.status != "available":
        return ToolResult(ok=False, tool="reschedule_appointment",
                          error="Requested new slot is not available.")
    doctor = db.get(Doctor, new_slot.doctor_id)
    payload = {"appointment_id": appt.id, "old_slot_id": appt.slot_id,
               "new_slot_id": new_slot.id}

    if not args.confirmed or not caller_confirmed:
        token = mint(call_id, "reschedule_appointment", payload)
        return ToolResult(ok=True, tool="reschedule_appointment",
                          data={"phase": "pending_confirmation", "confirm_token": token, **payload},
                          spoken=_spoken_new(new_slot, doctor, language))

    approved = consume(call_id, args.confirm_token, "reschedule_appointment")
    if approved is None or approved.get("appointment_id") != appt.id:
        return ToolResult(ok=False, tool="reschedule_appointment",
                          error="Confirmation missing or expired.")
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        fresh_appt = db.get(Appointment, appt.id)
        fresh_new = db.get(Slot, new_slot.id)
        if (fresh_appt is None or fresh_appt.status != "confirmed"
                or fresh_new is None or fresh_new.status != "available"):
            db.rollback()
            return ToolResult(ok=False, tool="reschedule_appointment",
                              error="Appointment or slot changed. Please retry.")
        old = db.get(Slot, fresh_appt.slot_id)
        if old:
            old.status = "available"   # release old slot
        fresh_new.status = "booked"    # commit new slot
        fresh_appt.slot_id = fresh_new.id
        db.commit()
    except Exception as exc:
        db.rollback()
        return ToolResult(ok=False, tool="reschedule_appointment",
                          error=f"Reschedule failed: {exc}")

    day = format_date_human(fresh_new.start_ts.date(), language)
    tim = format_time_human(fresh_new.start_ts, language)
    if language == "gu":
        spoken = f"તમારી એપોઇન્ટમેન્ટ {day} ના {tim} ને બદલીને કન્ફર્મ કરી છે."
    elif language == "hi":
        spoken = f"आपकी अपॉइंटमेंट {day} को {tim} के लिए बदल कर पक्की कर दी गई है."
    else:
        spoken = f"Your appointment has been rescheduled to {day} at {tim}."
    return ToolResult(ok=True, tool="reschedule_appointment",
                      data={"phase": "committed", **payload}, spoken=spoken)
