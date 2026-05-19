"""
Intent detection module.
"""

from typing import Optional

import re

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


class IntentDetector:
    INTERESTED_KEYWORDS = [
        "interested",
        "sounds good",
        "i will attend",
        "register me",
        "count me in",
        "yes i want to join",
        "haan interested hoon",
        "mujhe attend karna hai",
    ]

    END_CONVERSATION_KEYWORDS_ROMAN = [
        "bye",
        "goodbye",
        "thank you",
        "thanks",
        "see you",
        "end call",
        "stop conversation",
        "talk later",
        "bye bye",
        "dhanyawad",
        "dhanyavaad",
        "shukriya",
        "alvida",
        "theek hai bye",
        "chalo bye",
        "ok bye",
        "okay bye",
    ]

    # Devanagari goodbye (checked on original text, not lowercased)
    END_CONVERSATION_KEYWORDS_DEVANAGARI = [
        "बाय",
        "बाइ",
        "अलविदा",
        "धन्यवाद",
        "शुक्रिया",
        "फिर मिलते",
    ]

    MAYBE_KEYWORDS = [
        "maybe",
        "not sure",
        "will think",
        "possibly",
        "dekhta hoon",
        "shayad",
        "later",
    ]

    NOT_INTERESTED_KEYWORDS = [
        "not interested",
        "no thanks",
        "don't call",
        "not attending",
        "skip",
        "nahi interested",
        "mujhe nahi aana",
    ]

    @staticmethod
    def _is_goodbye_message(message: str) -> bool:
        lower = message.lower().strip()

        for keyword in IntentDetector.END_CONVERSATION_KEYWORDS_ROMAN:
            if keyword in lower:
                return True

        for keyword in IntentDetector.END_CONVERSATION_KEYWORDS_DEVANAGARI:
            if keyword in message:
                return True

        # "ठीक है, चलो बाय" — बाय with optional punctuation
        if DEVANAGARI_RE.search(message) and re.search(r"बाय", message):
            return True

        return False

    @staticmethod
    def detect_intent(user_message: str) -> Optional[str]:
        message = user_message.strip()
        if not message:
            return None

        lower = message.lower()

        for keyword in IntentDetector.INTERESTED_KEYWORDS:
            if keyword in lower:
                return "Interested"

        for keyword in IntentDetector.MAYBE_KEYWORDS:
            if keyword in lower:
                return "Maybe"

        for keyword in IntentDetector.NOT_INTERESTED_KEYWORDS:
            if keyword in lower:
                return "Not Interested"

        if IntentDetector._is_goodbye_message(message):
            return "End Conversation"

        return None
