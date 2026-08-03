# -*- coding: utf-8 -*-
import os
import tempfile
import requests
import subprocess
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
    يحمل الآيات، يدمجهم ويكررهم بسرعة البرق باستخدام ffmpeg، ويرجع مسار ملف mp3 نهائي.
    """
    tmpdir = tempfile.mkdtemp(prefix="quranbot_")
    failed = []
    downloaded_files = []

    total = ayah_end - ayah_start + 1
    
    # 1. تحميل الآيات المطلوبة
    for i, ayah in enumerate(range(ayah_start, ayah_end + 1), start=1):
        dest = os.path.join(tmpdir, f"{ayah}.mp3")
        ok = download_ayah(folder, surah, ayah, dest)
        if ok:
            downloaded_files.append(dest)
        else:
            failed.append(ayah)

        if progress_callback:
            progress_callback(i, total)

    if not downloaded_files:
        return None, failed

    out_path = os.path.join(tmpdir, "recitation.mp3")
    list_file = os.path.join(tmpdir, "list.txt")

    # 2. إنشاء ملف نصي لـ ffmpeg يحتوي على أسماء الملفات (مع التكرار)
    with open(list_file, "w", encoding="utf-8") as f:
        for _ in range(repeat):
            for audio_file in downloaded_files:
                f.write(f"file '{audio_file}'\n")

    # 3. دمج الملفات وتكرارها بسرعة البرق دون فك الضغط
    command = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        out_path
    ]
    
    # تنفيذ الأمر بصمت
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return out_path, failed
