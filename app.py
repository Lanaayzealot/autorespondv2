from flask import Flask, request, jsonify
import logging
from telegram import Update
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
import asyncio  # Import asyncio to handle async functions properly

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retrieve the Telegram bot token from the environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
application = ApplicationBuilder().token(TOKEN).build()

# Command handler for /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello, I will be responding instead of you when you are away!")

# Command handler for /stop
async def stop(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello, I am glad you're back!")

# Echo handler for text messages
async def echo(update: Update, context: CallbackContext):
    await update.message.reply_text(update.message.text)

# Handler for chat member updates
async def my_chat_member(update: Update, context: CallbackContext):
    logger.info(f"Chat member update: {update.chat_member}")
    if update.chat_member.new_chat_member.status == "kicked":
        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=f"The bot {update.chat_member.new_chat_member.user.first_name} has been kicked."
        )

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
application.add_handler(ChatMemberHandler(my_chat_member))  # ✅ Corrected chat member update handler

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles incoming webhook requests from Telegram."""
    try:
        json_data = request.get_json()
        logger.info(f"Incoming Update: {json_data}")

        if not json_data:
            logger.error("Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data'}), 400

        update = Update.de_json(json_data, application.bot)
        
        # ✅ Fix: Run process_update asynchronously
        asyncio.create_task(application.process_update(update))

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    # Start the Flask app on port 10000
    app.run(host='0.0.0.0', port=10000)
