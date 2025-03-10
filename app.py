from flask import Flask, request, jsonify
import logging
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, ApplicationBuilder
from telegram.ext import filters  # Updated import for filters

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize your bot with the token
TOKEN = '7565757922:AAHTCgAKxFYxl495Rr8l-ROr4W5BVdyiNkk'
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
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))  # Updated filters usage

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
        application.process_update(update)

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    # Start the Flask app on port 10000
    app.run(host='0.0.0.0', port=10000)
