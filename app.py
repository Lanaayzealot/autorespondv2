from flask import Flask, request, jsonify
import logging
from telegram import Update, Bot
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackContext,
    ApplicationBuilder,
    ChatMemberHandler,
    filters
)
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# Check if the token is loaded.  Good practice!
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
    exit(1)  # Exit if the token isn't found

# Use a global variable for the application.  This simplifies the webhook.
application = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello, I will be responding instead of you when you are away!")

async def stop(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello, I am glad you're back!")

async def echo(update: Update, context: CallbackContext):
    await update.message.reply_text(update.message.text)

async def my_chat_member(update: Update, context: CallbackContext):
    logger.info(f"Chat member update: {update.chat_member}")
    if update.chat_member.new_chat_member.status == "kicked":
        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=f"The bot {update.chat_member.new_chat_member.user.first_name} has been kicked."
        )

# Add handlers (best to do this before the webhook definition)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
application.add_handler(ChatMemberHandler(my_chat_member))

@app.route('/webhook', methods=['POST'])
async def webhook():  # Make the webhook function async
    """Handles incoming webhook requests from Telegram."""
    try:
        json_data = request.get_json()
        logger.info(f"Incoming Update: {json_data}")

        if not json_data:
            logger.error("Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data'}), 400

        update = Update.de_json(json_data, application.bot)

        # Process the update directly using await.  Much cleaner!
        await application.process_update(update)

        return 'OK', 200

    except Exception as e:
        logger.exception("Error processing update:")  # Logs the full traceback
        return jsonify({'error': 'Internal Server Error
