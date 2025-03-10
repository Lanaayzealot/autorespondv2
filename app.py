import os
import asyncio
import logging
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Create the bot application
bot = Application.builder().token(TOKEN).build()

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command."""
    await update.message.reply_text('Hello! I am your auto-responder bot.')

async def auto_respond(update: Update, context: CallbackContext) -> None:
    """Auto-responds to any text message from users mentioning 'Lana'."""
    user_id = update.message.from_user.id
    message_text = update.message.text.lower()
    
    # Ensure bot responds only when 'Lana' is mentioned and not to the user 'Lana' themselves
    if 'lana' in message_text and user_id != bot.bot.id:  # The bot does not respond to itself
        await update.message.reply_text("Hi. I am currently AFK, I'll get back to you as soon as I can. Respectfully, Lana")

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
    try:
        json_data = request.get_json()
        logger.info(f"Incoming Update: {json_data}")  # Log incoming updates

        if not json_data:
            raise ValueError("Invalid JSON data")

        update = Update.de_json(json_data, bot.bot)

        # Ensure bot is initialized before processing updates
        if not bot._initialized:
            await bot.initialize()

        await bot.process_update(update)  # Process the update

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error in Webhook: {e}", exc_info=True)
        return 'Internal Server Error', 500

async def set_webhook():
    """Sets the webhook for the Telegram bot."""
    await bot.bot.set_webhook(WEBHOOK_URL)

def run_flask():
    """Runs Flask in a separate thread to avoid event loop conflicts."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

async def main():
    """Initialize the bot, set webhook, and start Flask."""
    await bot.initialize()  # Ensure bot is initialized
    await set_webhook()  # Set webhook

    # Run Flask in a separate thread to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, run_flask)

    # Keep the bot running
    await bot.run_polling()

if __name__ == '__main__':
    asyncio.run(main())  # Run the bot in an event loop
