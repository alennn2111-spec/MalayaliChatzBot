import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

waiting_users = []
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /find to search for a stranger")

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        await update.message.reply_text("You are already in a chat")
        return

    if waiting_users:
        partner = waiting_users.pop(0)
        active_chats[user_id] = partner
        active_chats[partner] = user_id
        await context.bot.send_message(user_id, "Connected to stranger 👀")
        await context.bot.send_message(partner, "Connected to stranger 👀")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("Waiting for partner...")

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        active_chats.pop(partner, None)
        await context.bot.send_message(partner, "Stranger left the chat")
        await update.message.reply_text("You left the chat")
    else:
        await update.message.reply_text("You are not in a chat")

async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in active_chats:
        partner = active_chats[user_id]
        await context.bot.send_message(partner, text)
    else:
        await update.message.reply_text("Use /find to start chatting")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("leave", leave))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))

app.run_polling()
