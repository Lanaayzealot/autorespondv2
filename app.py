from flask import Flask, request, jsonify
import logging
from telegram import Update, Bot
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackContext,
    ApplicationBuilder,
    ChatMemberHandler,
    filters,
    Application
)
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables
load_dotenv()

# --- Flask Setup ---
app = Flask(__name__)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Telegram Bot Token ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
    exit(1)  # Exit if the token isn't found

# --- Telegram Bot Handlers ---
# Define handlers *before* creating the Application.

async def start(update: Update, context: CallbackContext):
    """Handles the /start command."""
    await update.message.reply_text("Hello, I will be responding instead of you when you are away!")

async def stop(update: Update, context: CallbackContext):
    """Handles the /stop command."""
    await update.message.reply_text("Hello, I am glad you're back!")

async def echo(update: Update, context: CallbackContext):
    """Echoes back any text message that is not a command."""
    await update.message.reply_text(update.message.text)

async def my_chat_member(update: Update, context: CallbackContext):
    """Handles changes to the bot's membership status in a chat."""
    logger.info(f"Chat member update: {update.chat_member}")
    if update.chat_member.new_chat_member.status == "kicked":
        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=f"The bot {update.chat_member.new_chat_member.user.first_name} has been kicked."
        )

# --- Application Initialization (Outside of Webhook) ---
# We create the Application *once* here.
application: Application = ApplicationBuilder().token(TOKEN).build()

# --- Register Handlers ---
# Register handlers *before* initializing.
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
application.add_handler(ChatMemberHandler(my_chat_member))


# --- Webhook Route ---
@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handles incoming webhook requests from Telegram."""
    try:
        json_data = request.get_json()
        logger.info(f"Incoming Update: {json_data}")

        if not json_data:
            logger.error("Invalid JSON data received.")
            return jsonify({'error': 'Invalid JSON data'}), 400

        update = Update.de_json(json_data, application.bot)

        # Process the update.  The application is already initialized.
        await application.process_update(update)

        return 'OK', 200  # Acknowledge receipt to Telegram

    except Exception as e:
        logger.exception("Error processing update:")  # Log the full traceback
        return jsonify({'error': 'Internal Server Error'}), 500

# --- Startup and Shutdown Hooks (VERY IMPORTANT) ---

@app.before_first_request
async def startup_event():
    """Initializes the Telegram bot application before handling the first request."""
    logger.info("Initializing Telegram application...")
    await application.initialize()
    # Set the webhook URL *here*, after initialization.  This ensures
    # the bot is ready to receive updates.
    webhook_url = f'{os.getenv("RENDER_EXTERNAL_URL")}/webhook'  # Use Render's URL
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

@app.after_request
async def after_request_callback(response):
    """Ensures all background tasks are finished before returning the response."""
    await application.update_queue.join()
    return response

@app.teardown_appcontext
async def shutdown_event(exception=None):
    """Shuts down the Telegram bot application when the Flask app shuts down."""
    logger.info("Shutting down Telegram application...")
    await application.shutdown()

# --- Run the App (for development) ---
if __name__ == '__main__':
    # For development only! Use Gunicorn or uWSGI in production.
    app.run(host='0.0.0.0', port=10000, debug=False)
