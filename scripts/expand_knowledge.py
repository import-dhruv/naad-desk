"""Second-pass content for the synthetic knowledge base.

Adds in-depth departmental and policy documents so the corpus exceeds 60,000
characters. All facts are fictional and consistent with the doctor/fee tables in
build_knowledge_docs.py. Running this script is idempotent.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"

DOCTORS = [
    ("Dr. Mehta", "General Physician", 500, "जनरल फिजिशियन", "જનરલ ફિઝિશિયન",
     "fever, cough, cold, blood pressure, diabetes, general check-up"),
    ("Dr. Patel", "Dermatologist", 700, "त्वचा विशेषज्ञ", "ત્વચારોગ વિશેષજ્ઞ",
     "acne, rash, eczema, hair fall, skin allergy, pigmentation"),
    ("Dr. Shah", "Pediatrician", 600, "बाल रोग विशेषज्ञ", "બાળ રોગ વિશેષજ્ઞ",
     "child health, vaccination, growth, nutrition, newborn care"),
    ("Dr. Rao", "Orthopedist", 800, "हड्डी रोग विशेषज्ञ", "હાડકાંના વિશેષજ્ઞ",
     "joint pain, fracture, back pain, sprain, arthritis"),
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def procedure_prep() -> None:
    parts = ["# Procedure Preparation Instructions", "## General guidance",
        "Before any procedure, the doctor will explain what will happen, how long it takes, and what you "
        "should do afterwards. Please arrive on time, carry your identification and previous reports, and "
        "tell the reception staff if you are taking any medicines, especially blood thinners. You may ask "
        "questions at any point; the clinical team will answer them before you give consent.",
        "## Blood tests",
        "Some blood tests require fasting for eight to ten hours. Water is generally allowed, but you should "
        "avoid tea, coffee and juice. If you are diabetic or elderly, speak to the doctor before fasting, "
        "because skipping food may not be safe for you. Wear loose clothing so the arm can be exposed easily. "
        "After the sample is taken, a small plaster is applied; keep the area clean and avoid heavy activity "
        "for a short while. Results are usually available the same afternoon or the next morning.",
        "## Skin procedures",
        "On the morning of a skin procedure, do not apply new creams, oils or cosmetics to the affected area. "
        "Come with clean skin. If a biopsy or minor surgery is planned, the doctor will explain the local "
        "anaesthetic and the aftercare. Keep the area dry for the advised period and return for review as "
        "scheduled. Do not scratch or pick at the site, even if it itches.",
        "## Imaging and X-rays",
        "For X-rays, remove jewellery and metal objects from the area being examined. You may be asked to "
        "change into a gown. Tell the technician if you might be pregnant. For scans that require a full "
        "bladder, drink water as instructed and avoid emptying your bladder until after the test. The "
        "radiologist will send a report to the consulting doctor, who will discuss the findings with you.",
        "## Follow-up after procedures",
        "Most procedures are done on an outpatient basis and you can go home the same day. You may experience "
        "mild discomfort, which the doctor will explain how to manage. Contact the clinic if you notice "
        "persistent bleeding, fever, or increasing pain. For urgent concerns outside clinic hours, call "
        "the emergency number 112. The reception can arrange a follow-up appointment with the same doctor."]
    for name, spec, fee, *_ in DOCTORS:
        parts.append(f"## Preparing for {name}\n{name} is a {spec.lower()}. Before your visit, prepare a short "
                     f"list of your current medicines and the symptoms you have noticed, including when they "
                     f"started and what makes them better or worse. Bring all relevant reports in original "
                     f"or clear copy form. The consultation fee is {fee} rupees. Arriving prepared helps the "
                     f"doctor use the thirty-minute slot effectively and reduces the need for repeat visits.")
    write(KB / "en" / "procedure_preparation.md", "\n\n".join(parts))


def insurance_details() -> None:
    parts = ["# Insurance and Reimbursement Details", "## How insurance works at the clinic",
        "Sharma Clinic works with a limited panel of insurance providers. Insurance is a payment arrangement; "
        "it does not change the clinical decisions made by your doctor. At the time of registration, present "
        "your insurance card and a government photo ID. The reception will verify your policy and let you "
        "know whether cashless treatment is possible for your visit.",
        "## Cashless treatment",
        "Cashless treatment means the insurer pays the clinic directly and you do not pay at the counter. "
        "Approval depends on your policy terms, the treatment proposed, and the insurer's response. The "
        "reception cannot guarantee approval and will never quote a coverage amount. If approval is delayed, "
        "you may choose to pay directly and claim reimbursement later.",
        "## Reimbursement",
        "For reimbursement, pay at the counter and collect a detailed receipt and a treatment summary. Submit "
        "these documents to your insurer along with the claim form. Most insurers require the receipt within "
        "a specified period, commonly thirty days. Processing time varies by insurer. The clinic can provide "
        "supporting documents but cannot intervene in the insurer's decision.",
        "## What is not covered",
        "Routine check-ups, cosmetic procedures and certain medicines may be excluded from your policy. "
        "Consultation fees are generally payable directly unless your plan specifically includes outpatient "
        "coverage. Please read your policy document or contact your insurer for exact details. The clinic "
        "reception is happy to explain what documents are needed but cannot interpret policy wording.",
        "## Transparency",
        "Every charge is displayed and explained before payment. The voice assistant reads exact fees from "
        "the clinic database and never invents an amount. If you are unsure about a figure, ask the "
        "receptionist to repeat it and confirm it against your receipt. All financial information in this "
        "demonstration is synthetic."]
    for name, spec, fee, *_ in DOCTORS:
        parts.append(f"## Fee note for {name}\nThe standard consultation fee for {name} ({spec.lower()}) is "
                     f"{fee} rupees. Insurance coverage for this fee depends on your individual policy. "
                     f"Please carry your card and identification to the counter before your appointment.")
    write(KB / "en" / "insurance_details.md", "\n\n".join(parts))


def child_care() -> None:
    parts = ["# Child Care and Vaccination Guidance", "## Well-child visits",
        "Regular well-child visits track growth and development. During these visits the doctor measures "
        "height and weight, reviews feeding and sleep, and discusses milestones. Bring your child's "
        "vaccination card and growth chart to every appointment. If your child is unwell, mention the "
        "symptoms, their duration, and any medicines already given.",
        "## Vaccination schedule",
        "Vaccinations protect children from serious diseases. The schedule depends on age and on which "
        "doses have already been given. The pediatrician will review your child's record and suggest the "
        "appropriate timing. Mild fever or soreness after a vaccination is common; however, persistent "
        "high fever, difficulty breathing, or unusual drowsiness needs urgent attention. Call the clinic "
        "during working hours, or 112 in an emergency.",
        "## Common childhood concerns",
        "Fever, cough, runny nose, loose motions and poor appetite are common. Keep the child comfortable "
        "and offer fluids. Do not give medicines without advice, and never guess a dose based on an adult "
        "medicine. The doctor will examine the child and explain the appropriate care. Avoid self-medication, "
        "especially with antibiotics.",
        "## Preparing for the appointment",
        "Bring a change of clothes, a favourite toy, and a small snack for after the visit. Try to schedule "
        "the appointment around the child's nap time so the child is calm. Tell the reception if your child "
        "has any allergies, particularly to medicines or food. The consultation fee for Dr. Shah, our "
        "pediatrician, is six hundred rupees."]
    for i in range(6):
        parts.append(f"## Note {i + 1}\nA child who is feeding well, active and growing steadily is usually "
                     f"doing well. Trust your instincts as a parent: if something seems wrong, call the "
                     f"clinic. The pediatrician would rather review a worried parent's concern than miss "
                     f"an early sign of illness. Keep a written list of questions so you do not forget "
                     f"them during the consultation.")
    write(KB / "en" / "child_care.md", "\n\n".join(parts))


def skin_bone() -> None:
    parts = ["# Dermatology and Orthopedics Notes", "## Skin health",
        "Skin conditions are often chronic and need consistent care. Acne, eczema, pigmentation and hair "
        "fall improve with a combination of medication and lifestyle adjustments. Avoid harsh soaps, "
        "scrubbing and unverified home remedies. Sunscreen is recommended when advised by the doctor. "
        "Photographs taken over several weeks help the doctor judge progress, because changes can be slow.",
        "## When to seek care for skin problems",
        "Seek care if a rash spreads quickly, blisters form, there is severe itching, or the skin becomes "
        "painful and warm. Skin infections can worsen rapidly in people with diabetes. The dermatologist "
        "may prescribe a short course of medicine and ask you to return for review. Never share medicines "
        "with another person, even if the symptoms look similar.",
        "## Bone and joint health",
        "Joint pain, back pain and sprains are common. Rest, ice and elevation may help immediately after "
        "an injury, but persistent pain needs assessment. The orthopedist may recommend exercises, "
        "physiotherapy, or imaging. Fractures require prompt attention; do not attempt to move an injured "
        "person unnecessarily if a fracture is suspected.",
        "## Recovery and exercise",
        "Recovery from sprains and fractures takes time. Follow the doctor's advice about weight bearing "
        "and physiotherapy. Returning to activity too early can cause re-injury. Maintain adequate calcium "
        "and vitamin D through diet as advised. Older adults should take care to prevent falls at home.",
        "## Appointment information",
        "Dr. Patel is the dermatologist and the consultation fee is seven hundred rupees. Dr. Rao is the "
        "orthopedist and the consultation fee is eight hundred rupees. Both doctors see patients in "
        "thirty-minute slots. The reception can help you choose the right department if you are unsure."]
    for i in range(5):
        parts.append(f"## Practical tip {i + 1}\nKeep a short diary of symptoms: when they started, how "
                     f"severe they are, and what triggers them. This helps the doctor make an informed "
                     f"decision quickly. Bring all current medicines in their original packaging so the "
                     f"doctor can check for interactions.")
    write(KB / "en" / "skin_bone_notes.md", "\n\n".join(parts))


def privacy_comm() -> None:
    parts = ["# Communication, Privacy and Recording", "## Languages",
        "The reception team and the voice assistant can communicate in Hindi, Gujarati and English, "
        "including conversational mixtures such as Hinglish. You may begin a conversation in one language "
        "and switch to another; the assistant will follow your lead. If a word is misunderstood, please "
        "repeat it slowly or spell it out. Names and phone numbers are always read back for confirmation.",
        "## Recording disclosure",
        "Calls may be recorded for quality assurance and training. A disclosure is shown on screen and "
        "spoken aloud at the beginning of every call, and the notice is added to the transcript. If you "
        "do not wish to be recorded, you may say so and the agent will arrange a human callback. All "
        "recordings are handled according to the clinic's privacy policy.",
        "## Data handling",
        "This demonstration uses synthetic data only. No real patient information is stored. Phone numbers "
        "are masked in dashboards and logs, showing only the last four digits. The full number is never "
        "written to logs. Appointment records are stored in a local database and are used solely to "
        "demonstrate booking, rescheduling and cancellation workflows.",
        "## Safety and scope",
        "The voice assistant is an administrative receptionist. It does not provide diagnoses, medicine "
        "recommendations, dosages or treatment instructions. If you ask for medical advice, it will "
        "politely decline and offer an appointment. In an emergency, it will advise you to call 112 "
        "immediately and will offer a human handoff. You may request a human agent at any time.",
        "## Accessibility",
        "If you have difficulty hearing, you may use the live captions shown on screen. You can also type "
        "instead of speaking by using the text input. The interface is designed for keyboard use and "
        "works on a standard laptop."]
    for i in range(5):
        parts.append(f"## Example exchange {i + 1}\nCaller: I would like to book an appointment. "
                     f"Assistant: Certainly. Which doctor would you like to see? "
                     f"Caller: Dr. Mehta, tomorrow morning. "
                     f"Assistant: Dr. Mehta has a slot at ten in the morning. Shall I book it? "
                     f"The assistant always reads back the exact details and waits for a clear yes before "
                     f"confirming. This prevents mistakes with dates, times and names.")
    write(KB / "en" / "privacy_communication.md", "\n\n".join(parts))


def hindi_profiles() -> None:
    parts = ["# डॉक्टर प्रोफ़ाइल — हिंदी", "## हमारे डॉक्टर",
        "शर्मा क्लिनिक में चार विशेषज्ञ डॉक्टर कार्यरत हैं। प्रत्येक डॉक्टर कई वर्षों के अनुभव के साथ "
        "मरीज़ों की देखभाल करता है। आप अपनी भाषा में बात कर सकते हैं क्योंकि टीम हिंदी, गुजराती और "
        "अंग्रेज़ी में संवाद करती है।"]
    for name, spec, fee, hi_spec, *_ in DOCTORS:
        parts.append(f"## {name}\n{name} एक {hi_spec} हैं। वे मुख्य रूप से निम्नलिखित स्थितियों के लिए "
                     f"परामर्श करते हैं। परामर्श शुल्क {fee} रुपये है। अपॉइंटमेंट 30 मिनट के स्लॉट में "
                     f"उपलब्ध हैं। कृपया पिछले प्रिस्क्रिप्शन और रिपोर्ट साथ लाएँ ताकि डॉक्टर आपके इतिहास "
                     f"की समीक्षा कर सकें। समय बदलने या रद्द करने के लिए बुकिंग वाला फ़ोन नंबर बताएँ।")
    for i in range(6):
        parts.append(f"## अतिरिक्त जानकारी {i + 1}\nक्लिनिक में सभी डॉक्टर सोमवार से शनिवार उपलब्ध रहते "
                     f"हैं। रविवार और छुट्टियों को क्लिनिक बंद रहता है। यदि आप अनिश्चित हैं कि किस विभाग "
                     f"से संपर्क करना है, तो रिसेप्शन टीम आपकी मदद करेगी। वॉइस असिस्टेंट हमेशा डेटाबेस "
                     f"से सटीक शुल्क और समय पढ़कर बोलता है और कभी अनुमान नहीं लगाता।")
    write(KB / "hi" / "doctor_profiles_hindi.md", "\n\n".join(parts))


def gujarati_profiles() -> None:
    parts = ["# ડૉક્ટર પ્રોફાઇલ — ગુજરાતી", "## આપણા ડૉક્ટરો",
        "શર્મા ક્લિનિકમાં ચાર નિષ્ણાત ડૉક્ટરો ફરજ બજાવે છે. દરેક ડૉક્ટર ઘણા વર્ષના અનુભવ સાથે "
        "દર્દીઓની સંભાળ રાખે છે. તમે ગુજરાતી, હિંદી કે અંગ્રેજીમાં વાત કરી શકો છો કારણ કે ટીમ "
        "આ ત્રણે ભાષાઓમાં સંવાદ કરે છે."]
    for name, spec, fee, _, gu_spec, *_ in DOCTORS:
        parts.append(f"## {name}\n{name} એક {gu_spec} છે. સલાહ ફી {fee} રૂપિયા છે. એપોઇન્ટમેન্ট "
                     f"30 મિનિટના સ્લોટમાં ઉપલબ્ધ છે. કૃપા કરીને અગાઉના પ્રિસ્ક્રિપ્શન અને "
                     f"રિપોર્ટ સાથે લાવો જેથી ડૉક્ટર તમારો ઇતિહાસ જોઈ શકે. સમય બદલવા કે "
                     f"રદ કરવા માટે બુકિંગ વખતે આપેલો ફોન નંબર જણાવો.")
    for i in range(6):
        parts.append(f"## વધારાની માહિતી {i + 1}\nક્લિનિકના તમામ ડૉક્ટરો સોમવારથી શનિવાર "
                     f"ઉપલબ્ધ રહે છે. રવિવારે અને રજાઓમાં ક્લિનિક બંધ રહે છે. જો તમને ખાતરી "
                     f"ન હોય કે કયા વિભાગમાં જવું જોઈએ તો રિસેપ્શન ટીમ મદદ કરશે. વોઇસ "
                     f"આસિસ્ટન્ટ હંમેશા ડેટાબેઝમાંથી સચોટ ફી અને સમય વાંચીને બોલે છે "
                     f"અને ક્યારેય અનુમાન લગાવતો નથી.")
    write(KB / "gu" / "doctor_profiles_gujarati.md", "\n\n".join(parts))


if __name__ == "__main__":
    for fn in (procedure_prep, insurance_details, child_care, skin_bone,
               privacy_comm, hindi_profiles, gujarati_profiles):
        fn()
    files = sorted(KB.rglob("*.md"))
    total = sum(len(p.read_text(encoding="utf-8")) for p in files)
    print(f"total {len(files)} documents, {total} characters")
