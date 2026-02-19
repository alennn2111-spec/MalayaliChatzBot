import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

app = Flask(__name__)
bot = Bot(token=TOKEN)

# store waiting users
waiting_users = []
active_chats = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # /start command
    if text == "/start":
        await update.message.reply_text("Send /find to search for a stranger")
        return

    # find partner
    if text == "/find":
        if user_id in active_chats:
            await update.message.reply_text("You are already in a chat")
            return

        if waiting_users:
            partner = waiting_users.pop(0)
            active_chats[user_id] = partner
            active_chats[partner] = user_id
            await bot.send_message(user_id, "Connected to stranger. Say hi 👀")
            await bot.send_message(partner, "Connected to stranger. Say hi 👀")
        else:
            waiting_users.append(user_id)
            await update.message.reply_text("Waiting for partner...")
        return

    # leave chat
    if text == "/leave":
        if user_id in active_chats:
            partner = active_chats.pop(user_id)
            active_chats.pop(partner, None)
            await bot.send_message(partner, "Stranger left the chat")
            await update.message.reply_text("You left the chat")
        else:
            await update.message.reply_text("You are not in a chat")
        return

    # relay message
    if user_id in active_chats:
        partner = active_chats[user_id]
        await bot.send_message(partner, text)
    else:
        await update.message.reply_text("Use /find to start chatting")


application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT, handle_message))

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Bot running"
