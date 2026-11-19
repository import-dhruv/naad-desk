"""Idempotent seed: 4 doctors, 3 weeks of slots, 30 existing appointments, holidays.

All data is synthetic. Phone numbers use reserved fictional ranges and are stored
only as a masked display string plus a one-way SHA-256 hash.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from .database import SessionLocal, init_db
from .models import Appointment, Doctor, Holiday, Slot

ZONE = None
try:
    from zoneinfo import ZoneInfo
    ZONE = ZoneInfo(settings.timezone)
except Exception:  # pragma: no cover
    ZONE = timezone.utc

DOCTORS = [
    ("Dr. Mehta", "General Physician", 50000, "hi,gu,en"),
    ("Dr. Patel", "Dermatologist", 70000, "hi,gu,en"),
    ("Dr. Shah", "Pediatrician", 60000, "hi,gu,en"),
    ("Dr. Rao", "Orthopedist", 80000, "hi,en"),
]

HOURS = [(9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
         (14, 0), (14, 30), (15, 0), (15, 30), (16, 0), (16, 30)]
WORKDAYS = {0, 1, 2, 3, 4, 5}  # Mon–Sat


def phone_hash(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())[-10:]
    return hashlib.sha256(("+91" + digits).encode()).hexdigest()


def mask_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())[-10:]
    return f"+91 ******{digits[-4:]}" if len(digits) >= 4 else "+91 ****"


def seed(session: Session | None = None) -> dict[str, int]:
    init_db()
    db = session or SessionLocal()
    own = session is None
    try:
        if db.scalar(select(Doctor).limit(1)):
            # Already seeded — idempotent.
            return {
                "doctors": db.query(Doctor).count(),
                "slots": db.query(Slot).count(),
                "appointments": db.query(Appointment).count(),
            }

        doctors: list[Doctor] = []
        for name, spec, fee, langs in DOCTORS:
            d = Doctor(name=name, speciality=spec, fee_paise=fee, languages=langs)
            db.add(d)
            doctors.append(d)
        db.flush()

        # Holidays in the next three weeks (2nd Saturday + one festival).
        today = datetime.now(ZONE).date()
        holidays = {
            (today + timedelta(days=(5 - today.weekday()) % 7 + 7)).isoformat(): "Second Saturday",
            (today + timedelta(days=10)).isoformat(): "Clinic closure (synthetic)",
        }
        for d, reason in holidays.items():
            db.add(Holiday(date=d, reason=reason))
        db.flush()

        # Three weeks of 30-minute slots on working days, excluding holidays.
        slots: list[Slot] = []
        for day_offset in range(1, 22):
            day = today + timedelta(days=day_offset)
            if day.weekday() not in WORKDAYS or day.isoformat() in holidays:
                continue
            for hour, minute in HOURS:
                for d in doctors:
                    s = Slot(
                        doctor_id=d.id,
                        start_ts=datetime.combine(day, time(hour, minute), tzinfo=ZONE),
                    )
                    db.add(s)
                    slots.append(s)
        db.flush()

        # 30 synthetic existing appointments on distinct near-term slots.
        names = ["A Sharma", "B Patel", "C Mehta", "D Shah", "E Rao", "F Desai",
                 "G Joshi", "H Nair", "I Verma", "K Gupta"]
        phones = ["9876500001", "9876500002", "9876500003", "9876500004", "9876500005",
                 "9876500006", "9876500007", "9876500008", "9876500009", "9876500010"]
        candidates = [s for s in slots if s.start_ts.date() <= today + timedelta(days=12)]
        for i in range(min(30, len(candidates))):
            slot = candidates[i]
            phone = phones[i % len(phones)]
            slot.status = "booked"
            db.add(Appointment(
                slot_id=slot.id,
                patient_name=names[i % len(names)],
                phone_masked=mask_phone(phone),
                phone_hash=phone_hash(phone),
                status="confirmed",
                created_call_id=f"seed-{i:03d}",
            ))
        db.commit()
        return {
            "doctors": db.query(Doctor).count(),
            "slots": db.query(Slot).count(),
            "appointments": db.query(Appointment).count(),
            "holidays": db.query(Holiday).count(),
        }
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    print(seed())
