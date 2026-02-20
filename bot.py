# bot.py
import asyncio
import logging
import os
from typing import Dict, AsyncGenerator

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

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
WEBHOOK_PATH = "/webhook"

application: Application = None

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
    
    await asyncio.sleep(1)
    
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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global application
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("find", find))
    application.add_handler(CommandHandler("leave", leave))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Set webhook
    webhook_url = f"{os.environ['RENDER_EXTERNAL_URL'].rstrip('/')}{WEBHOOK_PATH}"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to {webhook_url}")
    
    await application.initialize()
    await application.start()
    yield
    await application.stop()
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def webhook(req
