# 24-Scenario Replay Results

Generated: 2026-11-19T05:33:58.947408+00:00

Passed 12 · Observed 10 · Failed 2 · Total 24

| ID | Scenario | Status | Tools |
|---|---|---|---|
| S01 | Clinic timings | pass | — |
| S02 | Consultation fee | pass | get_fees |
| S03 | Next available appointment | pass | search_availability |
| S04 | Specific doctor/date/time | fail | book_appointment |
| S05 | Relative date | pass | search_availability |
| S06 | Unavailable slot | pass | search_availability |
| S07 | Reschedule | pass | reschedule_appointment |
| S08 | Cancel | pass | cancel_appointment |
| S09 | Documents required | pass | — |
| S10 | Location and parking | observed | — |
| S11 | Medicine request | pass | — |
| S12 | Emergency | pass | — |
| S13 | Human handoff | observed | handoff_to_human |
| S14 | Interrupt long response | observed | — |
| S15 | Hindi to English switch | pass | — |
| S16 | Gujarati to Hindi switch | pass | — |
| S17 | Extended silence | observed | — |
| S18 | Background noise | observed | — |
| S19 | Spell unusual name | observed | — |
| S20 | Dictate phone | observed | — |
| S21 | Unrelated question | observed | — |
| S22 | Ambiguous date | observed | search_availability |
| S23 | Fee then booking | fail | — |
| S24 | Correct a date | observed | reschedule_appointment |
