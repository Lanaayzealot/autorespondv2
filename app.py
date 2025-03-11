from fastapi import FastAPI, Request
import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters

# Retrieve environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OWNER_ID = int(os.getenv('TELEGRAM_OWNER_ID', "0"))  # Default to "0" to prevent NoneType errors

# Initialize FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Telegram bot application
application = ApplicationBuilder().token(TOKEN).build()

# Global bot state
bot_running = False

# Start command
async def start(update: Update, context: CallbackContext):
    global bot_running
    bot_running = True
    await update.message.reply_text("Auto-reply bot is now active!")

# Stop command
async def stop(update: Update, context: CallbackContext):
    global bot_running
    bot_running = False
    await update.message.reply_text("Auto-reply bot has been stopped.")

# Message handler for forwarding and replying
async def forward_and_reply(update: Update, context: CallbackContext):
    global bot_running
    if not bot_running:
        return  # Ignore messages if the bot is stopped

    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    text = update.message.text

    # Forward the message to the bot owner
    forward_text = f"📩 New message from @{user_name} ({user_id}):\n{text}"
    await context.bot.send_message(chat_id=OWNER_ID, text=forward_text)

    # Reply to the sender with the away message
    await update.message.reply_text("Hi, I am away at the moment, I will get back to you ASAP.")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_and_reply))

# Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    """Handles incoming webhook requests from Telegram."""
    json_data = await request.json()
    logger.info(f"Received webhook request: {json_data}")

    if not json_data:
        return {"error": "Invalid JSON data"}, 400

    update = Update.de_json(json_data, application.bot)

    # Async function to process the update
    async def process_update():
        await application.initialize()
        await application.process_update(update)

    # Call the async function non-blocking
    asyncio.create_task(process_update())

    return {"message": "OK"}, 200

# Route for root URL
@app.get("/")
async def index():
    return {"message": "Bot is running!"}
