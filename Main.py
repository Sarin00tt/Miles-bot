import os
import logging
import asyncio
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler
)

# Constants for registration
NAME, GENDER, PHOTO, MODE = range(4)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to MILES.\n"
        "For you from a mile away.\n"
        "I am greeting you on behalf of my creator, Null Island.\n"
        "What is your name?"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    keyboard = [[InlineKeyboardButton("Male", callback_data='Male'), InlineKeyboardButton("Female", callback_data='Female')]]
    await update.message.reply_text("What is your gender?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This assumes button click logic; for simplicity in text, we capture the reply
    gender = update.callback_query.data
    context.user_data['gender'] = gender
    await update.callback_query.message.reply_text("Upload a photo (or type skip to continue without one).")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Registration completion logic here...
    await update.message.reply_text("Registration complete. You are now ready to connect.")
    return ConversationHandler.END

# Queue logic for heterosexual matching
async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Add logic here to check if opposite gender queue is occupied
    # If male, pop from female queue; if female, pop from male queue
    await update.message.reply_text("Searching for a partner...")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "No man is an island. Connect across oceans, a mile away.\n\n"
        "Key Commands:\n"
        "/search - Find a partner\n"
        "/next - Find better\n"
        "/stop - Stop current dialog\n"
        "/help - How to use the bot\n"
        "Remember: 5 reports will result in a 5-day ban."
    )

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT, get_gender)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", find_partner))

    application.run_polling()
  
