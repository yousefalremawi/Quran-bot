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
أنت مساعد ذكي لبوت قرآن كريم على تليجرام.

رسالة المستخدم:
"{user_text}"

اتبع القواعد التالية:

1. خاطب المستخدم بصيغة محايدة، ولا تفترض أنه ذكر أو أنثى.
2. لا تكرر نفس الجملة أو نفس المعنى.
3. اجعل الرد قصيراً وطبيعياً.
4. لا تشرح وظيفة البوت في كل رد.
5. إذا كانت الرسالة مجرد شكر أو سلام أو دعاء، أجب بجملة قصيرة ولطيفة فقط.
6. إذا كانت الرسالة طلباً لسورة أو آيات، استخرج المعلومات وأرجع JSON فقط بهذا الشكل:

{{"type": "quran", "surah_name": "البقرة", "surah_num": 2, "start": 1, "end": 5}}

7. surah_num يجب أن يكون رقم السورة الصحيح من 1 إلى 114.
8. إذا طلب المستخدم أول عدد من الآيات، ابدأ من الآية 1.
9. إذا طلب آخر عدد من الآيات، احسب البداية والنهاية بشكل صحيح.
10. إذا ذكر آية واحدة فقط، اجعل start و end نفس الرقم.
11. لا ترجع أي كلام قبل أو بعد JSON عندما يكون الطلب قرآنياً.
12. في الدردشة العادية لا تستخدم JSON، وأرجع النص الطبيعي فقط.
"""
    
    headers = {'Content-Type': 'application/json'}
    payload = {
    "contents": [{
        "parts": [{"text": prompt}]
    }],
    "generationConfig": {
        "temperature": 0.1,
        "topP": 0.8,
        "maxOutputTokens": 300
    }
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
