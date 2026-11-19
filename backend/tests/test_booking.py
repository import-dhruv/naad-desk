"""Booking, cancellation, reschedule and transaction-safety tests (§8)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from app.db.database import Base
from app.db.models import Appointment, Slot
from app.db.seed import seed
from app.schemas.tools import BookAppointmentArgs, CancelArgs
from app.tools.availability import resolve_doctor
from app.tools.booking import book_appointment, is_affirmative
from app.tools.cancellation import cancel_appointment
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_affirmative_detection():
    for text in ["haan", "ji haan", "yes", "हाँ", "હા", "okay", "bilkul"]:
        assert is_affirmative(text), text
    assert not is_affirmative("no")
    assert not is_affirmative("kal")


def test_booking_requires_confirmation(db):
    slot = db.query(Slot).filter(Slot.status == "available").first()
    args = BookAppointmentArgs(slot_id=slot.id, patient_name="Test Patient",
                               phone="9876512345", confirmed=False)
    result = book_appointment(db, "call-test-1", args, "hi", caller_confirmed=False)
    assert result.ok
    assert result.data["phase"] == "pending_confirmation"
    assert db.query(Appointment).count() == 30  # unchanged

    token = result.data["confirm_token"]
    approved = BookAppointmentArgs(slot_id=slot.id, patient_name="Test Patient",
                                   phone="9876512345", confirmed=True, confirm_token=token)
    result2 = book_appointment(db, "call-test-1", approved, "hi", caller_confirmed=True)
    assert result2.ok and result2.data["phase"] == "committed"
    assert db.query(Appointment).count() == 31
    assert db.get(Slot, slot.id).status == "booked"


def test_wrong_token_does_not_commit(db):
    slot = db.query(Slot).filter(Slot.status == "available").first()
    args = BookAppointmentArgs(slot_id=slot.id, patient_name="X", phone="9876512345")
    book_appointment(db, "call-test-2", args)
    approved = BookAppointmentArgs(slot_id=slot.id, patient_name="X", phone="9876512345",
                                   confirmed=True, confirm_token="wrong")
    result = book_appointment(db, "call-test-2", approved, caller_confirmed=True)
    assert not result.ok


def test_cancel_and_reschedule(db):
    appt = db.query(Appointment).filter(Appointment.status == "confirmed").first()
    phone = "9876500001"  # seeded phone for first appointment
    cancel = cancel_appointment(db, "call-cancel", CancelArgs(phone=phone))
    assert cancel.data["phase"] == "pending_confirmation"
    done = cancel_appointment(db, "call-cancel",
                              CancelArgs(phone=phone, confirmed=True,
                                         confirm_token=cancel.data["confirm_token"]),
                              caller_confirmed=True)
    assert done.ok and db.get(Appointment, appt.id).status == "cancelled"
    assert db.get(Slot, appt.slot_id).status == "available"


@pytest.mark.parametrize("name", ["Mehta", "डॉक्टर मेहता", "મેહતા", "Dr. Patel", "पटेल"])
def test_doctor_resolution_multilingual(db, name):
    assert resolve_doctor(db, name) is not None


def test_concurrent_booking_only_one_wins(tmp_path):
    """Two simultaneous bookings for the same slot: exactly one succeeds."""
    db_file = tmp_path / "concurrent.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False},
                           future=True)
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    Base.metadata.create_all(engine)
    setup = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    s = setup()
    seed(s)
    slot = s.query(Slot).filter(Slot.status == "available").first()
    slot_id = slot.id
    s.close()

    def attempt(i: int) -> bool:
        sess = setup()
        try:
            args = BookAppointmentArgs(slot_id=slot_id, patient_name=f"P{i}",
                                       phone=f"987651234{i}")
            first = book_appointment(sess, f"cc-{i}", args)
            approved = BookAppointmentArgs(slot_id=slot_id, patient_name=f"P{i}",
                                           phone=f"987651234{i}", confirmed=True,
                                           confirm_token=first.data["confirm_token"])
            return book_appointment(sess, f"cc-{i}", approved, caller_confirmed=True).ok
        finally:
            sess.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [1, 2]))
    assert sum(results) == 1, results
