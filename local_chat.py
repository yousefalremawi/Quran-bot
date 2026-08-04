# -*- coding: utf-8 -*-
"""
ردود جاهزة لأنماط المحادثة الشائعة (سلام، شكر، كيفك...) بدون أي AI.
يرجّع dict {"type":"chat","message":...} إذا تعرّف على النمط،
أو None إذا الرسالة مش واضحة وبتحتاج AI فعلياً يفهمها.
"""
import re

from local_parser import _normalize

GREETING_WORDS = [
    "مرحبا", "مرحبتين", "هلا", "هلااا", "اهلا", "أهلا",
    "السلام عليكم", "سلام عليكم", "سلام",
    "صباح الخير", "صباح النور", "مساء الخير", "مساء النور",
]

HOW_ARE_YOU_WORDS = [
    "كيفك", "شلونك", "كيف حالك", "شو اخبارك", "شو أخبارك",
    "عامل ايه", "عامل إيه", "ايش اخبارك",
]

THANKS_WORDS = [
    "شكرا", "شكراً", "يعطيك العافية", "تسلم", "تسلمي",
    "مشكور", "مشكورة", "الله يعطيك العافية", "جزاك الله خير",
]

GOODBYE_WORDS = [
    "باي", "مع السلامة", "الى اللقاء", "إلى اللقاء", "تصبح على خير",
    "تصبحي على خير",
]

REPLIES = {
    "greeting": "وعليكم السلام وأهلاً فيك 🌙 اكتب اسم السورة والآيات يلي بدك تسمعها.",
    "how_are_you": "الحمدلله بخير 🌙 كيف أقدر أساعدك؟ اكتب اسم السورة والآيات يلي بدك تسمعها.",
    "thanks": "الله يبارك فيك 🤍 إذا بدك سورة ثانية، تفضل اكتبها.",
    "goodbye": "مع السلامة 🌙",
}


def _matches_any(text: str, words) -> bool:
    for w in words:
        if _normalize(w) in text:
            return True
    return False


def parse_chat(user_text: str):
    text = _normalize(user_text).strip()
    if not text:
        return None

    if len(text) > 40 or re.search(r"\d", text):
        return None

    if _matches_any(text, HOW_ARE_YOU_WORDS):
        return {"type": "chat", "message": REPLIES["how_are_you"]}

    if _matches_any(text, THANKS_WORDS):
        return {"type": "chat", "message": REPLIES["thanks"]}

    if _matches_any(text, GOODBYE_WORDS):
        return {"type": "chat", "message": REPLIES["goodbye"]}

    if _matches_any(text, GREETING_WORDS):
        return {"type": "chat", "message": REPLIES["greeting"]}

    return None
