# -*- coding: utf-8 -*-
import re
from surahs import NAME_TO_SURAH, NUM_TO_COUNT

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def normalize_digits(text: str) -> str:
    """يحول الأرقام العربية (٠-٩) إلى أرقام إنجليزية"""
    table = str.maketrans(ARABIC_DIGITS, "0123456789")
    return text.translate(table)


def parse_request(text: str):
    """
    يحاول يفهم رسالة زي:
    'سورة البقرة 90-95' أو 'البقرة ٩٠-٩٥' أو 'البقرة 90'
    يرجع (اسم_السورة, رقم_السورة, بداية, نهاية, رسالة_خطأ)
    """
    text = normalize_digits(text).strip()
    text = text.replace("سورة", "").strip()

    # نبحث عن أرقام الآيات في آخر النص (نطاق أو رقم واحد)
    match = re.search(r"(\d+)\s*[-–—]\s*(\d+)\s*$", text)
    single_match = re.search(r"(\d+)\s*$", text)

    if match:
        ayah_start, ayah_end = int(match.group(1)), int(match.group(2))
        name_part = text[:match.start()].strip()
    elif single_match:
        ayah_start = ayah_end = int(single_match.group(1))
        name_part = text[:single_match.start()].strip()
    else:
        return None, None, None, None, "ما قدرت ألاقي أرقام آيات بالرسالة. جربي مثلاً: سورة البقرة 90-95"

    name_part = name_part.strip(" ،,")
    if name_part not in NAME_TO_SURAH:
        return None, None, None, None, f"ما عرفت اتعرف على اسم السورة '{name_part}'. تأكدي من كتابة الاسم صح."

    surah_num, ayah_count = NAME_TO_SURAH[name_part]

    if ayah_start < 1 or ayah_end > ayah_count or ayah_start > ayah_end:
        return None, None, None, None, (
            f"سورة {name_part} فيها {ayah_count} آية بس، "
            f"تأكدي إن الأرقام اللي كتبتيها صحيحة."
        )

    return name_part, surah_num, ayah_start, ayah_end, None
