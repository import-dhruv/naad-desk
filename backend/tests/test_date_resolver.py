"""Date resolution tests (PRD §8.5)."""
from __future__ import annotations

from datetime import datetime

import pytest
from app.tools.date_resolver import format_date_human, normalize, resolve_date

NOW = datetime(2026, 11, 19, 10, 0)  # Thursday


@pytest.mark.parametrize("text,expected_offset", [
    ("aaj", 0), ("आज", 0), ("today", 0),
    ("kal", 1), ("कल", 1), ("કાલ", 1), ("tomorrow", 1),
    ("parso", 2), ("परसों", 2),
    ("appointment kal subah", 1), ("कल सुबह", 1),
])
def test_relative_days(text, expected_offset):
    r = resolve_date(text, NOW)
    assert r.ambiguous is False
    assert (r.date - NOW.date()).days == expected_offset


def test_part_of_day():
    assert resolve_date("kal subah", NOW).part_of_day == "morning"
    assert resolve_date("tomorrow afternoon", NOW).part_of_day == "afternoon"
    assert resolve_date("परसों शाम", NOW).part_of_day == "evening"


def test_next_friday():
    r = resolve_date("agle Friday", NOW)
    assert r.ambiguous is False
    assert r.date.weekday() == 4
    assert (r.date - NOW.date()).days > 0


def test_hindi_weekday():
    r = resolve_date("अगले शुक्रवार", NOW)
    assert r.date.weekday() == 4


def test_gujarati_weekday():
    r = resolve_date("આગલા શુક્રવાર", NOW)
    assert r.date.weekday() == 4


def test_bare_weekday_ambiguous():
    r = resolve_date("Friday", NOW)
    assert r.ambiguous is True


def test_weekend_ambiguous():
    r = resolve_date("this weekend", NOW)
    assert r.ambiguous is True


def test_iso_date():
    r = resolve_date("2026-12-01", NOW)
    assert r.iso == "2026-12-01"


def test_no_date():
    r = resolve_date("fee kya hai", NOW)
    assert r.date is None
    assert r.ambiguous is False


def test_devanagari_digits_normalized():
    assert normalize("१२३") == "123"
    assert normalize("૪૫૬") == "456"


@pytest.mark.parametrize("lang", ["hi", "gu", "en-in"])
def test_format_date_human(lang):
    from datetime import date
    out = format_date_human(date(2026, 12, 1), lang)
    assert "1" in out
