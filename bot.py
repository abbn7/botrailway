import os
import logging
import json
import httpx
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
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4.6",
                    "messages": user_histories[user_id],
                    "max_tokens": 1000
                }
            )

        logger.info(f"Status: {response.status_code}")
        logger.info(f"Raw response: {response.text[:500]}")

        data = response.json()

        # Handle different response formats
        if isinstance(data, dict):
            if "choices" in data:
                reply = data["choices"][0]["message"]["content"]
            elif "content" in data:
                reply = data["content"]
            elif "message" in data:
                reply = data["message"]
            elif "error" in data:
                reply = f"خطأ من الـ API: {data['error']}"
            else:
                reply = str(data)
        else:
            reply = str(data)

        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"خطأ: {str(e)[:200]}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logger.info("Bot starting...")
app.run_polling()
