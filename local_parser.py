# -*- coding: utf-8 -*-
"""
محلل محلي (بدون AI) يفهم أغلب صيغ الطلبات الشائعة مباشرة:
- "سورة البقرة من 90 لـ 95"
- "البقرة ٩٠-٩٥"
- "بدي أول خمس آيات من الكهف"
- "آخر عشر آيات من سورة الكهف"
- "الآية الخامسة من الكهف" / "آية 5 من الكهف"
- "سورة يس" (بدون أرقام = السورة كاملة)

الهدف: تغطية أغلب الرسائل بدون استهلاك كوتا الـ AI المحدودة، وترك حالات
الغموض الحقيقية فقط لـ ai_brain.analyze_message كـ fallback.

يرجّع dict بنفس شكل ai_brain عند النجاح، أو None إذا ما قدر يفهم الرسالة
بثقة كافية (وعندها لازم المتصل يستخدم الـ AI كـ fallback).
"""
import re

from surahs import NAME_TO_SURAH, NUM_TO_COUNT

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_DIGIT_TABLE = str.maketrans(ARABIC_DIGITS, "0123456789")

# كلمات الأعداد العربية الشائعة بالطلبات (اسم وأول/آخر آيات)
def _normalize(text: str) -> str:
    text = text.translate(_DIGIT_TABLE)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه")
    return text


_RAW_NUMBER_WORDS = {
    "اول": 1, "أول": 1, "واحدة": 1, "واحد": 1,
    "ثاني": 2, "ثانية": 2, "اثنين": 2, "اثنتين": 2,
    "ثالثة": 3, "ثلاث": 3, "ثلاثة": 3,
    "رابعة": 4, "اربع": 4, "أربع": 4, "اربعة": 4, "أربعة": 4,
    "خامسة": 5, "خمس": 5, "خمسة": 5,
    "سادسة": 6, "ست": 6, "ستة": 6,
    "سابعة": 7, "سبع": 7, "سبعة": 7,
    "ثامنة": 8, "ثمان": 8, "ثماني": 8, "ثمانية": 8,
    "تاسعة": 9, "تسع": 9, "تسعة": 9,
    "عاشرة": 10, "عشر": 10, "عشرة": 10,
}
# نطبّع كل مفاتيح القاموس (نفس المعالجة يلي بتصير عالنص) عشان المطابقة تظبط
# دايماً بغض النظر عن التاء المربوطة أو الألف بأشكالها
NUMBER_WORDS = {_normalize(k): v for k, v in _RAW_NUMBER_WORDS.items()}


def _find_surah(raw_text: str):
    """يدور على أطول اسم سورة متطابق داخل النص (مطبّع) لتجنب تطابقات جزئية خاطئة"""
    norm_text = _normalize(raw_text)
    best = None  # (name, surah_num, ayah_count)
    for name, (num, count) in NAME_TO_SURAH.items():
        norm_name = _normalize(name)
        if norm_name in norm_text:
            if best is None or len(norm_name) > len(_normalize(best[0])):
                best = (name, num, count)
    return best


def _extract_number_word(text: str):
    """يدور على أول كلمة عدد عربية موجودة بالنص"""
    for word, value in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return value
    return None


def parse_request(user_text: str):
    text = _normalize(user_text).strip()

    surah = _find_surah(user_text)
    if not surah:
        return None  # ما لقينا اسم سورة بثقة -> نسيب الأمر للـ AI

    surah_name, surah_num, ayah_count = surah

    # 1) نطاق أرقام صريح: "من 90 لـ 95" / "90-95" / "90 الى 95" / "من 90 الى 95"
    range_match = re.search(
        r"(\d+)\s*(?:-|–|—|الى|إلى|لـ|ل|حتى)\s*(\d+)", text
    )
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if 1 <= start <= end <= ayah_count:
            return {
                "type": "quran",
                "surah_name": surah_name,
                "surah_num": surah_num,
                "start": start,
                "end": end,
            }
        return None  # أرقام غير منطقية -> نسيب الـ AI يتعامل معها ويشرح

    # 1ب) نطاق بالكلمات: "من واحد لستة" / "من ثلاثة الى عشرة"
    word_alt = "|".join(sorted(NUMBER_WORDS.keys(), key=len, reverse=True))
    word_range_match = re.search(
        r"من\s+(" + word_alt + r")\s+(?:-|–|—|الى|إلى|لـ|ل|حتى)\s*(" + word_alt + r")",
        text,
    )
    if word_range_match:
        start = NUMBER_WORDS[word_range_match.group(1)]
        end = NUMBER_WORDS[word_range_match.group(2)]
        if 1 <= start <= end <= ayah_count:
            return {
                "type": "quran",
                "surah_name": surah_name,
                "surah_num": surah_num,
                "start": start,
                "end": end,
            }
        return None

    # 2) "أول N آيات" أو "أول آية" / "أول عشر آيات"
    first_match = re.search(r"(اول|أول)\s+([^\s]+)?\s*(ايه|آيه|ايات|آيات)", text)
    if first_match:
        num_token = first_match.group(2)
        n = None
        if num_token:
            if num_token.isdigit():
                n = int(num_token)
            else:
                n = _extract_number_word(num_token)
        n = n or 1
        end = min(n, ayah_count)
        return {
            "type": "quran",
            "surah_name": surah_name,
            "surah_num": surah_num,
            "start": 1,
            "end": end,
        }

    # 3) "آخر N آيات"
    last_match = re.search(r"(اخر|آخر)\s+([^\s]+)?\s*(ايه|آيه|ايات|آيات)", text)
    if last_match:
        num_token = last_match.group(2)
        n = None
        if num_token:
            if num_token.isdigit():
                n = int(num_token)
            else:
                n = _extract_number_word(num_token)
        n = n or 1
        start = max(1, ayah_count - n + 1)
        return {
            "type": "quran",
            "surah_name": surah_name,
            "surah_num": surah_num,
            "start": start,
            "end": ayah_count,
        }

    # 4) آية واحدة محددة: "الآية 5" / "آية 5" / "الآية الخامسة"
    single_digit = re.search(r"(ايه|آيه)\s*(?:رقم)?\s*(\d+)", text)
    if single_digit:
        n = int(single_digit.group(2))
        if 1 <= n <= ayah_count:
            return {
                "type": "quran",
                "surah_name": surah_name,
                "surah_num": surah_num,
                "start": n,
                "end": n,
            }
        return None

    single_word = re.search(r"(ايه|آيه)\s+ال(\w+)", text)
    if single_word:
        n = _extract_number_word(single_word.group(2))
        if n and 1 <= n <= ayah_count:
            return {
                "type": "quran",
                "surah_name": surah_name,
                "surah_num": surah_num,
                "start": n,
                "end": n,
            }

    # 5) رقم واحد فقط بعد اسم السورة، مثل "البقرة 90" -> آية وحدة
    trailing_digit = re.search(r"(\d+)\s*$", text)
    if trailing_digit:
        n = int(trailing_digit.group(1))
        if 1 <= n <= ayah_count:
            return {
                "type": "quran",
                "surah_name": surah_name,
                "surah_num": surah_num,
                "start": n,
                "end": n,
            }
        return None

    # 6) اسم السورة بس بدون أي أرقام -> السورة كاملة
    if not re.search(r"\d", text) and not _extract_number_word(text):
        return {
            "type": "quran",
            "surah_name": surah_name,
            "surah_num": surah_num,
            "start": 1,
            "end": ayah_count,
        }

    # ما قدرنا نفهم الأرقام بثقة كافية -> نسيب الـ AI يتكفل فيها
    return None
