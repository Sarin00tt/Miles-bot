import os
import asyncio
import logging
from telegram import Update, constants
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, ConversationHandler
)

# Define states for the profile conversation
NAME, AGE, INTERESTS, BIO, CONFIRM = range(5)

# In-memory storage (for persistence across restarts, use a database later)
waiting_queue = []
active_pairs = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to MILES. Let's set up your profile. What is your name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Nice to meet you! How old are you?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("What are your interests? (e.g., Gaming, Music, Hiking)")
    return INTERESTS

async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['interests'] = update.message.text
    await update.message.reply_text("Write a short quote or bio about yourself:")
    return BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bio'] = update.message.text
    profile = (f"👤 *Your Profile*\n\n"
               f"Name: {context.user_data['name']}\n"
               f"Age: {context.user_data['age']}\n"
               f"Interests: {context.user_data['interests']}\n"
               f"Bio: {context.user_data['bio']}")
    await update.message.reply_text(profile, parse_mode=constants.ParseMode.MARKDOWN)
    await update.message.reply_text("Is this correct? (Type 'yes' to finish, 'no' to restart)")
    return CONFIRM

async def confirm_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'yes':
        context.user_data['registered'] = True
        await update.message.reply_text("Profile saved! Type /search to start hunting.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Let's restart. What is your name?")
        return NAME

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('registered'):
        await update.message.reply_text("You aren't registered. Type /start.")
        return
    data = context.user_data
    profile = (f"👤 *Your Profile*\n\nName: {data['name']}\nAge: {data['age']}\n"
               f"Interests: {data['interests']}\nBio: {data['bio']}")
    await update.message.reply_text(profile, parse_mode=constants.ParseMode.MARKDOWN)

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        await update.message.reply_text("Already in a chat. Use /stop to leave.")
        return
    if waiting_queue:
        partner_id = waiting_queue.pop(0)
        active_pairs[user_id] = partner_id
        active_pairs[partner_id] = user_id
        # Send profiles to each other
        for uid in [user_id, partner_id]:
            p_id = partner_id if uid == user_id else user_id
            p_data = context.application.user_data.get(p_id, {})
            card = (f"👤 *Partner Profile*\nName: {p_data.get('name')}\n"
                    f"Age: {p_data.get('age')}\nInterests: {p_data.get('interests')}\n"
                    f"Bio: {p_data.get('bio')}")
            await context.bot.send_message(chat_id=uid, text=card, parse_mode=constants.ParseMode.MARKDOWN)
            await context.bot.send_message(chat_id=uid, text="Partner found! Say hello.")
    else:
        waiting_queue.append(user_id)
        context.application.user_data[user_id] = context.user_data
        await update.message.reply_text("Searching for a partner...")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs.pop(user_id)
        active_pairs.pop(partner_id, None)
        await update.message.reply_text("Disconnected. Happy Hunting!")
        await context.bot.send_message(chat_id=partner_id, text="Your partner left. Happy Hunting!")
    else:
        await update.message.reply_text("You aren't in a chat.")

async def skip_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs.pop(user_id)
        active_pairs.pop(partner_id, None)
        await update.message.reply_text("Skipping...")
        await context.bot.send_message(chat_id=partner_id, text="Your partner skipped you! Finding a new match...")
        waiting_queue.extend([user_id, partner_id])
        await find_partner(update, context)
    else:
        await update.message.reply_text("Not in a chat.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.[span_4](start_span)effective_user.id
    if user_id in active_pairs:
        partner_id = active_pairs[user_id]
        # Professional typing indicator[span_4](end_span)
        await context.bot.send_chat_action(chat_id=partner_id, action=constants.ChatAction.TYPING)
        await asyncio.sleep(1.2)
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("Type /search to hunt.")

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_profile)],
        },
        fallbacks=[CommandHandler("stop", stop_chat)],
    )
    
    app.add_handler(conv)
    app.add_handler(CommandHandler("search", find_partner))
    app.add_handler(CommandHandler("next", skip_partner))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.run_polling()
        
