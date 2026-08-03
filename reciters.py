# -*- coding: utf-8 -*-
"""
قائمة القراء - الاسم الظاهر للمستخدم + كود المجلد على everyayah.com
كل مجلد يحوي ملفات الآيات بصيغة: SSSAAA.mp3  (مثال: 002090.mp3 = سورة 2 آية 90)
"""

RECITERS = {
    "مشاري العفاسي": "Alafasy_128kbps",
    "عبدالباسط عبدالصمد (مرتل)": "Abdul_Basit_Murattal_192kbps",
    "عبدالباسط عبدالصمد (مجود)": "Abdul_Basit_Mujawwad_128kbps",
    "محمود خليل الحصري (مرتل)": "Husary_128kbps",
    "محمود خليل الحصري (مجود)": "Husary_128kbps_Mujawwad",
    "محمد صديق المنشاوي (مرتل)": "Minshawy_Murattal_128kbps",
    "محمد صديق المنشاوي (مجود)": "Minshawy_Mujawwad_192kbps",
    "سعد الغامدي": "Ghamadi_40kbps",
    "عبدالرحمن السديس": "Abdurrahmaan_As-Sudais_192kbps",
    "سعود الشريم": "Saood_ash-Shuraym_128kbps",
    "أبو بكر الشاطري": "Abu_Bakr_Ash-Shaatree_128kbps",
    "علي الحذيفي": "Hudhaify_128kbps",
    "ماهر المعيقلي": "Maher_AlMuaiqly_64kbps",
    "محمد أيوب": "Muhammad_Ayyoub_128kbps",
    "هاني الرفاعي": "Hani_Rifai_192kbps",
    "محمد الطبلاوي": "Mohammad_al_Tablaway_128kbps",
    "عبدالله بصفر": "Abdullah_Basfar_192kbps",
}

BASE_URL = "https://everyayah.com/data/{folder}/{surah:03d}{ayah:03d}.mp3"


def ayah_url(folder: str, surah: int, ayah: int) -> str:
    return BASE_URL.format(folder=folder, surah=surah, ayah=ayah)
