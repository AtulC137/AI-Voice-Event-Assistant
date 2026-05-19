"""
Event responder using lightweight NLP
(TF-IDF + cosine similarity)

No LLM. Very low latency. No training step required.

Fixes applied:
- Massively expanded intent examples to cover natural phrasing
- "tell me about timing" → TIME (not DESCRIPTION)
- "what time", "kitne baje", "kab shuru" all → TIME
- Confidence threshold raised to 0.15 with smarter fallback
- Added synonym expansion for common words
"""

import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------
# Event knowledge
# ---------------------------------------------------

EVENT_DATE        = "8th May 2026"
EVENT_TIME        = "10:00 AM onwards"
EVENT_VENUE       = "The Pride Hotel, Shivajinagar, Pune"
EVENT_CONTACT     = "+91 9850362300"

EVENT_DESCRIPTION = (
    "Yeh Adobe ka exclusive roundtable event hai "
    "senior business aur technology leaders ke liye. "
    "Ismein networking aur lunch bhi included hai."
)

EVENT_TOPICS = (
    "Event mein PDF innovation, Gen AI, "
    "future workflows aur collaboration discuss hoga."
)

FALLBACK_RESPONSE = (
    "Maaf kijiye, main samajh nahi paya. "
    "Kya aap thoda aur detail mein pooch sakte hain? "
    "Aap event ka time, venue, date, ya topics ke baare mein pooch sakte hain."
)

FAREWELL_RESPONSE = (
    "Shukriya. Aapse baat karke accha laga. "
    "Have a great day."
)

ACK_RESPONSES = [
    "Ji aur bataiye.",
    "Aur kya jaana chahenge?",
    "Ji main sun raha hoon.",
    "Bilkul, aur koi sawaal?"
]


# ---------------------------------------------------
# Intent examples
# KEY FIX: Separate TIME from DESCRIPTION clearly.
# "tell me about timing" has both "tell me" and "timing"
# so we must have many TIME examples with "tell me" pattern.
# ---------------------------------------------------

