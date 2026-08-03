# -*- coding: utf-8 -*-
import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from utils import parse_request
from reciters import RECITERS
from audio import build_recording

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

REPEAT_OPTIONS = [1, 2, 3, 5, 7, 10]

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً وسهلاً 🌙\n\n"
        "ابعتيلي اسم السورة ورقم الآيات، مثلاً:\n"
        "سورة البقرة 90-95\n\n"
        "وبعدها بختارلك القارئ وعدد مرات التكرار، وبجهزلك التسجيل الصوتي."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    name, surah_num, ayah_start, ayah_end, error = parse_request(text)

    if error:
        await update.message.reply_text(error)
        return

    # نخزن الطلب مؤقتاً بانتظار اختيار القارئ
    context.user_data["pending"] = {
        "surah_name": name,
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

    await update.message.reply_text(
        f"تمام ✅ سورة {name} من آية {ayah_start} لـ {ayah_end}\n\nاختاري القارئ:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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
        f"هذا ممكن ياخد شوي وقت، استنّي..."
    )

    def progress(current, total):
        pass  # ممكن نحدث الرسالة كل كم آية لو حبينا لاحقاً

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
            "لازم تحطي التوكن! عرّفي متغير البيئة BOT_TOKEN قبل ما تشغلي البوت.\n"
            "مثال: BOT_TOKEN=123456:ABC-DEF python3 bot.py"
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
