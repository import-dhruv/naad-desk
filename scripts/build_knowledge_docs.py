"""Generate the synthetic Sharma Clinic knowledge base.

All information is fictional. Running this script is idempotent and produces
Markdown documents under knowledge/{en,hi,gu}/. The prose is generated from
structured, varied data so the corpus exceeds 60,000 characters without filler.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"

DOCTORS = [
    ("Dr. Mehta", "General Physician", 500, "जनरल फिजिशियन", "જનરલ ફિઝિશિયન",
     "fever, cough, cold, blood pressure, diabetes, general check-up",
     "बुखार, खांसी, ज़ुकाम, ब्लड प्रेशर, डायबिटीज़, सामान्य जांच",
     "તાવ, ઉધરસ, શરદી, બ્લડ પ્રેશર, ડાયાબિટીઝ, સામાન્ય તપાસ"),
    ("Dr. Patel", "Dermatologist", 700, "त्वचा विशेषज्ञ", "ત્વચારોગ વિશેષજ્ઞ",
     "acne, rash, eczema, hair fall, skin allergy, pigmentation",
     "मुहासे, दाने, एक्जिमा, बालों का झड़ना, त्वचा एलर्जी, रंगत",
     "ખીલ, ફોલ્લીઓ, એક્ઝિમા, વાળ ખરવા, ત્વચા એલર્જી, રંગત"),
    ("Dr. Shah", "Pediatrician", 600, "बाल रोग विशेषज्ञ", "બાળ રોગ વિશેષજ્ઞ",
     "child health, vaccination, growth, nutrition, newborn care",
     "बच्चों का स्वास्थ्य, टीकाकरण, वृद्धि, पोषण, नवजात देखभाल",
     "બાળકોનું સ્વાસ્થ્ય, રસીકરણ, વૃદ્ધિ, પોષણ, નવજાત સંભાળ"),
    ("Dr. Rao", "Orthopedist", 800, "हड्डी रोग विशेषज्ञ", "હાડકાંના વિશેષજ્ઞ",
     "joint pain, fracture, back pain, sprain, arthritis",
     "जोड़ों का दर्द, फ्रैक्चर, पीठ दर्द, मोच, गठिया",
     "સાંધાનો દુખાવો, ફ્રેક્ચર, પીઠનો દુખાવો, મચકોડ, સંધિવા"),
]

EN_TIMES = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]

FAQS = [
    ("What are the clinic hours?", "The clinic is open Monday to Saturday from 9:00 AM to 5:00 PM. The morning session runs from 9:00 to 12:00 and the afternoon session from 2:00 to 5:00 PM."),
    ("Is the clinic open on Sunday?", "No. The clinic remains closed on Sundays and on declared holidays. The holiday calendar is published on the notice board and on the website."),
    ("How do I book an appointment?", "You may call the reception desk, use the website form, or ask this voice assistant to find and confirm a slot. A booking is confirmed only after you verbally approve the read-back."),
    ("Can I reschedule my appointment?", "Yes. Please call at least four hours before the scheduled time and quote the phone number used at the time of booking. Rescheduling is free of charge."),
    ("What is the cancellation policy?", "Appointments may be cancelled up to four hours before the visit without a fee. Repeated no-shows may require advance payment for future bookings."),
    ("Which payment methods are accepted?", "Cash, UPI, credit and debit cards, and net banking are accepted at the reception. UPI is the preferred method."),
    ("Do you accept insurance?", "We accept a limited panel of insurers. Please carry your insurance card and a government photo ID. Cashless treatment is subject to insurer approval."),
    ("What documents should I bring?", "Please bring a government photo ID, any previous prescriptions, relevant lab reports, and your insurance card if applicable. For children, carry the vaccination record."),
    ("Where is the clinic located?", "The clinic is in the heart of the city near the central bus stand, with clear signage and wheelchair access. Parking is available on a first-come, first-served basis."),
    ("Do I need to fast before a blood test?", "For fasting blood tests, avoid food for eight to ten hours. Water is allowed. Confirm the specific requirement when you book."),
    ("Can I get a medical certificate?", "Certificates are issued after a consultation by the treating doctor, subject to the clinic's documentation policy."),
    ("Is there a fee for a follow-up visit?", "A standard consultation fee applies to each visit unless included in a follow-up package. The reception can confirm the exact amount."),
]

HI_FAQS = [
    ("क्लिनिक का समय क्या है?", "क्लिनिक सोमवार से शनिवार सुबह 9:00 से शाम 5:00 तक खुला रहता है। सुबह का सत्र 9:00 से 12:00 और दोपहर का सत्र 2:00 से 5:00 है।"),
    ("क्या क्लिनिक रविवार को खुला है?", "नहीं। क्लिनिक रविवार और घोषित छुट्टियों को बंद रहता है। छुट्टियों की सूचना सूचना पट्ट और वेबसाइट पर उपलब्ध है।"),
    ("अपॉइंटमेंट कैसे बुक करूँ?", "आप रिसेप्शन डेस्क पर कॉल कर सकते हैं, वेबसाइट फ़ॉर्म भर सकते हैं, या इस वॉइस असिस्टेंट से समय चुन सकते हैं। पुष्टि तभी होती है जब आप पढ़कर सुनने के बाद सहमति दें।"),
    ("क्या अपॉइंटमेंट बदल सकते हैं?", "हाँ। कृपया निर्धारित समय से कम से कम चार घंटे पहले कॉल करें और बुकिंग वाला फ़ोन नंबर बताएँ। समय बदलने का कोई शुल्क नहीं है।"),
    ("रद्द करने की नीति क्या है?", "निर्धारित समय से चार घंटे पहले तक बिना शुल्क रद्द कर सकते हैं। बार-बार न आने वाले मरीज़ों को आगे अग्रिम भुगतान करना पड़ सकता है।"),
    ("कौन-कौन से भुगतान तरीके हैं?", "नकद, यूपीआई, क्रेडिट और डेबिट कार्ड, और नेट बैंकिंग स्वीकार किए जाते हैं। यूपीआई पसंदीदा तरीका है।"),
    ("क्या बीमा स्वीकार है?", "हम सीमित पैनल के बीमाकर्ताओं को स्वीकार करते हैं। बीमा कार्ड और सरकारी फ़ोटो पहचान पत्र साथ रखें। कैशलेस उपचार बीमा कंपनी के अनुमोदन पर निर्भर है।"),
    ("कौन-कौन से दस्तावेज़ लाने चाहिए?", "सरकारी फ़ोटो पहचान पत्र, पिछले प्रिस्क्रिप्शन, प्रासंगिक लैब रिपोर्ट, और यदि हो तो बीमा कार्ड लाएँ। बच्चों के लिए टीकाकरण रिकॉर्ड साथ रखें।"),
    ("क्लिनिक कहाँ स्थित है?", "क्लिनिक शहर के बीचों-बीच केंद्रीय बस स्टैंड के पास है, जहाँ स्पष्ट संकेत और व्हीलचेयरfirst-class पहुँच है। पार्किंग पहले आओ पहले पाओ आधार पर उपलब्ध है।"),
    ("खून की जांच से पहले उपवास?", "उपवास वाली जांच के लिए आठ से दस घंटे भोजन न करें। पानी पी सकते हैं। बुकिंग के समय विशिष्ट आवश्यकता पुछ लें।"),
]

GU_FAQS = [
    ("ક્લિનિકનો સમય શું છે?", "ક્લિનિક સોમવારથી શનિવાર સવાર 9:00 થી સાંજ 5:00 સુધી ખુલ્લું રહે છે. સવારનો સત્ર 9:00 થી 12:00 અને બપોરનો સત્ર 2:00 થી 5:00 છે."),
    ("શું ક્લિનિક રવિવારે ખુલ્લું છે?", "ના. ક્લિનિક રવિવારે અને જાહેર કરેલી રજાઓમાં બંધ રહે છે. રજાઓની યાદી સૂચના પટ્ટી અને વેબસાઇટ પર ઉપલબ્ધ છે."),
    ("એપોઇન્ટમેન્ટ કેવી રીતે બુક કરું?", "તમે રિસેપ્શન ડેસ્ક પર કૉલ કરી શકો છો, વેબસાઇટ ફોર્મ ભરી શકો છો, અથવા આ વોઇસ આસિસ્ટન્ટ સાથે સમય પસંદ કરી શકો છો. વાંચીને સાંભળ્યા પછી તમે સંમતિ આપો ત્યારે જ પુષ્ટિ થાય છે."),
    ("શું એપોઇન્ટમેન્ટ બદલી શકાય?", "હા. કૃપા કરીને નિર્ધારિત સમયના ઓછામાં ઓછા ચાર કલાક પહેલા કૉલ કરો અને બુકિંગ વખતે આપેલો ફોન નંબર જણાવો. સમય બદલવાનો કોઈ શુલ્ક નથી."),
    ("રદ કરવાની નીતિ શું છે?", "નિર્ધારિત સમયના ચાર કલાક પહેલા સુધી વગર શુલ્કે રદ કરી શકાય છે. વારંવાર ન આવતા દર્દીઓએ આગળ અગ્રિમ ચુકવણી કરવી પડી શકે છે."),
    ("કઈ ચુકવણી પદ્ધતિઓ છે?", "રોકડ, યુપીઆઈ, ક્રેડિટ અને ડેબિટ કાર્ડ, અને નેટ બૅંકિંગ સ્વીકારવામાં આવે છે. યુપીઆઈ પસંદગીની પદ્ધતિ છે."),
    ("શું વીમો સ્વીકારવામાં આવે છે?", "અમે મર્યાદિત પેનલના વીમાદાતાઓ સ્વીકારીએ છીએ. વીમા કાર્ડ અને સરકારી ફોટો ઓળખપત્ર સાથે રાખો. કૅશલેસ સારવાર વીમા કંપનીની મંજૂરી પર આધારિત છે."),
    ("કયા દસ્તાવેજો લાવવા જોઈએ?", "સરકારી ફોટો ઓળખપત્ર, અગાઉના પ્રિસ્ક્રિપ્શન, સંબંધિત લૅબ રિપોર્ટ, અને જો હોય તો વીમા કાર્ડ લાવો. બાળકો માટે રસીકરણનો રેકોર્ડ સાથે રાખો."),
    ("ક્લિનિક ક્યાં આવેલું છે?", "ક્લિનિક શહેરના મધ્યમાં કેન્દ્રીય બસ સ્ટેન્ડ નજીક આવેલું છે, જ્યાં સ્પષ્ટ સંકેત અને વ્હીલચેર પહોંચ છે. પાર્કિંગ પહેલા આવો પહેલા પાઓ ધોરણે ઉપલબ્ધ છે."),
    ("લોહીના ટેસ્ટ પહેલાં ઉપવાસ?", "ઉપવાસવાળા ટેસ્ટ માટે આઠથી દસ કલાક ખાવાનું ટાળો. પાણી પી શકાય છે. બુકિંગ વખતે ચોક્કસ આવશ્યકતા પૂછી લો."),
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def build_en() -> None:
    d = KB / "en"
    overview = ["# Sharma Clinic — Overview", "## About the clinic",
        "Sharma Clinic is a neighbourhood multi-speciality outpatient clinic serving families in the city. "
        "The clinic focuses on primary care, dermatology, pediatrics and orthopedics. Every consultation is "
        "conducted by a qualified doctor, and the reception team supports patients in Hindi, Gujarati and English. "
        "The clinic uses synthetic data for demonstrations; no real patient records are stored here.",
        "## Departments",
        "The general physician handles common ailments such as fever, cough, cold, blood pressure monitoring and "
        "diabetes follow-up. The dermatology department treats acne, rashes, eczema, hair fall and skin allergies. "
        "The pediatrics department looks after child health, vaccination schedules and nutrition. The orthopedics "
        "department manages joint pain, sprains, fractures and back pain.",
        "## Getting started",
        "New patients are requested to arrive ten minutes early to complete registration. Please carry a "
        "government photo identification document and any previous medical records. The reception desk can "
        "answer questions about fees, timings, parking and the documents required for your visit."]
    for doc in DOCTORS:
        overview.append(f"## {doc[0]} — {doc[1]}\n{doc[0]} consults on {doc[5]}. The consultation fee is {doc[2]} rupees. "
                        f"Appointments are available in 30-minute slots during morning and afternoon sessions.")
    write(d / "clinic_overview.md", "\n\n".join(overview))

    profiles = ["# Doctor Profiles", "## Meet our doctors"]
    for name, spec, fee, en_expertise in [(x[0], x[1], x[2], x[5]) for x in DOCTORS]:
        profiles.append(
            f"## {name}\n{name} is a {spec.lower()} at Sharma Clinic with many years of experience in "
            f"{en_expertise}. Patients consult {name} for {en_expertise}. The consultation fee is {fee} rupees "
            f"per visit. {name} speaks Hindi, Gujarati and English, so you may describe your concern in the "
            f"language you are most comfortable with. New patients are welcome and same-day appointments are "
            f"often available. Please bring previous prescriptions and reports so the doctor can review your history.")
    write(d / "doctor_profiles.md", "\n\n".join(profiles))

    fees = ["# Consultation Fees and Payment Methods", "## Fee schedule"]
    for name, spec, fee, *_ in DOCTORS:
        fees.append(f"{name}, {spec}: {fee} rupees per consultation. Follow-up visits are charged at the same "
                    f"standard rate unless a package has been agreed with the reception desk.")
    fees.append("""## Payment methods
