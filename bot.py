import os
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + "/webhook"

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

async def handle(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response()

async def main():
    global app
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)

    web_app = web.Application()
    web_app.router.add_post("/webhook", handle)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()

    await app.start()
    await app.stop()

import asyncio
asyncio.run(main())
