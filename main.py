import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler, CallbackQueryHandler
)

# Constants for states
NAME, GENDER, PHOTO, MODE_SELECT = range(4)

# Global storage for matching
waiting_queue = []
active_pairs = {}
user_genders = {}

# Logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('registered'):
        await update.message.reply_text("You are already registered! Use /edit_profile to update.")
        return ConversationHandler.END
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
    gender = query.data
    user_genders[update.effective_user.id] = gender
    context.user_data['gender'] = gender
    await query.message.reply_text("Upload a photo (or type 'skip').")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or (update.message.text and update.message.text.lower() == 'skip'):
        context.user_data['registered'] = True
        keyboard = [[InlineKeyboardButton("Hunting (Live)", callback_data='hunt'), InlineKeyboardButton("Fishing (Browse)", callback_data='fish')]]
        await update.message.reply_text("Registered! Do you want to Hunt or Fish?", reply_markup=InlineKeyboardMarkup(keyboard))
        return MODE_SELECT
    await update.message.reply_text("Please upload a photo, or type 'skip'.")
    return PHOTO

async def mode_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'hunt':
        await find_partner(update, context)
    else:
        await query.message.reply_text("Fishing mode enabled. You can now browse profiles.")
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
        await context.bot.send_message(chat_id=user_id, text="Partner found! Say hello.")
        await context.bot.send_message(chat_id=partner_id, text="Partner found! Say hello.")
    else:
        waiting_queue.append(user_id)
        await context.bot.send_message(chat_id=user_id, text="Searching for a partner...")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs.pop(user_id)
        active_pairs.pop(partner_id, None)
        await update.message.reply_text("You disconnected. Happy Hunting!")
        await context.bot.send_message(chat_id=partner_id, text="Your partner left. Happy Hunting!")
    else:
        await update.message.reply_text("You aren't in a chat.")

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['registered'] = False
    await update.message.reply_text("Profile reset. Type /start to update.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs[user_id]
        gender = user_genders.get(user_id, 'Person')
        typing_msg = "Man is typing..." if gender == 'Male' else "Woman is typing..."
        await context.bot.send_message(chat_id=partner_id, text=typing_msg)
        await asyncio.sleep(0.5)
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("Type /search to find a partner.")

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables.")
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [CallbackQueryHandler(get_gender)],
            PHOTO: [MessageHandler(filters.PHOTO | filters.TEXT, get_photo)],
            MODE_SELECT: [CallbackQueryHandler(mode_select)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: None)],
    )
    
    application.add_handler(conv)
    application.add_handler(CommandHandler("search", find_partner))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("edit_profile", edit_profile))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    application.run_polling()
    
