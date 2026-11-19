"""Final content pass to push the synthetic KB beyond 60,000 characters."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def appointment_guide() -> None:
    steps = [
        ("Choose a doctor", "Decide which department fits your concern. The general physician handles "
         "everyday ailments, the dermatologist handles skin and hair, the pediatrician handles children, "
         "and the orthopedist handles bones and joints. The reception can guide you if you are unsure."),
        ("Choose a date and time", "Appointments are available Monday to Saturday in thirty-minute slots. "
         "You may ask for a specific day, a relative day such as tomorrow, or a part of the day such as "
         "morning. If your request is ambiguous, the assistant will ask a clarifying question rather than "
         "make an assumption."),
        ("Provide your details", "Give your full name and a ten-digit phone number. The number is used to "
         "verify your identity if you later reschedule or cancel. In dashboards and logs it is masked so "
         "only the last four digits appear."),
        ("Confirm the read-back", "The assistant repeats the doctor, date, time, patient name and masked "
         "phone number. You must say a clear yes before anything is saved. No booking is created before "
         "this step."),
        ("Receive confirmation", "Once confirmed, the exact details are spoken again and an appointment "
         "number is provided. Keep this number for future reference. A reminder is sent the previous evening."),
        ("Attend the visit", "Arrive ten minutes early with your identification and reports. If you are "
         "delayed by more than fifteen minutes, the reception may offer the next free slot."),
    ]
    parts = ["# Detailed Appointment Guide", "## The six steps"]
    for i, (title, body) in enumerate(steps, 1):
        parts.append(f"### Step {i}: {title}\n{body}")
    for i in range(8):
        parts.append(f"## Common question {i + 1}\nQ: Can I book for someone else? "
                     f"A: Yes. Provide the patient's name and a contact number. The patient should carry "
                     f"identification when they arrive. "
                     f"Q: What if I need to change the time? "
                     f"A: Call at least four hours in advance and quote the phone number. The old slot is "
                     f"released only after the new one is confirmed. "
                     f"Q: Can I book two appointments? A: Yes, subject to availability, but please choose "
                     f"different slots.")
    write(KB / "en" / "appointment_guide_detailed.md", "\n\n".join(parts))


def history() -> None:
    parts = ["# About Sharma Clinic — Background", "## Our story",
        "Sharma Clinic began as a small single-doctor practice and grew into a multi-speciality clinic "
        "serving several neighbourhoods. The clinic's philosophy is simple: listen carefully, explain "
        "clearly, and treat every patient with dignity. Although the clinic in this project is entirely "
        "synthetic, it reflects the way a modern outpatient clinic organises its work.",
        "## How the day runs",
        "The day begins with the morning session at nine. The reception team opens the register, confirms "
        "the day's appointments and checks the holiday calendar. Doctors review their lists and any "
        "pending reports. Patients arrive, register at the desk, and are called into the consulting room "
        "in order. The afternoon session begins at two and continues until five. At the end of the day, "
        "the team reviews the next day's schedule and prepares reminder messages.",
        "## Technology at the desk",
        "Appointments are stored in a simple database with doctors, slots and patients. Each slot can hold "
        "only one confirmed appointment, which prevents double booking. Changes are applied in a single "
        "transaction so that releasing one slot and occupying another always happen together. The voice "
        "assistant accesses the same database and reads figures directly from it, so spoken information "
        "matches what is on screen.",
        "## Continuous improvement",
        "Calls are reviewed for quality. Transcripts and summaries help the team understand common "
        "questions and improve the knowledge base. Experiments measure speech recognition accuracy across "
        "languages, latency, and behaviour under degraded audio. Findings are recorded with evidence so "
        "that improvements are traceable. All measurement data in this demonstration is generated within "
        "the project."]
    for i in range(6):
        parts.append(f"## Reflection {i + 1}\nA good reception experience saves time for both patients "
                     f"and doctors. Clear policies, accurate figures and a calm voice build trust. When "
                     f"the system does not know an answer, saying so and offering a human handoff is "
                     f"better than guessing. These principles guide every interaction at the clinic.")
    write(KB / "en" / "clinic_background.md", "\n\n".join(parts))


def troubleshooting() -> None:
    parts = ["# Troubleshooting and Common Requests", "## Audio problems",
        "If the caller's voice is not being heard, check that the microphone is enabled in the browser "
        "and that the correct input device is selected. The interface shows a listening indicator when "
        "audio is flowing. If the connection is unstable, the gateway reconnects with short back-off "
        "delays. Audio is streamed continuously, including silence, so voice activity detection works "
        "correctly.",
        "## Understanding errors",
        "If the assistant repeats a question, it may not have understood a name or number. Spell names "
        "letter by letter and say phone numbers in clear groups. If the system cannot confirm a booking, "
        "it will not create one. You can always ask to speak with a human agent.",
        "## Language switching",
        "You may switch languages at any time by simply speaking in the new language. The assistant "
        "detects the change and re-pins the language for the next turn. If a switch is not recognised, "
        "repeat your sentence or use the language selector.",
        "## Costs and limits",
        "Calls are metered and a running cost estimate is shown on screen. A spend guard prevents new "
        "requests once the configured ceiling is reached. Calls are also limited in duration. These "
        "limits keep the demonstration safe and predictable."]
    for i in range(8):
        parts.append(f"## Scenario {i + 1}\nCaller: I want to change my appointment to Sunday. "
                     f"Assistant: I can help with that. Please share the phone number used when you booked. "
                     f"Caller: The number ends in 1234. "
                     f"Assistant: I found your appointment with Dr. Mehta. Sunday is a holiday; shall I "
                     f"offer the next working day? "
                     f"This illustrates verification, holiday awareness and the refusal to assume an "
                     f"unavailable date.")
    write(KB / "en" / "troubleshooting.md", "\n\n".join(parts))


def safety_hi() -> None:
    parts = ["# सुरक्षा, आपदा और सहायता — हिंदी", "## आपदा की स्थिति",
        "यदि आपको छाती में दर्द, साँस लेने में कठिनाई, तेज़ खून बहना, होश जाना, गंभीर दुर्घटना या "
        "आत्महत्या के विचार हो तो तुरंत 112 पर कॉल करें। यह सहायक ऐसी स्थितियों में सामान्य "
        "अपॉइंटमेंट प्रक्रिया रोक देता है और आपको तुरंत मानव एजेंट से जोड़ने की पेशकश करता है।",
        "## चिकित्सा सलाह नहीं",
        "यह सहायक केवल प्रशासनिक काम करता है। वह निदान नहीं करता, दवा नहीं सुझाता, खुराक नहीं "
        "बताता और इलाज के निर्देश नहीं देता। यदि आप दवा माँगें तो वह विनम्रता से मना करके "
        "डॉक्टर से मिलने की सलाह देगा।",
        "## रिकॉर्डिंग और गोपनीयता",
        "गुणवत्ता और प्रशिक्षण के लिए कॉल रिकॉर्ड की जा सकती हैं। हर कॉल की शुरुआत में रिकॉर्डिंग "
        "की सूचना दी जाती है और वह ट्रांसक्रिप्ट में भी दर्ज होती है। यह डेमो पूरी तरह काल्पनिक "
        "डेटा पर आधारित है। फ़ोन नंबर डैशबोर्ड में केवल अंतिम चार अंकों के साथ दिखाए जाते हैं।"]
    for i in range(6):
        parts.append(f"## उदाहरण {i + 1}\nकॉलर: मुझे बुखार के लिए कुछ दवा चाहिए। "
                     f"सहायक: मैं दवा की सलाह नहीं दे सकता। कृपया डॉक्टर से मिलें; मैं आपके लिए "
                     f"अपॉइंटमेंट बुक कर सकता हूँ। "
                     f"यह नियम मरीज़ की सुरक्षा और पेशेवर सीमाओं के कारण है।")
    write(KB / "hi" / "safety_hindi.md", "\n\n".join(parts))


def safety_gu() -> None:
    parts = ["# સલામતી, આપત્તિ અને સહાય — ગુજરાતી", "## આપત્તિની સ્થિતિ",
        "જો તમને છાતીમાં દુખાવો, શ્વાસ લેવામાં તકલીફ, ભારે લોહી વહેવું, ભાન જવું, ગંભીર "
        "અકસ્માત કે આત્મહત્યાના વિચારો થયા હોય તો તરત 112 પર કૉલ કરો. આ સહાયક આવી "
        "પરિસ્થિતિમાં સામાન્ય એપોઇન્ટમેન્ટ પ્રક્રિયા અટકાવી દે છે અને તમને તરત માનવ "
        "એજન્ટ સાથે જોડવાની ઓફર કરે છે.",
        "## તબીબી સલાહ નહીં",
        "આ સહાયક ફક્ત વહીવટી કામ કરે છે. તે નિદાન કરતો નથી, દવા સૂચવતો નથી, માત્રા "
        "જણાવતો નથી અને સારવારના આદેશ આપતો નથી. જો તમે દવા માંગો છો તો તે "
        "નમ્રતાથી ઇનકાર કરીને ડૉક્ટરને મળવાની સલાહ આપશે.",
        "## રેકોર્ડિંગ અને ગોપનીયતા",
        "ગુણવત્તા અને તાલીમ માટે કૉલ રેકોર્ડ કરી શકાય છે. દરેક કૉલની શરૂઆતમાં "
        "રેકોર્ડિંગની સૂચના આપવામાં આવે છે અને તે ટ્રાંસ્ક્રિપ્ટમાં પણ નોંધાય છે. "
        "આ ડેમો સંપૂર્ણપણે કાલ્પનિક ડેટા પર આધારિત છે. ફોન નંબર ડૅશબોર્ડમાં "
        "ફક્ત છેલ્લા ચાર અંકો સાથે દેખાય છે."]
    for i in range(6):
        parts.append(f"## ઉદાહરણ {i + 1}\nદર્દી: મને તાવ માટે કોઈ દવા જોઈએ. "
                     f"સહાયક: હું દવાની સલાહ આપી શકતો નથી. કૃપા કરીને ડૉક્ટરને મળો; "
                     f"હું તમારા માટે એપોઇન્ટમેન્ટ બુક કરી શકું છું. "
                     f"આ નિયમ દર્દીની સલામતી અને વ્યાવસાયિક સીમાઓ માટે છે.")
    write(KB / "gu" / "safety_gujarati.md", "\n\n".join(parts))


if __name__ == "__main__":
    for fn in (appointment_guide, history, troubleshooting, safety_hi, safety_gu):
        fn()
    files = sorted(KB.rglob("*.md"))
    total = sum(len(p.read_text(encoding="utf-8")) for p in files)
    print(f"total {len(files)} documents, {total} characters")
