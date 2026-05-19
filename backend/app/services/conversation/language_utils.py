"""
Detect user/response language style and pick matching TTS voice.
"""

import re

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
LATIN_RE = re.compile(r"[a-zA-Z]")

# Event/brand terms — keep in Latin; use English TTS voice
BRAND_TERMS = (
    "adobe", "roundtable", "pdf", "pune", "pride", "hotel",
    "cmo", "cio", "cto", "gen ai",
)

HINGLISH_MARKERS = (
    "mujhe", "aap", "aapko", "kya", "hai", "hain", "nahi", "nahin",
    "batao", "bataiye", "kaise", "kab", "kahan", "kyun", "ke",
    "ki", "ko", "mein", "main", "yeh", "ye", "woh", "haan", "ji",
    "shukriya", "dhanyawad", "alvida", "subah", "shaam",
)


def detect_language_style(text: str) -> str:
    if not text or not text.strip():
        return "english"

    has_devanagari = bool(DEVANAGARI_RE.search(text))
    lower = text.lower()
    marker_hits = sum(
        1 for word in HINGLISH_MARKERS if re.search(rf"\b{word}\b", lower)
    )

    if has_devanagari and marker_hits == 0:
        ascii_ratio = sum(1 for c in text if c.isascii()) / max(len(text), 1)
        if ascii_ratio < 0.3:
            return "hindi"

    if has_devanagari or marker_hits >= 2:
        return "hinglish"

    if marker_hits == 1:
        return "hinglish"

    return "english"


def language_instruction(style: str) -> str:
    brand_rule = (
        "Always write Adobe, Adobe Exclusive Roundtable, Pune, "
        "and The Pride Hotel in Latin/English letters (never transliterate brands)."
    )
    if style == "hindi":
        return (
            f"{brand_rule} "
            "Reply in Hindi (Devanagari) for general words. "
            "Keep it short (1-3 sentences) for voice."
        )
    if style == "hinglish":
        return (
            f"{brand_rule} "
            "Reply in Hinglish using Latin script only (no Devanagari). "
            "Keep it short (1-3 sentences) for voice."
        )
    return (
        "Reply in clear English only. Do not use Hindi words or Hinglish. "
        "Keep it short (1-3 sentences) for voice."
    )


def contains_brand_terms(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in BRAND_TERMS)


def pick_tts_language(
    user_message: str,
    assistant_text: str,
    stt_language_code: str | None = None,
) -> str:
    """
    Prefer en-IN for clear English brand pronunciation.
    Use hi-IN only for pure Devanagari with no Latin/brand text.
    """
    if LATIN_RE.search(assistant_text) or contains_brand_terms(assistant_text):
        return "en-IN"

    if detect_language_style(user_message) == "english":
        return "en-IN"

    if DEVANAGARI_RE.search(assistant_text):
        return "hi-IN"

    if stt_language_code and stt_language_code.lower().startswith("en"):
        return "en-IN"

    return "en-IN"
