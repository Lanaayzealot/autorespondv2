from flask import Flask, request, jsonify
import logging
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, ApplicationBuilder, filters
from dotenv import load_dotenv
import os

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

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Ensure there's an active event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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
        
        async def process_update():
            await application.initialize()  # ✅ Ensure proper initialization
            await application.process_update(update)

        loop.run_until_complete(process_update())  # ✅ Run in existing loop

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=10000)
