import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = os.environ.get("TOKEN")

waiting_users = []
active_chats = {}

def start(update, context):
    update.message.reply_text("Send /find to search for a stranger")

def find(update, context):
    user_id = update.message.chat_id

    if user_id in active_chats:
        update.message.reply_text("You are already in a chat")
        return

    if waiting_users:
        partner = waiting_users.pop(0)
        active_chats[user_id] = partner
        active_chats[partner] = user_id
        context.bot.send_message(user_id, "Connected to stranger 👀")
        context.bot.send_message(partner, "Connected to stranger 👀")
    else:
        waiting_users.append(user_id)
        update.message.reply_text("Waiting for partner...")

def leave(update, context):
    user_id = update.message.chat_id

    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        active_chats.pop(partner, None)
        context.bot.send_message(partner, "Stranger left the chat")
        update.message.reply_text("You left the chat")
    else:
        update.message.reply_text("You are not in a chat")

def relay(update, context):
    user_id = update.message.chat_id
    text = update.message.text

    if user_id in active_chats:
        partner = active_chats[user_id]
        context.bot.send_message(partner, text)
    else:
        update.message.reply_text("Use /find to start chatting")

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("find", find))
dp.add_handler(CommandHandler("leave", leave))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, relay))

updater.start_polling()
updater.idle()
