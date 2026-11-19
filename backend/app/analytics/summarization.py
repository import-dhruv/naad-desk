"""Three-bullet summary in the call's primary language (§10.5)."""
from __future__ import annotations


def build_summary(extraction: dict, language: str) -> str:
    bullets = [b for b in (extraction.get("summary_bullets") or []) if str(b).strip()]
    bullets = bullets[:3]
    if not bullets:
        goal = extraction.get("caller_goal") or "general enquiry"
        achieved = extraction.get("goal_achieved")
        if language == "gu":
            bullets = [f"દર્દીએ {goal} માટે પૂછ્યું.",
                       ("એપોઇન્ટમેન્ટ કન્ફર્મ થઈ." if achieved else "એપોઇન્ટમેન્ટ કન્ફર્મ થઈ નહીં."),
                       "વધારાની સહાયની વિનંતી નથી."]
        elif language == "hi":
            bullets = [f"कॉलर ने {goal} के बारे में पूछा।",
                       ("अपॉइंटमेंट पक्की हो गई।" if achieved else "अपॉइंटमेंट पक्की नहीं हुई।"),
                       "कोई अतिरिक्त सहायता नहीं मांगी गई।"]
        else:
            bullets = [f"Caller asked about {goal}.",
                       ("Appointment was booked." if achieved else "Appointment was not booked."),
                       "No additional assistance requested."]
    return "\n".join(f"- {b}" for b in bullets)
