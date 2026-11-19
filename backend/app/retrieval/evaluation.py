"""40-question retrieval evaluation set (30 answerable / 10 unanswerable) and
groundedness metrics (§7.3–7.4)."""
from __future__ import annotations

from dataclasses import dataclass

from .hybrid import HybridRetriever

QUESTIONS: list[dict] = [
    # 30 answerable
    {"id": "Q01", "question": "What time does the clinic open?", "answerable": True, "keywords": ["9:00", "सुबह", "9"], "language": "en"},
    {"id": "Q02", "question": "Is the clinic open on Sunday?", "answerable": True, "keywords": ["रविवार", "Sunday", "बंद"], "language": "en"},
    {"id": "Q03", "question": "What is Dr. Mehta's consultation fee?", "answerable": True, "keywords": ["500", "शुल्क", "fee"], "language": "en"},
    {"id": "Q04", "question": "How much does Dr. Patel charge?", "answerable": True, "keywords": ["700", "शुल्क"], "language": "en"},
    {"id": "Q05", "question": "Which doctor treats skin problems?", "answerable": True, "keywords": ["Patel", "त्वचा", "dermatologist"], "language": "en"},
    {"id": "Q06", "question": "Who is the pediatrician?", "answerable": True, "keywords": ["Shah", "बाल", "pediatric"], "language": "en"},
    {"id": "Q07", "question": "What payment methods are accepted?", "answerable": True, "keywords": ["UPI", "cash", "card"], "language": "en"},
    {"id": "Q08", "question": "Do you accept insurance?", "answerable": True, "keywords": ["insurance", "बीमा", "वीमો"], "language": "en"},
    {"id": "Q09", "question": "What documents should I bring?", "answerable": True, "keywords": ["ID", "दस्तावेज़", "дар"], "language": "en"},
    {"id": "Q10", "question": "Where is the clinic located?", "answerable": True, "keywords": ["bus stand", "बस", "पार्क"], "language": "en"},
    {"id": "Q11", "question": "Is there parking available?", "answerable": True, "keywords": ["parking", "पार्किंग"], "language": "en"},
    {"id": "Q12", "question": "What is the cancellation policy?", "answerable": True, "keywords": ["four hours", "चार घंटे", "रद्द"], "language": "en"},
    {"id": "Q13", "question": "Can I reschedule my appointment?", "answerable": True, "keywords": ["reschedule", "बदल", "चार घंटे"], "language": "en"},
    {"id": "Q14", "question": "What should I do before a blood test?", "answerable": True, "keywords": ["fasting", "उपवास", "8"], "language": "en"},
    {"id": "Q15", "question": "How do I request a human agent?", "answerable": True, "keywords": ["human", "मानव", "handoff"], "language": "en"},
    {"id": "Q16", "question": "What should I do in an emergency?", "answerable": True, "keywords": ["112", "emergency", "आपदा"], "language": "en"},
    {"id": "Q17", "question": "Does the assistant give medical advice?", "answerable": True, "keywords": ["diagnos", "निदान", "दवा"], "language": "en"},
    {"id": "Q18", "question": "When is the second Saturday holiday?", "answerable": True, "keywords": ["second Saturday", "शनिवार", "रजा"], "language": "en"},
    {"id": "Q19", "question": "How long is a consultation slot?", "answerable": True, "keywords": ["30", "minutes", "मिनट"], "language": "en"},
    {"id": "Q20", "question": "Which doctor treats joint pain?", "answerable": True, "keywords": ["Rao", "जोड़", "orthopedic"], "language": "en"},
    {"id": "Q21", "question": "क्लिनिक का समय क्या है?", "answerable": True, "keywords": ["9:00", "सुबह", "शाम"], "language": "hi"},
    {"id": "Q22", "question": "क्या क्लिनिक रविवार को खुला है?", "answerable": True, "keywords": ["रविवार", "बंद"], "language": "hi"},
    {"id": "Q23", "question": "डॉक्टर मेहता की फी कितनी है?", "answerable": True, "keywords": ["500", "शुल्क", "रुपये"], "language": "hi"},
    {"id": "Q24", "question": "भुगतान के कौन-कौन से तरीके हैं?", "answerable": True, "keywords": ["यूपीआई", "नकद", "कार्ड"], "language": "hi"},
    {"id": "Q25", "question": "अपॉइंटमेंट कैसे रद्द करूँ?", "answerable": True, "keywords": ["चार घंटे", "रद्द", "फ़ोन"], "language": "hi"},
    {"id": "Q26", "question": "बच्चे के लिए कौन-से दस्तावेज़ चाहिए?", "answerable": True, "keywords": ["टीकाकरण", "वैक्सीन", "रिकॉर्ड"], "language": "hi"},
    {"id": "Q27", "question": "શું આજે ક્લિનિક ખુલ્લું છે?", "answerable": True, "keywords": ["સવાર", "શનિવાર"], "language": "gu"},
    {"id": "Q28", "question": "ક્લિનિક ક્યાં આવેલું છે?", "answerable": True, "keywords": ["બસ", "સ્ટેન્ડ", "પાર્ક"], "language": "gu"},
    {"id": "Q29", "question": "ડૉક્ટર પટેલની ફી કેટલી છે?", "answerable": True, "keywords": ["700", "રૂપિયા", "ફી"], "language": "gu"},
    {"id": "Q30", "question": "kya kal appointment available hai?", "answerable": True, "keywords": ["उपलब्ध", "समय", "कल"], "language": "hinglish"},
    # 10 unanswerable
    {"id": "Q31", "question": "What is the clinic's URL?", "answerable": False, "keywords": [], "language": "en"},
    {"id": "Q32", "question": "Who is the clinic's chief financial officer?", "answerable": False, "keywords": [], "language": "en"},
    {"id": "Q33", "question": "What is the doctor's personal mobile number?", "answerable": False, "keywords": [], "language": "en"},
    {"id": "Q34", "question": "What is the clinic's registered company number?", "answerable": False, "keywords": [], "language": "en"},
    {"id": "Q35", "question": "What is today's stock price of the clinic?", "answerable": False, "keywords": [], "language": "en"},
    {"id": "Q36", "question": "क्लिनिक का आईएसओ कोड क्या है?", "answerable": False, "keywords": [], "language": "hi"},
    {"id": "Q37", "question": "डॉक्टर का घर का पता क्या है?", "answerable": False, "keywords": [], "language": "hi"},
    {"id": "Q38", "question": "ક્લિનિકનો ફેક્સ નંબર શું છે?", "answerable": False, "keywords": [], "language": "gu"},
    {"id": "Q39", "question": "ક્લિનિકનો ISO કોડ શું છે?", "answerable": False, "keywords": [], "language": "gu"},
    {"id": "Q40", "question": "clinic ka license number kya hai?", "answerable": False, "keywords": [], "language": "hinglish"},
]


