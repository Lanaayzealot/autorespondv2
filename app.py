import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Create the bot application
bot = Application.builder().token(TOKEN).build()

# Flag to track if auto-response is enabled
auto_response_enabled = False

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command."""
    global auto_response_enabled
    auto_response_enabled = True
    await update.message.reply_text('Auto-response is now enabled!')

async def auto_respond(update: Update, context: CallbackContext) -> None:
    """Auto-responds to any text message from users if enabled."""
    global auto_response_enabled
    if auto_response_enabled and update.message:
        await update.message.reply_text("I'm currently unavailable. I'll get back to you soon!")

# Register handlers
bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_respond))

@app.route('/')
def home():
    """Home route to check if the server is running."""
    return "Telegram bot is running."

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handles incoming webhook requests from Telegram."""
    json_data = request.get_json()
    logger.info(f"Incoming Update: {json_data}")

    if not json_data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    update = Update.de_json(json_data, bot.bot)
    await bot.process_update(update)

    return 'OK', 200

async def set_webhook():
    """Sets the webhook for the Telegram bot."""
    # You can set the webhook here if needed
    pass

def run_flask():
    """Runs Flask app."""
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

async def main():
    """Initialize the bot and set the webhook."""
    await bot.initialize()
    run_flask()

if __name__ == '__main__':
    asyncio.run(main())
