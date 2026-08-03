import google.generativeai as genai
import os
import json

# ربط الكود بمفتاح الذكاء الاصطناعي اللي ضفناه بـ Railway
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_message(user_text):
    prompt = f"""
    أنت مساعد ذكي لبوت قرآن كريم على تليجرام.
    رسالة المستخدم: "{user_text}"
    
    إذا كانت الرسالة دردشة عادية أو سلام، رد عليه بلطف واشرح له أنك بوت لإرسال الآيات القرآنية. (أرجع النص فقط).
    إذا كانت الرسالة طلب لسورة أو آيات، استخرج المعلومات التالية وأرجعها بصيغة JSON حصراً بهذا الشكل:
    {{"type": "quran", "surah": "اسم السورة", "start": رقم_البداية, "end": رقم_النهاية}}
    إذا لم يحدد آية النهاية، اجعلها نفس آية البداية.
    """
    response = model.generate_content(prompt)
    
    try:
        # نحاول فهم إذا كان الرد JSON (يعني طلب قرآن)
        return json.loads(response.text.strip('```json').strip('```'))
    except:
        # إذا فشل، معناه إنها دردشة عادية
        return {"type": "chat", "message": response.text}
