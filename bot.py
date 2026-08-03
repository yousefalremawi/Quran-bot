# -*- coding: utf-8 -*-
import logging
import os
import json
import google.generativeai as genai

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from reciters import RECITERS
from audio import build_recording

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# إخفاء رسائل الاتصال المزعجة
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

REPEAT_OPTIONS = [1, 2, 3, 5, 7, 10]

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# تهيئة الذكاء الاصطناعي بالموديل المتوافق تماماً
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # استخدام الموديل القياسي المدعوم حالياً
    ai_model = genai.GenerativeModel('gemini-2.5-flash')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً وسهلاً 🌙\n\n"
        "اكتبيلي اسم السورة وأي آيات بتحبي تسمعيها بأي طريقة بتريحك، مثلاً:\n"
        "- سورة البقرة من 90 لـ 95\n"
        "- بدي أول خمس آيات من الكهف\n\n"
        "وبعدها بختارلك القارئ وعدد مرات التكرار، وبجهزلك التسجيل الصوتي."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("⏳ ثواني بس أفهم طلبك...")

    if not GEMINI_API_KEY:
        await msg.edit_text("عذراً، مفتاح الذكاء الاصطناعي مفقود.")
        return

    prompt = f"""
    أنت مساعد ذكي لبوت قرآن كريم على تليجرام، وتتحدث مع سيدة كبيرة في السن (جدة).
    رسالة المستخدمة: "{text}"
    
    إذا كانت الرسالة دردشة عادية، دعاء، أو شكر، ردي عليها باحترام ولطف شديد ودعاء جميل بلهجة عامية بسيطة ومحببة، واشرحي لها أنك بوت لإرسال الآيات. (أرجعي النص الطبيعي فقط).
    
    أما إذا كانت الرسالة طلب لسورة أو آيات بأي صيغة كانت، فاستخرجي المعلومات وأرجعيها بصيغة JSON حصراً بهذا الشكل:
    {{"type": "quran", "surah_name": "البقرة", "surah_num": 2, "start": 1, "end": 5}}
    
    ملاحظات هامة:
    - surah_num يجب أن يكون رقم السورة الصحيح في ترتيب المصحف (من 1 إلى 114).
    - إذا لم تحدد آية النهاية، اجعليها نفس آية البداية.
    - لا ترجعي أي نص قبل أو بعد الـ JSON.
    """
    
    try:
        response = ai_model.generate_content(prompt)
        ai_text = response.text
        
        clean_text = ai_text.strip().strip('`').replace('json\n', '')
        
        try:
            data = json.loads(clean_text)
            
            if data.get("type") == "quran":
                surah_name = data.get("surah_name")
                surah_num = int(data.get("surah_num"))
                ayah_start = int(data.get("start"))
                ayah_end = int(data.get("end"))
                
                context.user_data["pending"] = {
                    "surah_name": surah_name,
                    "surah_num": surah_num,
                    "ayah_start": ayah_start,
                    "ayah_end": ayah_end,
                }

                keyboard = []
                row = []
                for i, reciter_name in enumerate(RECITERS.keys(), start=1):
                    row.append(InlineKeyboardButton(reciter_name, callback_data=f"reciter|{reciter_name}"))
                    if i % 2 == 0:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)

                await msg.edit_text(
                    f"تمام ✅ سورة {surah_name} من آية {ayah_start} لـ {ayah_end}\n\nاختاري القارئ:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await msg.edit_text(ai_text)
                
        except json.JSONDecodeError:
            await msg.edit_text(ai_text)
            
    except Exception as e:
        logger.exception("AI Error")
        await msg.edit_text("صار في مشكلة بالاتصال، جربي ابعتي الطلب مرة ثانية 🙏")


async def handle_reciter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reciter_name = query.data.split("|", 1)[1]
    pending = context.user_data.get("pending")
    if not pending:
        await query.edit_message_text("في مشكلة، ابعتي الطلب من جديد لو سمحتي 🙏")
        return

    pending["reciter_name"] = reciter_name
    context.user_data["pending"] = pending

    keyboard = [
        [InlineKeyboardButton(str(n), callback_data=f"repeat|{n}") for n in REPEAT_OPTIONS]
    ]
    await query.edit_message_text(
        f"القارئ: {reciter_name}\n\nكم مرة بدك التسجيل يتكرر؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_repeat_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    repeat = int(query.data.split("|", 1)[1])
    pending = context.user_data.get("pending")
    if not pending:
        await query.edit_message_text("في مشكلة، ابعتي الطلب من جديد لو سمحتي 🙏")
        return

    surah_name = pending["surah_name"]
    surah_num = pending["surah_num"]
    ayah_start = pending["ayah_start"]
    ayah_end = pending["ayah_end"]
    reciter_name = pending["reciter_name"]
    folder = RECITERS[reciter_name]

    status_msg = await query.edit_message_text(
        f"جاري تجهيز التسجيل 🎧\n"
        f"سورة {surah_name} ({ayah_start}-{ayah_end}) - {reciter_name} - مكرر {repeat} مرات\n\n"
        f"هذا ممكن ياخد ثواني، استنّي شوي..."
    )

    def progress(current, total):
        pass  

    try:
        out_path, failed = build_recording(
            folder, surah_num, ayah_start, ayah_end, repeat, progress
        )
    except Exception as e:
        logger.exception("Error building recording")
        await status_msg.edit_text(f"صار في خطأ أثناء تجهيز التسجيل: {e}")
        return

    if out_path is None:
        await status_msg.edit_text(
            "ما قدرت أحمل ولا آية من هالقارئ. جربي قارئ ثاني."
        )
        return

    caption = f"سورة {surah_name} ({ayah_start}-{ayah_end}) - {reciter_name} - مكرر {repeat}×"
    if failed:
        caption += f"\n⚠️ ما نزلت آية/آيات: {', '.join(map(str, failed))}"

    with open(out_path, "rb") as audio_file:
        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=audio_file,
            caption=caption,
            title=f"{surah_name} {ayah_start}-{ayah_end}",
        )

    await status_msg.delete()
    context.user_data.pop("pending", None)


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "لازم تحطي التوكن! عرّفي متغير البيئة BOT_TOKEN قبل ما تشغلي البوت."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_reciter_choice, pattern=r"^reciter\|"))
    app.add_handler(CallbackQueryHandler(handle_repeat_choice, pattern=r"^repeat\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
