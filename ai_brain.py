# -*- coding: utf-8 -*-
import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """
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


def _finalize(result):
    """يتأكد إن الأرقام int فعلاً قبل ما نرجع النتيجة للبوت"""
    if result.get("type") == "quran":
        result["surah_num"] = int(result["surah_num"])
        result["start"] = int(result["start"])
        result["end"] = int(result["end"])
    return result


def _call_gemini(user_text, api_key):
    """يحاول يستخدم Gemini. يرجع dict عند النجاح، أو يرمي Exception عند الفشل."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": PROMPT_TEMPLATE.format(user_text=user_text)}]}
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json"
        }
    }

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    ai_text = (
        response_data["candidates"][0]["content"]["parts"][0]["text"]
    ).strip()

    return _finalize(json.loads(ai_text))


def _call_groq(user_text, api_key):
    """
    مزوّد احتياطي مجاني (Groq) لما Gemini يفشل (كوتا/404/أي خطأ).
    Groq بيدعم واجهة متوافقة مع OpenAI، وعنده فري تير سخي لموديلات llama/gpt-oss.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "user", "content": PROMPT_TEMPLATE.format(user_text=user_text)}
        ]
    }

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    ai_text = response_data["choices"][0]["message"]["content"].strip()

    return _finalize(json.loads(ai_text))


def analyze_message(user_text):
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not gemini_key and not groq_key:
        return {
            "type": "chat",
            "message": "مفتاح الذكاء الاصطناعي غير موجود."
        }

    if gemini_key:
        try:
            return _call_gemini(user_text, gemini_key)
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            logger.error("Gemini HTTP error %s: %s", error.code, error_body)
        except Exception:
            logger.exception("Gemini request failed")

    if groq_key:
        try:
            return _call_groq(user_text, groq_key)
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            logger.error("Groq HTTP error %s: %s", error.code, error_body)
        except Exception:
            logger.exception("Groq request failed")

    return {
        "type": "chat",
        "message": "تعذر فهم الطلب حالياً، أعد المحاولة بعد قليل."
    }