INTENTS = {

    "TIME": {
        "examples": [
            # Direct time questions
            "what time does event start",
            "what time is the event",
            "what is the timing",
            "event timing",
            "event start time",
            "timing of event",
            "what time event",
            "time of event",
            "event time",
            "start time",
            "when does event start",
            "when will event begin",
            "when does it start",
            "when is the event starting",
            "at what time",
            "what time should i come",
            "what time to arrive",
            "morning or evening",
            # "tell me about X" patterns for TIME
            "tell me about the timing",
            "tell me the timing",
            "tell me about time",
            "can you tell me about timing",
            "can you tell me the timing",
            "can you tell me what time",
            "tell me when event starts",
            "i want to know the timing",
            "i want to know the time",
            "what is the event timing",
            "what is the start time",
            "what is the schedule time",
            # Hindi / Hinglish
            "event kab hai",
            "event kab shuru hoga",
            "kab shuru hoga",
            "kitne baje hai",
            "kitne baje shuru hoga",
            "kitne baje ka event hai",
            "timing kya hai",
            "time kya hai",
            "event ka time batao",
            "event ka time kya hai",
            "शुरू कब होगा",
            "इवेंट कितने बजे है",
            "टाइम क्या है",
            "कितने बजे",
            "कब शुरू होगा",
            "event kitne baje se hai",
            "kya time hai event ka",
        ],
        "response": f"Event {EVENT_TIME} se shuru hoga, {EVENT_DATE} ko."
    },

    "DATE": {
        "examples": [
            # Direct date questions
            "what is the date",
            "event date",
            "when is the event",
            "which date is event",
            "what date is event",
            "event kab hai date",
            "date of event",
            "event schedule date",
            "which day is event",
            "what day is the event",
            "on which date",
            "tell me the date",
            "tell me about date",
            "can you tell me the date",
            "what is event date",
            "event ka date kya hai",
            # Hindi / Hinglish
            "इवेंट कब है",
            "date kya hai",
            "kab hai event",
            "event ka din kya hai",
            "कौन सी तारीख",
            "तारीख क्या है",
            "event ki date batao",
            "may mein kab hai",
        ],
        "response": f"Event {EVENT_DATE} ko hai, {EVENT_TIME} se."
    },

    "VENUE": {
        "examples": [
            # Direct venue questions
            "where is the event",
            "event venue",
            "event location",
            "where will event be held",
            "where is event held",
            "event address",
            "what is the venue",
            "event ka venue kya hai",
            "which hotel",
            "which place",
            "where should i go",
            "where to come",
            "event kahan hoga",
            "event kahan hai",
            "location kya hai",
            "address kya hai",
            "tell me the venue",
            "tell me the location",
            "tell me about venue",
            "can you tell me the venue",
            "can you tell me where",
            "i want to know the venue",
            "what is the address",
            # Hindi / Hinglish
            "इवेंट कहाँ है",
            "kahan hai",
            "jagah kya hai",
            "कहाँ है",
            "venue batao",
            "location batao",
            "hotel kahan hai",
            "pune mein kahan hai",
        ],
        "response": f"Event {EVENT_VENUE} mein hoga."
    },

    "DESCRIPTION": {
        "examples": [
            # Questions about what the event IS — not when/where
            "tell me about the event",
            "describe the event",
            "what is this event",
            "event overview",
            "what kind of event is this",
            "what type of event",
            "what is the event about",
            "can you describe the event",
            "give me details about event",
            "more about event",
            "event details",
            "about the event",
            "what is happening",
            "event kya hai",
            "yeh kya event hai",
            "event ke baare mein batao",
            "event ki jankari do",
            "event kaise hoga",
            "kaisa event hai",
            # Hindi
            "इवेंट के बारे में बताओ",
            "क्या है यह इवेंट",
            "इवेंट क्या है",
            "बताइए इस इवेंट के बारे में",
            "event ka overview kya hai",
            "event mein kya hoga",
            "event kaisa hoga",
        ],
        "response": EVENT_DESCRIPTION
    },

    "TOPICS": {
        "examples": [
            "agenda",
            "topics",
            "what topics will be covered",
            "what will be discussed",
            "discussion topics",
            "event agenda",
            "what will happen in event",
            "what is on the agenda",
            "what subjects",
            "what themes",
            "session topics",
            "what are the sessions",
            "tell me about agenda",
            "tell me the agenda",
            "what will they talk about",
            "kya discuss hoga",
            "kya hoga event mein",
            "agenda kya hai",
            "topics kya hai",
            "kya seekhne milega",
            "sessions kya hai",
            # Hindi
            "इवेंट में क्या होगा",
            "एजेंडा क्या है",
            "क्या सीखने मिलेगा",
            "event ka agenda batao",
            "kis cheez par discussion hogi",
        ],
        "response": EVENT_TOPICS
    },

    "CONTACT": {
        "examples": [
            "contact number",
            "phone number",
            "helpline",
            "who to contact",
            "contact details",
            "contact information",
            "how to contact",
            "support number",
            "call number",
            "reach out to",
            "contact kaise karein",
            "number kya hai",
            "phone kya hai",
            "kisko call karein",
            "helpline number",
            # Hindi
            "नंबर क्या है",
            "संपर्क कैसे करें",
            "contact ka number batao",
            "kise contact karein",
        ],
        "response": f"Aap {EVENT_CONTACT} par contact kar sakte hain."
    },

    "REGISTRATION": {
        "examples": [
            "how to register",
            "registration process",
            "how do i join",
            "how to attend",
            "can i register",
            "register for event",
            "sign up",
            "book seat",
            "how to book",
            "i want to attend",
            "register me",
            "count me in",
            "i will attend",
            "interested to join",
            "kaise register karein",
            "register kaise karein",
            "attend kaise karein",
            "mujhe attend karna hai",
            "mera naam register karo",
            # Hindi
            "रजिस्टर कैसे करें",
            "कैसे जुड़ें",
            "event mein kaise aayein",
        ],
        "response": (
            f"Registration ke liye aap {EVENT_CONTACT} par "
            "contact kar sakte hain. Humari team aapki madad karegi."
        )
    },

    "NETWORKING": {
        "examples": [
            "networking",
            "will there be networking",
            "lunch included",
            "is lunch provided",
            "food",
            "meals",
            "networking opportunity",
            "meet people",
            "networking event",
            "lunch kya hai",
            "khana milega",
            "lunch milega kya",
            "networking hoga kya",
        ],
        "response": (
            "Haan, event mein networking aur lunch dono included hain. "
            "Aap senior business aur technology leaders se mil sakte hain."
        )
    },

    "ORGANIZER": {
        "examples": [
            "who is organizing",
            "who organized this event",
            "organizer",
            "who is behind this event",
            "which company event",
            "adobe event",
            "kisne organize kiya",
            "kaun organize kar raha hai",
            "event organizer kaun hai",
        ],
        "response": (
            "Yeh event Adobe ne organize kiya hai — "
            "senior business aur technology leaders ke liye ek exclusive roundtable."
        )
    }
}


FAREWELL_WORDS = [
    "bye",
    "goodbye",
    "thank you",
    "thanks",
    "see you",
    "alvida",
    "shukriya",
    "dhanyawad",
    "theek hai bye",
    "theek hai alvida",
    "ok bye",
    "okay bye",
    "baad mein baat karte hain",
    # Hindi script — punctuation stripped before matching
    "बाय",           # "ठीक है, बाय।" → stripped → "ठीक है बाय" → matches
    "शुक्रिया",
    "धन्यवाद",
    "अलविदा",
    "बाय बाय",
    "फिर मिलेंगे",
]

ACK_WORDS = [
    "ok",
    "okay",
    "hmm",
    "haan",
    "ठीक है",
    "theek hai",
    "achha",
    "alright",
    "got it",
    "understood",
    "samajh gaya",
]


# ---------------------------------------------------
# Build TF-IDF vectors once at import time
# ---------------------------------------------------

