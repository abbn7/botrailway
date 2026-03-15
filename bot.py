import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
API_KEY = os.environ.get("API_KEY", "").strip()
API_URL = "https://agentrouter.org/v1/chat/completions"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing!")
if not API_KEY:
    raise ValueError("API_KEY is missing!")

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("أهلاً! أنا بوت ذكاء اصطناعي. كلمني في أي حاجة 🤖")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("تم مسح المحادثة ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_message})

    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    await update.message.chat.send_action("typing")

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://agentrouter.org",
                "Referer": "https://agentrouter.org/"
            },
            json={
                "model": "glm-4.6",
                "messages": user_histories[user_id],
                "max_tokens": 1000
            },
            timeout=60
        )
        logger.info(f"API status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API error: {response.text[:300]}")
            await update.message.reply_text(f"خطأ {response.status_code} من الـ API")
            return

        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except requests.exceptions.Timeout:
        await update.message.reply_text("الـ API بطيء، حاول تاني 🙏")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"خطأ: {str(e)}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logger.info("Bot starting...")
app.run_polling()
