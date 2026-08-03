# -*- coding: utf-8 -*-
import os
import json
from google import genai

# تهيئة العميل بالطريقة الحديثة
API_KEY = os.environ.get("GEMINI_API_KEY", "")
ai_client = genai.Client(api_key=API_KEY) if API_KEY else None

def analyze_message(user_text):
    if not ai_client:
        return {"type": "chat", "message": "عذراً، مفتاح الذكاء الاصطناعي مفقود."}

    prompt = f"""
    أنت مساعد ذكي لبوت قرآن كريم على تليجرام، وتتحدث مع سيدة كبيرة في السن (جدة).
    رسالة المستخدمة: "{user_text}"
    
    إذا كانت الرسالة دردشة عادية، دعاء، أو شكر، ردي عليها باحترام ولطف شديد ودعاء جميل بلهجة عامية بسيطة ومحببة، واشرحي لها أنك بوت لإرسال الآيات. (أرجعي النص الطبيعي فقط).
    
    أما إذا كانت الرسالة طلب لسورة أو آيات بأي صيغة كانت، فاستخرجي المعلومات وأرجعيها بصيغة JSON حصراً بهذا الشكل:
    {{"type": "quran", "surah_name": "البقرة", "surah_num": 2, "start": 1, "end": 5}}
    
    ملاحظات هامة:
    - surah_num يجب أن يكون رقم السورة الصحيح في ترتيب المصحف (من 1 إلى 114).
    - إذا لم تحدد آية النهاية، اجعليها نفس آية البداية.
    - لا ترجعي أي نص قبل أو بعد الـ JSON.
    """
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        ai_text = response.text.strip().strip('`').replace('json\n', '').replace('```', '')
        
        try:
            return json.loads(ai_text)
        except json.JSONDecodeError:
            return {"type": "chat", "message": ai_text}
            
    except Exception as e:
        return {"type": "chat", "message": "صار في مشكلة بالاتصال مع الذكاء الاصطناعي، جربي ابعتي الطلب مرة ثانية 🙏"}
