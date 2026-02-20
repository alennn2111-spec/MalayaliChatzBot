# bot.py
import asyncio
import logging
import os
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import Response

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TOKEN"]
PORT = int(os.environ.get("PORT", 8000))
WEBHOOK_URL = os.environ["RENDER_EXTERNAL_URL"]

# Global state for pairs: {user_id: partner_id}
pairs: Dict[int, int] = {}
waiting_users: list[int] = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Anonymous Chat Bot\n\n"
        "/find - Find a random partner\n"
        "/leave - Leave current chat"
    )

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id in pairs:
        await update.message.reply_text("You are already in a chat. Use /leave to disconnect.")
        return
    
    waiting_users.append(user_id)
    await update.message.reply_text("Searching for partner...")
    
    await asyncio.sleep(1)  # Simulate search
    
    if len(waiting_users) >= 2:
        partner1 = waiting_users.pop(0)
        partner2 = waiting_users.pop(0)
        if partner1 != partner2:
            pairs[partner1] = partner2
            pairs[partner2] = partner1
            await context.bot.send_message(partner1, "Partner found! Start chatting anonymously.")
            await context.bot.send_message(partner2, "Partner found! Start chatting anonymously.")
        else:
            waiting_users.insert(0, partner1)
            await update.message.reply_text("No partner available. Try again.")
    else:
        await update.message.reply_text("Waiting for another user...")

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id not in pairs:
        await update.message.reply_text("You are not in a chat.")
        return
    
    partner_id = pairs.pop(user_id)
    if partner_id in pairs:
        pairs.pop(partner_id, None)
        await context.bot.send_message(partner_id, "Your partner has left the chat.")
    
    await update.message.reply_text("You left the chat.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id not in pairs:
        await update.message.reply_text("Use /find to start a chat.")
        return
    
    partner_id = pairs[user_id]
    message_text = update.message.text or update.message.caption or "📎"
    
    await context.bot.send_message(
        chat_id=partner_id,
        text=f"👤 Stranger: {message_text}"
    )

async def webhook_endpoint(request: Request, application: Application) -> Response:
    json_data = await request.json()
    update = Update.de_json(json_data, application.bot)
    await application.process_update(update)
    return Response()

async def main() -> None:
    application = (
        Application.builder()
        .token(TOKEN)
        .updater(None)
        .build()
    )
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("find", find))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Set webhook
    webhook_path = "/webhook"
    await application.bot.set_webhook(f"{WEBHOOK_URL.rstrip('/')}{webhook_path}")
    
    # FastAPI app
    app = FastAPI()
    app.post(webhook_path)(lambda request: webhook_endpoint(request, application))
    
    # Uvicorn config
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())

