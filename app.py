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

# --- Telegram Bot Application ---
#  Initialize the application *outside* the webhook function.
application = ApplicationBuilder().token(TOKEN).build()

# --- Telegram Bot Handlers ---

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

# --- Register Handlers ---
# It's cleaner to register handlers *before* defining the webhook.
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

        # Use await directly to process the update.
        await application.process_update(update)

        return 'OK', 200  # Acknowledge receipt to Telegram

    except Exception as e:
        logger.exception("Error processing update:")  # Log the full traceback
        return jsonify({'error': 'Internal Server Error'}), 500  # Return a 500 error


# --- Run the App (for development) ---
if __name__ == '__main__':
    #  For development only! Use Gunicorn or uWSGI in production.
    app.run(host='0.0.0.0', port=10000, debug=False) #debug should be false

    # --- Example of how to set the webhook (IMPORTANT!) ---
    #   You'll need to run this *once* (or whenever your server's
    #   public URL changes).  You can do this in a separate script,
    #   or you can uncomment the lines below and run this script *once*.
    #   Replace 'YOUR_SERVER_ADDRESS' with your actual server address.
    #
    # async def set_webhook_url():
    #     bot = Bot(TOKEN)
    #     webhook_url = f'https://YOUR_SERVER_ADDRESS/webhook'  # Your server's URL
    #     result = await bot.set_webhook(url=webhook_url)
    #     if result:
    #         print(f"Webhook set successfully to {webhook_url}")
    #     else:
    #         print("Failed to set webhook.")
    #
    # asyncio.run(set_webhook_url())
