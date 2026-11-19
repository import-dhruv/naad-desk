"""Identity-verified, confirmation-enforced appointment cancellation (§8.3)."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.models import Appointment, Doctor, Slot
from ..db.seed import phone_hash
from ..schemas.tools import CancelArgs, ToolResult
from .availability import format_time_human
from .confirmation import consume, mint
from .date_resolver import format_date_human


def find_appointment(db: Session, phone: str | None, ref: str | None = None):
    if not phone:
        return None
    h = phone_hash(phone)
    q = db.query(Appointment).filter(
        Appointment.phone_hash == h, Appointment.status == "confirmed")
    if ref and ref.isdigit():
        q = q.filter(Appointment.id == int(ref))
    return q.order_by(Appointment.created_at.desc()).first()


def _describe(db: Session, appt: Appointment, language: str) -> str:
    slot = db.get(Slot, appt.slot_id)
    doctor = db.get(Doctor, slot.doctor_id)
    day = format_date_human(slot.start_ts.date(), language)
    tim = format_time_human(slot.start_ts, language)
    if language == "gu":
        return f"{doctor.name} સાથે {day} ના {tim} ની એપોઇન્ટમેન્ટ"
    if language == "hi":
        return f"{doctor.name} के साथ {day} को {tim} की अपॉइंटमेंट"
    return f"appointment with {doctor.name} on {day} at {tim}"


def cancel_appointment(db: Session, call_id: str, args: CancelArgs,
                       language: str = "hi", caller_confirmed: bool = False) -> ToolResult:
    appt = find_appointment(db, args.phone, args.appointment_ref)
    if appt is None:
        return ToolResult(ok=False, tool="cancel_appointment",
                          error="No matching appointment found for that phone number.")
    desc = _describe(db, appt, language)
    payload = {"appointment_id": appt.id, "slot_id": appt.slot_id}

    if not args.confirmed or not caller_confirmed:
        token = mint(call_id, "cancel_appointment", payload)
        if language == "gu":
            spoken = f"તમે {desc} રદ કરવા માંગો છો? કૃપા કરીને પુષ્ટિ કરો."
        elif language == "hi":
            spoken = f"आप {desc} रद्द करना चाहते हैं? कृपया पुष्टि करें."
        else:
            spoken = f"You want to cancel the {desc}? Please confirm."
        return ToolResult(ok=True, tool="cancel_appointment",
                          data={"phase": "pending_confirmation", "confirm_token": token, **payload},
                          spoken=spoken)

    approved = consume(call_id, args.confirm_token, "cancel_appointment")
    if approved is None or approved.get("appointment_id") != appt.id:
        return ToolResult(ok=False, tool="cancel_appointment",
                          error="Confirmation missing or expired.")
    try:
        db.execute(text("BEGIN IMMEDIATE"))
        fresh = db.get(Appointment, appt.id)
        if fresh is None or fresh.status != "confirmed":
            db.rollback()
            return ToolResult(ok=False, tool="cancel_appointment", error="Already cancelled.")
        fresh.status = "cancelled"
        slot = db.get(Slot, fresh.slot_id)
        if slot:
            slot.status = "available"
        db.commit()
    except Exception as exc:
        db.rollback()
        return ToolResult(ok=False, tool="cancel_appointment", error=f"Cancellation failed: {exc}")
    if language == "gu":
        spoken = f"તમારી એપોઇન્ટમેન્ટ {appt.id} રદ કરી દેવામાં આવી છે."
    elif language == "hi":
        spoken = f"आपकी अपॉइंटमेंट नंबर {appt.id} रद्द कर दी गई है."
    else:
        spoken = f"Your appointment number {appt.id} has been cancelled."
    return ToolResult(ok=True, tool="cancel_appointment",
                      data={"phase": "committed", **payload}, spoken=spoken)
