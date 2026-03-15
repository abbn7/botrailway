import os
import logging
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
PROXY_URL = os.environ.get("PROXY_URL", "").strip()  # Cloudflare Worker URL

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing!")
if not API_KEY:
    raise ValueError("API_KEY is missing!")
if not PROXY_URL:
    raise ValueError("PROXY_URL is missing!")

API_URL = f"{PROXY_URL}/v1/chat/completions"
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
        data = response.json()

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            user_histories[user_id].append({"role": "assistant", "content": reply})
            await update.message.reply_text(reply)
        else:
            logger.error(f"Unexpected response: {data}")
            await update.message.reply_text(f"خطأ: {str(data)[:200]}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"خطأ: {str(e)[:200]}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

logger.info("Bot starting...")
app.run_polling()
