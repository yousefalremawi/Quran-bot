# -*- coding: utf-8 -*-
import os
import tempfile
import requests
from pydub import AudioSegment
from reciters import ayah_url


def download_ayah(folder: str, surah: int, ayah: int, dest_path: str) -> bool:
    """يحمل ملف صوتي لآية وحدة. يرجع True لو نجح."""
    url = ayah_url(folder, surah, ayah)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(dest_path, "wb") as f:
                f.write(r.content)
            return True
        return False
    except requests.RequestException:
        return False


def build_recording(folder: str, surah: int, ayah_start: int, ayah_end: int,
                     repeat: int, progress_callback=None):
    """
    يحمل الآيات، يدمجهم، يكررهم، ويرجع مسار ملف mp3 نهائي.
    progress_callback(current, total) اختياري لتحديث حالة التحميل.
    يرجع (مسار_الملف, قائمة_آيات_فشلت)
    """
    tmpdir = tempfile.mkdtemp(prefix="quranbot_")
    failed = []
    segments = []
    silence = AudioSegment.silent(duration=700)  # وقفة بين الآيات

    total = ayah_end - ayah_start + 1
    for i, ayah in enumerate(range(ayah_start, ayah_end + 1), start=1):
        dest = os.path.join(tmpdir, f"{ayah}.mp3")
        ok = download_ayah(folder, surah, ayah, dest)
        if ok:
            try:
                seg = AudioSegment.from_mp3(dest)
                segments.append(seg)
            except Exception:
                failed.append(ayah)
        else:
            failed.append(ayah)

        if progress_callback:
            progress_callback(i, total)

    if not segments:
        return None, failed

    # دمج الآيات مع وقفة بينهم
    combined = segments[0]
    for seg in segments[1:]:
        combined += silence + seg

    # تكرار كامل المقطع المدموج
    final = combined * repeat

    out_path = os.path.join(tmpdir, "recitation.mp3")
    final.export(out_path, format="mp3", bitrate="128k")
    return out_path, failed
