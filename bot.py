import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("API_KEY")
API_URL = "https://agentrouter.org/v1/chat/completions"

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("أهلاً! أنا بوت ذكاء اصطناعي. كلمني في أي حاجة 🤖")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_message})

    # Keep last 10 messages only
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    await update.message.chat.send_action("typing")

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "glm-4.6",
                "messages": user_histories[user_id],
                "max_tokens": 1000
            },
            timeout=30
        )
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        user_histories[user_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = "حصل خطأ، حاول تاني 🙏"

    await update.message.reply_text(reply)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("تم مسح المحادثة ✅")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
