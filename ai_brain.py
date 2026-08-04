# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.error

def analyze_message(user_text):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"type": "chat", "message": "عذراً، مفتاح الذكاء الاصطناعي مفقود."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    prompt = f"""
    أنت مساعد ذكي لبوت قرآن كريم على تليجرام،.
    رسالة المستخدمة: "{user_text}"
    
    إذا كانت الرسالة دردشة عادية، دعاء، أو شكر، رد عليها باحترام ولطف شديد ودعاء جميل بلهجة عامية بسيطة ومحببة، واشرح أنك بوت لإرسال الآيات. (أرجعي النص الطبيعي فقط).
    
    أما إذا كانت الرسالة طلب لسورة أو آيات بأي صيغة كانت، فاستخرج المعلومات وأرجعها بصيغة JSON حصراً بهذا الشكل:
    {{"type": "quran", "surah_name": "البقرة", "surah_num": 2, "start": 1, "end": 5}}
    
    ملاحظات هامة:
    - surah_num يجب أن يكون رقم السورة الصحيح في ترتيب المصحف (من 1 إلى 114).
    - إذا لم تحدد آية النهاية، اجعلها نفس آية البداية.
    - لا ترجع أي نص قبل أو بعد الـ JSON.
    """
    
    headers = {'Content-Type': 'application/json'}
    payload = {
    "contents": [{
        "parts": [{"text": prompt}]
    }]
}
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            ai_text = res_data['candidates'][0]['content']['parts'][0]['text']
            
            clean_text = ai_text.strip().strip('`').replace('json\n', '').replace('```', '')
            
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError:
                return {"type": "chat", "message": ai_text}
                
    except Exception as e:
        return {"type": "chat", "message": "صار في مشكلة بالاتصال مع الذكاء الاصطناعي، اطلب مرة اخرى 🙏"}
