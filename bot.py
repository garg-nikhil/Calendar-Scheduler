import os
import logging
import time
import requests
import dateparser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load from GitHub Secrets (via GitHub Actions env vars)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAS_WEBHOOK_URL = os.getenv("GAS_WEBHOOK_URL")

# Simple help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your calendar event like: `Meeting with John tomorrow at 4pm`")

# Handle messages with natural language
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.chat_id
    logger.info(f"Received from {user_id}: {user_message}")

    # Parse date/time
    parsed_dt = dateparser.parse(user_message)
    if not parsed_dt:
        await update.message.reply_text("Sorry, I couldn't understand the date/time. Try again.")
        return

    # Prepare payload for Apps Script
    payload = {
        "eventText": user_message,
        "datetime": parsed_dt.isoformat()
    }

    try:
        response = requests.post(GAS_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            await update.message.reply_text("✅ Event created on your Google Calendar!")
        else:
            logger.error(f"GAS response: {response.status_code} - {response.text}")
            await update.message.reply_text("⚠️ Failed to create event. Try again later.")
    except Exception as e:
        logger.exception("Error while calling GAS webhook")
        await update.message.reply_text("❌ Error occurred while creating event.")

# Main runner
async def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling (but only for a short time)
    logger.info("Bot polling started (limited time)...")
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.sleep(60)  # Poll only for 60 seconds
        await app.updater.stop()
        await app.stop()
    logger.info("Bot polling stopped.")

# Entrypoint
if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())