@dataclass
class RetrievalMetrics:
    recall_at_4: float
    groundedness: float
    unanswerable_rejection: float
    hinglish_recall_delta: float
    details: list[dict]


def _hit(result, keywords: list[str]) -> bool:
    blob = " ".join(c.content for c in result.chunks).lower()
    return any(k.lower() in blob for k in keywords) if keywords else False


def evaluate(retriever: HybridRetriever, hinglish: bool = True,
             min_confidence: float = 0.50) -> RetrievalMetrics:
    answerable = [q for q in QUESTIONS if q["answerable"]]
    unanswerable = [q for q in QUESTIONS if not q["answerable"]]
    details: list[dict] = []
    hits = 0
    grounded = 0
    for q in answerable:
        r = retriever.query(q["question"], top_k=4, min_confidence=min_confidence, hinglish=hinglish)
        kw_hit = any(k.lower() in " ".join(c.content for c in r.chunks).lower()
                     for k in q["keywords"])
        hits += int(kw_hit)
        grounded += int(r.grounded)
        details.append({"id": q["id"], "hit": kw_hit, "grounded": r.grounded,
                        "confidence": r.confidence, "chunk_ids": [c.chunk_id for c in r.chunks]})
    rejected = 0
    for q in unanswerable:
        r = retriever.query(q["question"], top_k=4, min_confidence=min_confidence, hinglish=hinglish)
        rejected += int(not r.grounded)
        details.append({"id": q["id"], "hit": None, "grounded": r.grounded,
                        "confidence": r.confidence, "chunk_ids": [c.chunk_id for c in r.chunks]})

    # Ablation: measure the effect of Hinglish normalisation on keyword recall.
    base_hits = 0
    for q in answerable:
        r = retriever.query(q["question"], top_k=4, min_confidence=min_confidence, hinglish=False)
        base_hits += int(any(k.lower() in " ".join(c.content for c in r.chunks).lower()
                             for k in q["keywords"]))

    n = len(answerable)
    return RetrievalMetrics(
        recall_at_4=round(hits / n, 4),
        groundedness=round(grounded / n, 4),
        unanswerable_rejection=round(rejected / len(unanswerable), 4),
        hinglish_recall_delta=round((hits - base_hits) / n, 4),
        details=details,
    )
