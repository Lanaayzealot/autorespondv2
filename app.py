from flask import Flask, request, jsonify
import logging
import asyncio
import os
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, ApplicationBuilder, filters

# Retrieve environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Bot Token
OWNER_ID = int(os.getenv('TELEGRAM_OWNER_ID', "0"))  # Default to "0" to prevent NoneType errors

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Telegram bot application
application = ApplicationBuilder().token(TOKEN).build()

# Global bot state
bot_running = False

# Start command handler
async def start(update: Update, context: CallbackContext):
    global bot_running
    bot_running = True
    await update.message.reply_text("Auto-reply bot is now active!")

# Stop command handler
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

# Add handlers for start, stop, and forwarding/replying
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_and_reply))

# Webhook route to handle incoming requests from Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming webhook requests from Telegram."""
    try:
        json_data = request.get_json()
        logger.info(f"Received webhook request: {json_data}")  # Log incoming data

        if not json_data:
            logger.error("Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data'}), 400

        update = Update.de_json(json_data, application.bot)

        # Process update in async function
        async def process_update():
            await application.initialize()  # Ensure proper initialization
            await application.process_update(update)

        asyncio.ensure_future(process_update())  # Non-blocking execution

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

# Main entry point for Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
