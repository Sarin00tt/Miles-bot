import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler, CallbackQueryHandler
)

# Constants for registration
NAME, GENDER, PHOTO = range(3)

# Global storage for matching
waiting_queue = []
active_pairs = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to MILES. What is your name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    keyboard = [[InlineKeyboardButton("Male", callback_data='Male'), InlineKeyboardButton("Female", callback_data='Female')]]
    await update.message.reply_text("What is your gender?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['gender'] = query.data
    await query.message.reply_text("Upload a photo (or type skip).")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration complete. Use /search to connect.")
    return ConversationHandler.END

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        await update.message.reply_text("Already in a chat. Use /stop to leave.")
        return
    if waiting_queue:
        partner_id = waiting_queue.pop(0)
        active_pairs[user_id] = partner_id
        active_pairs[partner_id] = user_id
        await update.message.reply_text("Partner found! Say hello.")
        await context.bot.send_message(chat_id=partner_id, text="Partner found! Say hello.")
    else:
        waiting_queue.append(user_id)
        await update.message.reply_text("Searching for a partner...")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs.pop(user_id)
        active_pairs.pop(partner_id, None)
        await update.message.reply_text("Disconnected.")
        await context.bot.send_message(chat_id=partner_id, text="Partner disconnected.")
    else:
        await update.message.reply_text("You aren't in a chat.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/search - Find partner\n/stop - Stop chat\n/help - Commands")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        await context.bot.send_message(chat_id=active_pairs[user_id], text=update.message.text)
    else:
        await update.message.reply_text("Type /search to find a partner.")

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [CallbackQueryHandler(get_gender)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: None)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", find_partner))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()
    
