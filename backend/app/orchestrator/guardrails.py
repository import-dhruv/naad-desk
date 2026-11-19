"""Safety guardrails: medical advice, emergencies, prompt injection, consent (§9)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

EMERGENCY_PATTERNS = [
    (r"chest pain|chest strain|दर्द.*छाती|छाती.*दर्द|छાતી.*દુખાવો", "chest_pain"),
    (r"can'?t breathe|cannot breathe|difficulty breathing|breathless|साँस.*कठिन|श्वास.*तकलीफ|શ્વાસ.*તકલીફ", "breathing"),
    (r"severe bleeding|lots of blood|खून.*बह|ભારે.*લોહી", "bleeding"),
    (r"unconscious|passed out|कोमा|बेहोश|ભાન.*જવું", "unconscious"),
    (r"serious accident|major accident|गंभीर.*दुर्घटना|ગંભીર.*અકસ્માત", "accident"),
    (r"suicid|self.?harm|आत्महत्या|આત્મહત્યા", "self_harm"),
    (r"stroke|heart attack|हार्ट अटैक|ха ttack|બુધ", "critical"),
]

MEDICAL_REQUEST_PATTERNS = [
    r"medicine|medication|tablet|dose|dosage|prescription|antibiotic|injection",
    r"दवा|गोली|खुराक|नुस्खा|एंटीबायॉटिक",
    r"દવા|ગોળી|માત્રા|પ્રિસ્ક્રિપ્શન",
    r"diagnos|what disease|what illness|निदान|क्या बीमारी|નિદાન",
]

INJECTION_PATTERNS = [
    r"ignore (all |the )?(previous|prior|above|system|earlier) (instructions|prompt|rules)",
    r"forget (your|the|all) (instructions|rules|prompt)",
    r"you are now|act as|pretend to be|new instructions|system prompt",
    r"reveal (your|the) (system|instructions|prompt|api|key|secret)",
    r"print (your|the) (system|instructions|prompt)",
    r"disregard|override (your|the) (rules|instructions)",
    r"ignore.*सistema|अपने निर्देश भूल|तमારા સૂચના ભૂલી",
    r"api key|secret key|password|token.*show|output.*key",
    r"do not follow|don't follow|निर्देश.*न मान",
    r"jailbreak|developer mode|admin mode|sudo mode",
]

DISCLOSURE_TEXT = {
    "hi": "यह कॉल गुणवत्ता और प्रशिक्षण के लिए रिकॉर्ड की जा सकती है।",
    "gu": "આ કૉલ ગુણવત્તા અને તાલીમ માટે રેકોર્ડ કરી શકાય છે.",
    "en-in": "This call may be recorded for quality and training purposes.",
}


@dataclass
class GuardrailResult:
    action: str  # allow | refuse_medical | emergency | injection_blocked | handoff
    reason: str = ""
    spoken: str = ""


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").lower()


def check_emergency(text: str) -> str | None:
    t = _norm(text)
    for pattern, label in EMERGENCY_PATTERNS:
        if re.search(pattern, t):
            return label
    return None


def check_medical_request(text: str) -> bool:
    t = _norm(text)
    return any(re.search(p, t) for p in MEDICAL_REQUEST_PATTERNS)


def check_injection(text: str) -> bool:
    """Treat caller speech and retrieved documents as untrusted data."""
    t = _norm(text)
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


def emergency_spoken(language: str) -> str:
    if language == "gu":
        return ("આ એક આપત્તિ છે. કૃપા કરીને તરત 112 પર કૉલ કરો. "
                "હું તમને માનવ એજન્ટ સાથે પણ જોડી શકું છું.")
    if language == "hi":
        return "यह आपदा है। कृपया तुरंत 112 पर कॉल करें। मैं आपको मानव एजेंट से भी जोड़ सकता हूँ।"
    return "This sounds like an emergency. Please call 112 immediately. I can also connect you with a human agent."


def medical_refusal_spoken(language: str) -> str:
    if language == "gu":
        return ("હું દવા કે સારવારની સલાહ આપી શકતો નથી. કૃપા કરીને ડૉક્ટર સાથે મુલાકાત લો; "
                "હું તમારા માટે એપોઇન્ટમેન્ટ બુક કરી શકું છું.")
    if language == "hi":
        return "मैं दवा या इलाज की सलाह नहीं दे सकता। कृपया डॉक्टर से मिलें; मैं आपका अपॉइंटमेंट बुक कर सकता हूँ।"
    return "I can't give medical advice. Please speak with a doctor; I can book an appointment for you."


def guard(text: str, language: str = "hi", source: str = "caller") -> GuardrailResult:
    """Run all guardrails. Caller input and retrieved text both go through this."""
    emergency = check_emergency(text)
    if emergency and source == "caller":
        return GuardrailResult("emergency", emergency, emergency_spoken(language))
    if check_injection(text):
        # Never execute instructions embedded in retrieved documents.
        return GuardrailResult("injection_blocked", "untrusted instruction detected")
    if check_medical_request(text) and source == "caller":
        return GuardrailResult("refuse_medical", "medical advice out of scope",
                               medical_refusal_spoken(language))
    return GuardrailResult("allow")


def disclosure(language: str) -> str:
    return DISCLOSURE_TEXT.get(language, DISCLOSURE_TEXT["en-in"])