training_text   = []
training_labels = []

for label, data in INTENTS.items():
    for example in data["examples"]:
        training_text.append(example)
        training_labels.append(label)

# ngram_range (1,2) captures bigrams like "event timing", "start time"
# This greatly improves matching for multi-word queries
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=1,
    analyzer="word"
)

X = vectorizer.fit_transform(training_text)


# ---------------------------------------------------
# Keyword overrides for high-confidence cases
# These run BEFORE TF-IDF to catch clear matches instantly
# ---------------------------------------------------

KEYWORD_OVERRIDES = {
    "TIME": [
        "timing", "time", "baje", "kitne baje", "kab shuru",
        "start time", "shuru", "schedule", "टाइम", "कितने बजे",
        "समय", "टाइमिंग", "वक्त", "बजे",
    ],
    "DATE": [
        "date", "din", "tarikh", "तारीख", "कौन सी तारीख",
        "which date", "what date", "डेट", "तिथि",
    ],
    "VENUE": [
        "venue", "location", "address", "kahan", "where",
        "कहाँ", "jagah", "hotel", "place",
        "वेन्यू", "लोकेशन", "जगह", "पता", "कहां",
    ],
    "CONTACT": [
        "contact", "phone", "number", "call", "helpline",
        "नंबर", "संपर्क", "फोन", "कॉल",
    ],
    "REGISTRATION": [
        "register", "registration", "sign up", "book", "attend",
        "join", "रजिस्टर",
    ],
}

# Words that should BLOCK a TIME override (to avoid false positives)
TIME_BLOCKLIST = [
    "about event", "describe", "overview", "what is event",
    "event hai", "kaisa", "kya hai event"
]


def keyword_override(text: str):
    """
    Fast pre-check before TF-IDF.
    Returns intent label string if a keyword match is found, else None.
    Priority: TIME > DATE > VENUE > CONTACT > REGISTRATION
    TIME check has extra blocklist guard.
    """
    lower = text.lower()

    # TIME — but block if it looks like a description question
    for block in TIME_BLOCKLIST:
        if block in lower:
            break
    else:
        for kw in KEYWORD_OVERRIDES["TIME"]:
            if kw in lower:
                return "TIME"

    for kw in KEYWORD_OVERRIDES["DATE"]:
        if kw in lower:
            return "DATE"

    for kw in KEYWORD_OVERRIDES["VENUE"]:
        if kw in lower:
            return "VENUE"

    for kw in KEYWORD_OVERRIDES["CONTACT"]:
        if kw in lower:
            return "CONTACT"

    for kw in KEYWORD_OVERRIDES["REGISTRATION"]:
        if kw in lower:
            return "REGISTRATION"

    return None


# ---------------------------------------------------
# Responder
# ---------------------------------------------------

class EventResponder:

    @staticmethod
    def get_best_match(user_message: str) -> dict:

        # Strip punctuation before any matching
        # "ठीक है, बाय।" → "ठीक है बाय"
        # "bye!" → "bye"
        import re
        text = re.sub(r"[।,\.!?;:।\-]", " ", user_message.lower()).strip()
        text = re.sub(r"\s+", " ", text).strip()

        # ── Farewell check FIRST (before ACK) ───────────────────
        # Must be before ACK because "ठीक है, बाय।" contains both
        # an ACK word ("ठीक है") AND a farewell word ("बाय").
        # Farewell is terminal — it takes priority.
        for word in FAREWELL_WORDS:
            if word in text:
                return {
                    "label":       "FAREWELL",
                    "response":    FAREWELL_RESPONSE,
                    "is_farewell": True
                }

        # ── ACK check ───────────────────────────────────────────
        if text in ACK_WORDS:
            return {
                "label":       "ACK",
                "response":    random.choice(ACK_RESPONSES),
                "is_farewell": False
            }

        # ── Keyword override (instant, before TF-IDF) ────────────
        override_label = keyword_override(text)   # text already cleaned above
        if override_label:
            return {
                "label":       override_label,
                "response":    INTENTS[override_label]["response"],
                "is_farewell": False
            }

        # ── TF-IDF cosine similarity ─────────────────────────────
        query        = vectorizer.transform([text])
        similarities = cosine_similarity(query, X)[0]
        best_index   = similarities.argmax()
        confidence   = similarities[best_index]

        print(
            f"[NLP] query='{text}' "
            f"best='{training_labels[best_index]}' "
            f"confidence={confidence:.3f}",
            flush=True
        )

        if confidence < 0.15:
            return {
                "label":       "FALLBACK",
                "response":    FALLBACK_RESPONSE,
                "is_farewell": False
            }

        intent = training_labels[best_index]

        return {
            "label":       intent,
            "response":    INTENTS[intent]["response"],
            "is_farewell": False
        }

    @staticmethod
    def get_response(user_message: str) -> str:
        return EventResponder.get_best_match(user_message)["response"]

    @staticmethod
    def is_farewell(user_message: str) -> bool:
        return EventResponder.get_best_match(user_message)["is_farewell"]