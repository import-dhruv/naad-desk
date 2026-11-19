"""Multilingual relative-date resolution in Asia/Kolkata (PRD §8.5).

Supports Hindi (Devanagari + Latin/Hinglish), Gujarati (Gujarati script +
transliteration), and English. Ambiguous references return `ambiguous=True`
so the orchestrator asks a clarification question instead of assuming.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ..config import settings

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(settings.timezone)
except Exception:  # pragma: no cover
    from datetime import timezone
    TZ = timezone.utc

DEVANAGARI_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("०१२३४५६७८९")}
GUJARATI_DIGITS = {ord(c): ord(str(i)) for i, c in enumerate("૦૧૨૩૪૫૬૭૮૯")}

WEEKDAYS: dict[str, int] = {
    # English
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    # Hindi (Devanagari)
    "सोमवार": 0, "मंगलवार": 1, "बुधवार": 2, "गुरुवार": 3,
    "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6, "वह": 4,
    # Hindi (Latin)
    "somvar": 0, "mangalvar": 1, "budhvar": 2, "guruvar": 3,
    "shukrvar": 4, "shaniwar": 5, "shamvar": 5, "ravivar": 6,
    # Gujarati
    "સોમવાર": 0, "મંગળવાર": 1, "બુધવાર": 2, "ગુરુવાર": 3,
    "શુક્રવાર": 4, "શનિવાર": 5, "રવિવાર": 6,
    # Gujarati transliteration shares the Latin-script forms above.
}

TODAY_WORDS = {"aaj", "आज", "આજ", "today"}
TOMORROW_WORDS = {"kal", "कल", "કાલ", "कल्", "tomorrow", "tomorrow morning"}
DAY_AFTER_WORDS = {"parso", "परसों", "પરસો", "day after tomorrow"}
NEXT_WORDS = {"agle", "अगले", "આગલા", "next", "agla", "coming"}
THIS_WORDS = {"this", "इस", "આ"}
WEEKEND_WORDS = {"weekend", "वीकेंड", "સપ્તાહાંત", "week end"}

PART_OF_DAY: dict[str, str] = {
    "morning": "morning", "subah": "morning", "सुबह": "morning", "સવાર": "morning",
    "savare": "morning", "જલદી": "morning",
    "afternoon": "afternoon", "dopahar": "afternoon", "दोपहर": "afternoon",
    "બપોર": "afternoon", "bapori": "afternoon",
    "evening": "evening", "shaam": "evening", "शाम": "evening", "સાંજ": "evening",
    "sanj": "evening",
    "night": "evening", "raat": "evening", "रात": "evening", "રાત": "evening",
}


@dataclass
class DateResolution:
    date: date | None
    part_of_day: str = "any"
    ambiguous: bool = False
    reason: str = ""
    matched: str = ""

    @property
    def iso(self) -> str | None:
        return self.date.isoformat() if self.date else None


def normalize(text: str) -> str:
    text = unicodedata_normalize(text)
    text = text.translate(DEVANAGARI_DIGITS).translate(GUJARATI_DIGITS)
    text = text.lower().strip()
    text = re.sub(r"[.,!?।]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def unicodedata_normalize(text: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFC", text)


def _next_weekday(base: date, target: int, next_week: bool = True) -> date:
    delta = (target - base.weekday()) % 7
    if delta == 0:
        delta = 7 if next_week else 0
    return base + timedelta(days=delta)


def resolve_date(text: str, now: datetime | None = None) -> DateResolution:
    """Resolve a free-form date reference relative to `now` (Asia/Kolkata)."""
    now = now or datetime.now(TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=TZ)
    base = now.date()
    t = normalize(text)
    words = set(t.split())

    # part of day
    pod = "any"
    for word in words:
        if word in PART_OF_DAY:
            pod = PART_OF_DAY[word]
            break

    # Explicit ISO date
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        try:
            return DateResolution(date.fromisoformat(m.group(0)), pod, matched=m.group(0))
        except ValueError:
            pass

    # DD/MM or DD-MM
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", t)
    if m:
        try:
            d = date(base.year, int(m.group(2)), int(m.group(1)))
            if d < base:
                d = d.replace(year=base.year + 1)
            return DateResolution(d, pod, matched=m.group(0))
        except ValueError:
            pass

    if words & TODAY_WORDS:
        return DateResolution(base, pod, matched=next(w for w in words if w in TODAY_WORDS))
    if words & TOMORROW_WORDS:
        return DateResolution(base + timedelta(days=1), pod,
                              matched=next(w for w in words if w in TOMORROW_WORDS))
    if words & DAY_AFTER_WORDS:
        return DateResolution(base + timedelta(days=2), pod,
                              matched=next(w for w in words if w in DAY_AFTER_WORDS))

    if words & WEEKEND_WORDS:
        # Upcoming Saturday; ambiguous between Sat/Sun -> clarify.
        sat = _next_weekday(base, 5)
        return DateResolution(sat, pod, ambiguous=True,
                              reason="Weekend could mean Saturday or Sunday.", matched="weekend")

    # weekday with modifier
    weekday_word = next((w for w in words if w in WEEKDAYS), None)
    if weekday_word is not None:
        target = WEEKDAYS[weekday_word]
        if words & NEXT_WORDS:
            return DateResolution(_next_weekday(base, target, True), pod, matched=weekday_word)
        if words & THIS_WORDS:
            delta = (target - base.weekday()) % 7
            return DateResolution(base + timedelta(days=delta), pod,
                                  ambiguous=(delta == 0 and pod == "any"),
                                  reason="Today is also this weekday." if delta == 0 else "",
                                  matched=weekday_word)
        # Bare weekday: ambiguous (this vs next).
        return DateResolution(_next_weekday(base, target, True), pod, ambiguous=True,
                              reason="Bare weekday: this or next week?", matched=weekday_word)

    if "number" in words or "number vala" in t or re.search(r"\d{1,2}", t):
        # A bare number like "5" is ambiguous as a date.
        return DateResolution(None, pod, ambiguous=True, reason="Bare number is not a resolvable date.")

    return DateResolution(None, pod, ambiguous=False,
                          reason="No date reference found.", matched="")


def format_date_human(d: date, language: str = "hi") -> str:
    """Deterministic spoken date string (no LLM)."""
    months_en = ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"]
    if language == "gu":
        months = ["જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ", "મે", "જૂન", "જુલાઈ",
                  "ઓગસ્ટ", "સપ્ટેમ્બર", "ઓક્ટોબર", "નવેમ્બર", "ડિસેમ્બર"]
        return f"{d.day} {months[d.month - 1]} {d.year}"
    if language == "en-in" or language == "en":
        return f"{d.day} {months_en[d.month - 1]} {d.year}"
    months_hi = ["जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई",
                 "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
    return f"{d.day} {months_hi[d.month - 1]} {d.year}"
