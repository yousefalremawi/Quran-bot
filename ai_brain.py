# -*- coding: utf-8 -*-
import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def analyze_message(user_text):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        return {
            "type": "chat",
            "message": "مفتاح الذكاء الاصطناعي غير موجود."
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-3.6-flash:generateContent?key={api_key}"
    )

    prompt = f"""
أنت المسؤول عن فهم رسائل المستخدم داخل بوت قرآن كريم.

افهم الطلب مهما كانت طريقة كتابته، سواء كان بالفصحى أو باللهجة العامية،
وسواء استخدم المستخدم أرقاماً عربية أو إنجليزية.

رسالة المستخدم:
{user_text}

المطلوب:

إذا كان المستخدم يطلب سورة أو مجموعة آيات، أرجع JSON فقط بالشكل التالي:
{{"type":"quran","surah_name":"البقرة","surah_num":2,"start":1,"end":5}}

أمثلة للفهم:
- "أول عشر آيات من البقرة" تعني start=1 و end=10
- "سورة النور الآيات 9-16" تعني start=9 و end=16
- "البقرة من واحد لستة" تعني start=1 و end=6
- "بدي الآية الخامسة من الكهف" تعني start=5 و end=5
- "آخر خمس آيات من سورة الكهف" احسب أرقام آخر خمس آيات بشكل صحيح

إذا كانت الرسالة سلاماً أو شكراً أو كلاماً عادياً، أرجع:
{{"type":"chat","message":"رد عربي قصير وطبيعي"}}

قواعد مهمة:
- افهم المعنى، ولا تجبر المستخدم على صيغة محددة.
- لا تكتب أي شيء خارج JSON.
- لا تستخدم صيغة المذكر أو المؤنث في الرد.
- لا تضع Markdown أو علامات ``` حول JSON.
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json"
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_data = json.loads(
                response.read().decode("utf-8")
            )

        ai_text = (
            response_data["candidates"][0]
            ["content"]["parts"][0]["text"]
        ).strip()

        result = json.loads(ai_text)

        if result.get("type") == "quran":
            result["surah_num"] = int(result["surah_num"])
            result["start"] = int(result["start"])
            result["end"] = int(result["end"])

        return result

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Gemini HTTP error %s: %s",
            error.code,
            error_body
        )

        return {
            "type": "chat",
            "message": "تعذر فهم الطلب حالياً، أعد المحاولة بعد قليل."
        }

    except Exception:
        logger.exception("Gemini request failed")

        return {
            "type": "chat",
            "message": "تعذر فهم الطلب حالياً، أعد المحاولة بعد قليل."
        }
