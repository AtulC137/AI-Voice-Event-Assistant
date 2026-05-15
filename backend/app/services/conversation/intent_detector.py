"""
Intent detection module.

Responsible for:
- detecting user interest level
- classifying lead intent
"""

from typing import Optional


class IntentDetector:
    """
    Detects conversation intent from user messages.
    """

    INTERESTED_KEYWORDS = [
        "interested",
        "sounds good",
        "i will attend",
        "register me",
        "count me in",
        "yes i want to join",
        "haan interested hoon",
        "mujhe attend karna hai"
    ]

    MAYBE_KEYWORDS = [
        "maybe",
        "not sure",
        "will think",
        "possibly",
        "dekhta hoon",
        "shayad",
        "later"
    ]

    NOT_INTERESTED_KEYWORDS = [
        "not interested",
        "no thanks",
        "don't call",
        "not attending",
        "skip",
        "nahi interested",
        "mujhe nahi aana"
    ]

    @staticmethod
    def detect_intent(
        user_message: str
    ) -> Optional[str]:
        """
        Detect user intent from message text.
        """

        message = user_message.lower()

        for keyword in IntentDetector.INTERESTED_KEYWORDS:

            if keyword in message:
                return "Interested"

        for keyword in IntentDetector.MAYBE_KEYWORDS:

            if keyword in message:
                return "Maybe"

        for keyword in IntentDetector.NOT_INTERESTED_KEYWORDS:

            if keyword in message:
                return "Not Interested"

        return None