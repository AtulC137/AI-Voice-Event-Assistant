"""
Fixed welcome and goodbye lines for voice playback.
"""


def normalize_language_code(language_code: str | None) -> str:
    if not language_code:
        return "en-IN"
    code = language_code.lower()
    if code.startswith("hi"):
        return "hi-IN"
    return "en-IN"


def welcome_message(language_code: str = "en-IN") -> str:
    return (
        "Hello! I am your AI assistant for the Adobe Exclusive Roundtable. "
        "How can I help you today?"
    )


def goodbye_message(language_code: str = "en-IN") -> str:
    # Hinglish in Latin script + en-IN TTS for clear pronunciation
    return (
        "Thank you! It was nice talking with you. Have a great day."
    )