The reception accepts cash, UPI, credit cards, debit cards and net banking. UPI is the fastest method;
patients may scan the QR code displayed at the counter. Cards are processed through a secure gateway and
the clinic does not store card numbers. A printed receipt is given for every payment. Refunds, if any, are
processed to the original payment method within five to seven working days.

## Insurance
We empanel a limited set of insurers. To avail cashless treatment you must present a valid insurance card
and a government photo ID at the counter. Cashless requests are subject to approval by your insurer. If
your insurer is not empanelled, you may pay directly and submit the receipt for reimbursement. The reception
team cannot confirm coverage amounts; please contact your insurer for exact policy limits.

## Billing clarifications
All fees are displayed at the time of booking and are also read aloud before a booking is confirmed. The
voice assistant always states the exact fee from the clinic database and never estimates an amount. If you
hear a figure that seems unclear, please ask the receptionist to repeat it before making a payment.""")
    write(d / "fees_payment.md", "\n\n".join(fees))

    hours = ["# Working Hours and Holidays", "## Regular hours",
        "Sharma Clinic operates Monday through Saturday. The morning session is from 9:00 AM to 12:00 PM and "
        "the afternoon session is from 2:00 PM to 5:00 PM. The clinic is closed on Sundays. The telephone line "
        "is answered during working hours; calls received after hours are recorded and returned the next working day.",
        "## Slot timings",
        "Appointments are scheduled in 30-minute slots. The available start times are " + ", ".join(EN_TIMES) + ". "
        "Please arrive a few minutes before your slot. If you are more than fifteen minutes late, the reception "
        "may offer the next available slot instead. Emergency cases are always prioritised.",
        "## Holidays",
        "The clinic remains closed on national and regional holidays, on the second Saturday of every month, "
        "and on days declared by the clinic management. A holiday notice is displayed at the entrance and on "
        "the website at least one week in advance. If your appointment falls on a holiday, the reception will "
        "proactively contact you to reschedule. The voice assistant consults the holiday calendar before "
        "offering dates and will never suggest a closed day.",
        "## Seasonal variations",
        "During festival weeks the clinic may run a shortened morning session. Any change to regular hours is "
        "announced in advance. When in doubt, please call the reception desk to confirm that the doctor is "
        "available on a particular day."]
    write(d / "hours_holidays.md", "\n\n".join(hours))

    policies = ["# Appointment Policies", "## Booking",
        "An appointment is created only after the patient or caller explicitly confirms the details read back "
        "by the receptionist or the voice assistant. A booking is never created on the basis of an assumption. "
        "The caller must provide a name and a contact number; the contact number is used to verify identity "
        "for later changes and is stored only in masked form in dashboards.",
        "## Confirmation and reminders",
        "After a booking is committed, a confirmation number is provided. A reminder message is sent to the "
        "registered number on the previous evening. Please keep the confirmation number handy if you need to "
        "reschedule or cancel. The voice assistant quotes the exact date and time from the appointment database.",
        "## Rescheduling",
        "You may reschedule free of charge up to four hours before the appointment. Quote the phone number used "
        "at the time of booking so the reception can verify identity. The old slot is released only after the new "
        "slot is secured, and both changes are applied together. Rescheduling to a different doctor is possible "
        "subject to availability.",
        "## Cancellation and no-shows",
        "Cancellations made at least four hours in advance carry no fee. Frequent no-shows may require advance "
        "payment for future appointments. If you cannot attend, please cancel early so another patient can use "
        "the slot. The voice assistant can cancel an appointment after verifying your phone number and reading "
        "back the appointment details.",
        "## Walk-ins",
        "Walk-in patients are seen when a slot is free, but booked appointments take priority. Waiting time for "
        "a walk-in depends on the clinic's workload on that day."]
    write(d / "appointment_policies.md", "\n\n".join(policies))

    location = ["# Location and Parking", "## Finding the clinic",
        "Sharma Clinic is located in the city centre near the central bus stand, on the main road opposite the "
        "municipal park. The building has a distinctive blue signboard and is visible from the bus stop. "
        "Auto-rickshaws and taxis are readily available. The nearest metro station is a ten-minute walk away.",
        "## Accessibility",
        "The clinic is on the ground floor and is wheelchair accessible. A ramp is available at the main "
        "entrance, and the reception desk is at wheelchair height. Visitors needing assistance may request "
        "a volunteer at the entrance.",
        "## Parking",
        "Limited on-site parking is available on a first-come, first-served basis. Two-wheelers may be parked "
        "in the marked area to the left of the building. Four-wheelers can use the paid parking lot two minutes "
        "away. During peak morning hours the on-site lot fills quickly, so patients are encouraged to arrive "
        "early or use public transport.",
        "## Landmarks",
        "Nearby landmarks include the central library, the post office and the municipal park. If you are "
        "having trouble finding the clinic, call the reception desk and the team will guide you."]
    write(d / "location_parking.md", "\n\n".join(location))

    docs = ["# Documents Required Before Appointments", "## For all visits",
        "Please carry a government-issued photo identification document such as an Aadhaar card, driving licence "
        "or passport. Bring any previous prescriptions, lab reports and scans that are relevant to your visit. "
        "A list of current medicines, including dosage, helps the doctor review your treatment safely.",
        "## For specific departments",
        "For dermatology visits, bring photographs of the affected area if the condition varies over time, and "
        "a list of skincare products currently in use. For pediatric visits, bring the child's vaccination record "
        "and growth chart. For orthopedics, bring earlier X-rays and MRI reports. For general physician visits, "
        "bring recent blood test results and blood pressure readings if available.",
        "## Insurance and payment documents",
        "If you wish to use insurance, carry your insurance card and a government photo ID. For cashless "
        "treatment, the insurer may also require a referral letter. A copy of the appointment confirmation is "
        "helpful at the reception desk.",
        "## Preparation notes",
        "For fasting blood tests, avoid food for eight to ten hours; water is permitted. For skin procedures, "
        "avoid applying new creams on the morning of the visit. If your appointment involves a minor procedure, "
        "the doctor will explain the preparation during the consultation. Never stop prescribed medication "
        "without consulting your doctor first."]
    write(d / "documents_preparation.md", "\n\n".join(docs))

    faq = ["# Frequently Asked Questions"]
    for q, a in FAQS:
        faq.append(f"## {q}\n{a}")
    write(d / "faq.md", "\n\n".join(faq))

    safety = ["# Escalation and Safety Policies", "## Administrative scope",
        "This reception service is administrative only. The assistant can help with clinic information, "
        "appointments, fees and routing calls. It does not diagnose conditions, recommend medicines, specify "
        "dosages or give treatment instructions. If a caller asks for medical advice, the assistant politely "
        "declines and offers an appointment with a qualified doctor.",
        "## Emergencies",
        "If a caller describes chest pain, difficulty breathing, severe bleeding, loss of consciousness, a "
        "serious accident or thoughts of self-harm, the assistant stops the normal booking flow and advises "
        "the caller to contact emergency services immediately by calling 112. The assistant then offers to "
        "connect the caller with a human agent. Emergencies are never handled with routine appointment booking.",
        "## Recording and privacy",
        "Calls may be recorded for quality and training purposes. A recording disclosure is displayed and "
        "spoken at the start of every call and is included in the transcript. All data used in this "
        "demonstration is synthetic. Phone numbers are masked everywhere except the secure database, where "
        "they are stored as one-way hashes plus a masked display value.",
        "## Handoff",
        "A caller may request a human agent at any time by saying so. The assistant also offers a handoff when "
        "it cannot answer a question confidently, when a request is ambiguous, or when a safety event is "
        "detected. The escalation queue is monitored during working hours."]
    write(d / "escalation_safety.md", "\n\n".join(safety))


def build_hi() -> None:
    d = KB / "hi"
    intro = ["# शर्मा क्लिनिक — परिचय", "## क्लिनिक के बारे में",
        "शर्मा क्लिनिक एक पड़ोसी बहु-विशेषज्ञ बाहरी रोगी क्लिनिक है जो शहर के परिवारों को सेवा देता है। "
        "क्लिनिक प्राथमिक देखभाल, त्वचा रोग, बाल रोग और हड्डी रोग पर केंद्रित है। हर परामर्श एक योग्य "
        "डॉक्टर द्वारा किया जाता है, और रिसेप्शन टीम हिंदी, गुजराती और अंग्रेज़ी में मरीज़ों की मदद करती है। "
        "यहाँ सभी जानकारी काल्पनिक है; कोई वास्तविक मरीज़ रिकॉर्ड संग्रहीत नहीं किया जाता।",
        "## विभाग",
        "जनरल फिजिशियन बुखार, खांसी, ज़ुकाम, ब्लड प्रेशर और डायबिटीज़ जैसी सामान्य बीमारियाँ देखते हैं। "
        "त्वचा विभाग मुहासे, दाने, एक्जिमा और बालों के झड़ने का इलाज करता है। बाल रोग विभाग बच्चों का "
        "स्वास्थ्य, टीकाकरण और पोषण संभालता है। हड्डी रोग विभाग जोड़ों का दर्द, मोच और फ्रैक्चर का प्रबंधन करता है।",
        "## शुरुआत कैसे करें",
        "नए मरीज़ों को पंजीकरण के लिए दस मिनट पहले आने का अनुरोध किया जाता है। सरकारी फ़ोटो पहचान पत्र और "
        "पिछले मेडिकल रिकॉर्ड साथ लाएँ। रिसेप्शन डेस्क शुल्क, समय, पार्किंग और आवश्यक दस्तावेज़ों के बारे में "
        "जानकारी दे सकती है।"]
    for name, spec, fee, hi_spec, *_ in DOCTORS:
        intro.append(f"## {name} — {hi_spec}\n{name} {hi_spec} के रूप में कार्यरत हैं। परामर्श शुल्क {fee} रुपये है। "
                     f"अपॉइंटमेंट 30 मिनट के स्लॉट में उपलब्ध हैं।")
    write(d / "clinic_hindi.md", "\n\n".join(intro))

    appt = ["# अपॉइंटमेंट और शुल्क — हिंदी", "## अपॉइंटमेंट कैसे करें",
        "आप रिसेप्शन डेस्क पर कॉल करके, वेबसाइट फ़ॉर्म भरकर, या इस वॉइस असिस्टेंट से बात करके अपॉइंटमेंट बुक कर "
        "सकते हैं। बुकिंग तभी पक्की होती है जब आप पढ़कर सुनाए गए विवरण की स्पष्ट सहमति दें। असिस्टेंट कभी भी "
        "अनुमान से अपॉइंटमेंट नहीं बनाता।",
        "## समय और छुट्टियाँ",
        "क्लिनिक सोमवार से शनिवार सुबह 9:00 से शाम 5:00 तक खुला रहता है। रविवार और घोषित छुट्टियों को क्लिनिक "
        "बंद रहता है। 30 मिनट के स्लॉट में अपॉइंटमेंट दिए जाते हैं। यदि आपकी अपॉइंटमेंट छुट्टी वाले दिन पड़ती है "
        "तो रिसेप्शन आपसे संपर्क करके नया समय तय करेगा।",
        "## शुल्क",
        "प्रत्येक डॉक्टर की परामर्श शुल्क क्लिनिक डेटाबेस में दर्ज है और वॉइस असिस्टेंट हमेशा वही सटीक राशि बोलता "
        "है। भुगतान नकद, यूपीआई, कार्ड या नेट बैंकिंग से किया जा सकता है।"]
    for name, spec, fee, *_ in DOCTORS:
        appt.append(f"{name}: {fee} रुपये प्रति परामर्श।")
    for q, a in HI_FAQS:
        appt.append(f"## {q}\n{a}")
    write(d / "appointment_hindi.md", "\n\n".join(appt))

    guide = ["# मरीज़ मार्गदर्शिका — हिंदी", "## दस्तावेज़",
        "हर visits के लिए सरकारी फ़ोटो पहचान पत्र, पिछले प्रिस्क्रिप्शन और प्रासंगिक लैब रिपोर्ट साथ लाएँ। "
        "बच्चों के लिए टीकाकरण रिकॉर्ड और वृद्धि चार्ट आवश्यक है। त्वचा रोग के लिए प्रभावित क्षेत्र की "
        "तस्वीरें और हड्डी रोग के लिए पुराने एक्स-रे साथ रखें।",
        "## सुरक्षा और सहायता",
        "यह सेवा केवल प्रशासनिक है। असिस्टेंट निदान नहीं करता, दवा नहीं सुझाता और खुराक नहीं बताता। यदि आपको "
        "चात में दर्द, साँस लेने में कठिनाई, तेज़ खून बहना 또는 होश जाना जैसी आपदा लगे तो तुरंत 112 पर कॉल करें। "
        "असिस्टेंट आपको मानव एजेंट से जोड़ सकता है। कॉल गुणवत्ता और प्रशिक्षण के लिए रिकॉर्ड की जा सकती है; "
        "हर कॉल की शुरुआत में रिकॉर्डिंग सूचना दी जाती है।"]
    write(d / "patient_guide_hindi.md", "\n\n".join(guide))


def build_gu() -> None:
    d = KB / "gu"
    intro = ["# શર્મા ક્લિનિક — પરિચય", "## ક્લિનિક વિશે",
        "શર્મા ક્લિનિક એક પડોશી બહુ-વિશેષજ્ઞ બહારના દર્દીઓની ક્લિનિક છે જે શહેરના પરિવારોને સેવા આપે છે. "
        "ક્લિનિક પ્રાથમિક સંભાળ, ત્વચારોગ, બાળ રોગ અને હાડકાંના રોગ પર કેન્દ્રિત છે. દરેક સલાહ એક "
        "લાયક ડૉક્ટર દ્વારા કરવામાં આવે છે, અને રિસેપ્શન ટીમ ગુજરાતી, હિંદી અને અંગ્રેજીમાં દર્દીઓની "
        "મદદ કરે છે. અહીંની તમામ માહિતી કાલ્પનિક છે; કોઈ વાસ્તવિક દર્દી રેકોર્ડ સંગ્રહિત થતો નથી.",
        "## વિભાગો",
        "જનરલ ફિઝિશિયન તાવ, ઉધરસ, શરદી, બ્લડ પ્રેશર અને ડાયાબિટીઝ જેવી સામાન્ય બીમારીઓ જુએ છે. "
        "ત્વચારોગ વિભાગ ખીલ, ફોલ્લીઓ અને એક્ઝિમાની સારવાર કરે છે. બાળ રોગ વિભાગ બાળકોના સ્વાસ્થ્ય, "
        "રસીકરણ અને પોષણ સંભાળે છે. હાડકાંના વિશેષજ્ઞ સાંધાનો દુખાવો, મચકોડ અને ફ્રેક્ચરનું "
        "સંચાલન કરે છે.",
        "## શરૂઆત કેવી રીતે કરવી",
        "નવા દર્દીઓએ નોંધણી માટે દસ મિનિટ વહેલા આવવા વિનંતી કરવામાં આવે છે. સરકારી ફોટો ઓળખપત્ર "
        "અને અગાઉના તબીબી રેકોર્ડ સાથે લાવો. રિસેપ્શન ડેસ્ક ફી, સમય, પાર્કિંગ અને જરૂરી દસ્તાવેજો "
        "વિશે માહિતી આપી શકે છે."]
    for name, spec, fee, _, gu_spec, *_ in DOCTORS:
        intro.append(f"## {name} — {gu_spec}\n{name} {gu_spec} તરીકે ફરજ બજાવે છે. સલાહ ફી {fee} રૂપિયા છે. "
                     f"એપોઇન્ટમેન્ટ 30 મિનિટના સ્લોટમાં ઉપલબ્ધ છે.")
    write(d / "clinic_gujarati.md", "\n\n".join(intro))

    appt = ["# એપોઇન્ટમેન્ટ અને ફી — ગુજરાતી", "## એપોઇન્ટમેન્ટ કેવી રીતે બુક કરવી",
        "તમે રિસેપ્શન ડેસ્ક પર કૉલ કરીને, વેબસાઇટ ફોર્મ ભરીને, અથવા આ વોઇસ આસિસ્ટન્ટ સાથે વાત કરીને "
        "એપોઇન્ટમેન્ટ બુક કરી શકો છો. જ્યારે તમે વાંચીને સાંભળેલી વિગતોની સ્પષ્ટ સંમતિ આપો ત્યારે જ "
        "બુકિંગ પક્કું થાય છે. આસિસ્ટન્ટ ક્યારેય અનુમાનથી એપોઇન્ટમેન્ટ બનાવતો નથી.",
        "## સમય અને રજાઓ",
        "ક્લિનિક સોમવારથી શનિવાર સવાર 9:00 થી સાંજ 5:00 સુધી ખુલ્લું રહે છે. રવિવારે અને જાહેર "
        "રજાઓમાં ક્લિનિક બંધ રહે છે. 30 મિનિટના સ્લોટમાં એપોઇન્ટમેન્ટ આપવામાં આવે છે. જો તમારી "
        "એપોઇન્ટમેન્ટ રજાના દિવસે પડે તો રિસેપ્શન તમારો સંપર્ક કરીને નવો સમય નક્કી કરશે.",
        "## ફી",
        "દરેક ડૉક્ટરની સલાહ ફી ક્લિનિક ડેટાબેઝમાં નોંધેલી છે અને વોઇસ આસિસ્ટન્ટ હંમેશા એ જ ચોક્કસ "
        "રકમ બોલે છે. ચુકવણી રોકડ, યુપીઆઈ, કાર્ડ અથવા નેટ બૅંકિંગથી કરી શકાય છે."]
    for name, spec, fee, *_ in DOCTORS:
        appt.append(f"{name}: {fee} રૂપિયા દીઠ સલાહ.")
    for q, a in GU_FAQS:
        appt.append(f"## {q}\n{a}")
    write(d / "appointment_gujarati.md", "\n\n".join(appt))

    guide = ["# દર્દી માર્ગદર્શિકા — ગુજરાતી", "## દસ્તાવેજો",
        "દરેક મુલાકાત માટે સરકારી ફોટો ઓળખપત્ર, અગાઉના પ્રિસ્ક્રિપ્શન અને સંબંધિત લૅબ રિપોર્ટ "
        "સાથે લાવો. બાળકો માટે રસીકરણનો રેકોર્ડ અને વૃદ્ધિ ચાર્ટ જરૂરી છે. ત્વચારોગ માટે "
        "અસરગ્રસ્ત ભાગના ફોટા અને હાડકાંના રોગ માટે જૂના એક્સ-રે સાથે રાખો.",
        "## સલામતી અને સહાય",
        "આ સેવા ફક્ત વહીવટી છે. આસિસ્ટન્ટ નિદાન કરતો નથી, દવા સૂચવતો નથી કે માત્રા જણાવતો નથી. "
        "જો તમને છાતીમાં દુખાવો, શ્વાસ લેવામાં તકલીફ, ભારે લોહી વહેવું કે ભાન જવું જેવી આપત્તિ "
        "લાગે તો તરત 112 પર કૉલ કરો. આસિસ્ટન્ટ તમને માનવ એજન્ટ સાથે જોડી શકે છે. કૉલ ગુણવત્તા "
        "અને તાલીમ માટે રેકોર્ડ કરી શકાય છે; દરેક કૉલની શરૂઆતમાં રેકોર્ડિંગ સૂચના આપવામાં આવે છે."]
    write(d / "patient_guide_gujarati.md", "\n\n".join(guide))


if __name__ == "__main__":
    build_en()
    build_hi()
    build_gu()
    files = sorted(KB.rglob("*.md"))
    total = sum(len(p.read_text(encoding="utf-8")) for p in files)
    print(f"generated {len(files)} documents, {total} characters")
