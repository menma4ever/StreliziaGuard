from telegram import Update, ChatPermissions
from telegram import ChatPermissions
from telegram.ext import ContextTypes
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,    
    ContextTypes,
)
import logging
import time
import re
from better_profanity import profanity
from keep_alive import keep_alive
keep_alive()


# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialize the profanity filter
profanity.load_censor_words()

# Strelizia's tone and style for bot responses
def strelizia_response(text):
    return f"💫 Strelizia: {text}"

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        strelizia_response(
            "I am Strelizia, the protector of this domain. I will ensure order and safety here. Call upon me when needed."
        )
    )

# Mute handler
# Mute handler for admins only
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("Only admins can mute users.")
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            strelizia_response(
                "To mute someone, reply to their message and specify the duration (e.g., '1 minute', '1 hour')."
            )
        )
        return

    try:
        # Parse duration
        duration_text = " ".join(context.args).lower()
        user_id = update.message.reply_to_message.from_user.id
        if "m" in duration_text:
            duration = int(duration_text.split()[0]) * 60
        elif "h" in duration_text:
            duration = int(duration_text.split()[0]) * 3600
        elif "d" in duration_text:
            duration = int(duration_text.split()[0]) * 86400
        else:
            raise ValueError("Invalid time format")

        until_date = int(time.time() + duration)
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )

        await update.message.reply_text(
            strelizia_response(
                f"💫 Strelizia has muted @{update.message.reply_to_message.from_user.username} for {duration_text}. Order must be maintained."
            )
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            strelizia_response(
                "I couldn't understand the time duration. Use formats like '1 m = minute', '5 m = minutes', '1 h = hour', or '1 d = day'."
            )
        )

# Unmute handler for admins only
# Unmute handler for admins only
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("Only admins can unmute users.")
        )
        return

    # If the message is a reply, unmute the user from the reply
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.username
    else:
        # If the message contains a username, extract the username from the command
        if len(context.args) == 1 and context.args[0].startswith('@'):
            username = context.args[0][1:]  # remove the '@' symbol
            
            # Try fetching the user by username using get_chat_member
            try:
                user = await context.bot.get_chat_member(chat_id, username)
                user_id = user.user.id
            except Exception as e:
                # Log the exception and send error feedback
                logger.error(f"Error finding user @{username}: {str(e)}")
                await update.message.reply_text(
                    strelizia_response(f"Error finding user @{username}: {str(e)}")
                )
                return
        else:
            await update.message.reply_text(
                strelizia_response("Please reply to a user's message or specify a username with '@'.")
            )
            return

    # Ensure the bot is not unmuting itself
    if user_id == context.bot.id:
        await update.message.reply_text(
            strelizia_response("I cannot unmute myself. Please choose another user.")
        )
        return

    # Check if the user is part of the chat before attempting to unmute
    try:
        user_member = await context.bot.get_chat_member(chat_id, user_id)
        if user_member.status in ['left', 'kicked']:
            await update.message.reply_text(
                strelizia_response(f"User @{username} is not part of the chat.")
            )
            return
    except Exception as e:
        await update.message.reply_text(
            strelizia_response(f"Error checking user status: {str(e)}")
        )
        return

    # Unmute the user by adjusting permissions
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(
            strelizia_response(
                f"💫 @{username} has been unmuted! The chat is open for them now."
            )
        )
    except Exception as e:
        logger.error(f"Failed to unmute user: {e}")
        await update.message.reply_text(
            strelizia_response("There was an issue while unmuting the user. Please try again.")
        )




# Ban handler
# Ban handler
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(
            strelizia_response(
                "To ban someone, reply to their message with the /ban command."
            )
        )
        return
    
    # Check if the user issuing the command is an admin
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response(
                "Only admins can ban users."
            )
        )
        return

    # Get the user being banned
    banned_user_id = update.message.reply_to_message.from_user.id
    banned_username = update.message.reply_to_message.from_user.username
    
    # Ban the user from the chat (this removes them and prevents them from rejoining)
    await context.bot.ban_chat_member(
        chat_id=chat_id,
        user_id=banned_user_id
    )

    await update.message.reply_text(
        strelizia_response(
            f"💫 Strelizia has permanently banned @{banned_username}. The domain is now safer."
        )
    )


# Profanity detection and message deletion
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    # Check if the message contains profane words
    if profanity.contains_profanity(message_text):
        # Delete the message
        await update.message.delete()

        # Log the action
        logger.info(f"Deleted a message from {update.message.from_user.username} due to profanity.")

# Advertisement detection
async def handle_advertisement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Check for common ad patterns
    ad_patterns = [
        r"http[s]?://",  # Links (e.g., http://, https://)
        r"www\.",        # URLs starting with www
    ]

    if any(re.search(pattern, message) for pattern in ad_patterns):
        await update.message.delete()
        await update.message.reply_text(
            strelizia_response(
                "💫 Strelizia has removed an advertisement. Stay focused on the purpose of this group."
            )
        )

# Spam detection
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if update.message.text.isupper():
        await update.message.delete()
        await update.message.reply_text(
            strelizia_response(
                "💫 Excessive shouting is not permitted. Maintain decorum."
            )
        )

# Main function
async def main():
    # Replace 'YOUR_BOT_TOKEN' with your bot's API token from BotFather
    application = Application.builder().token("8175120417:AAHqwpE5iMvTibJxZu2atlw_gC4Y60Kdki8").build()
    keep_alive()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mute", mute_user))  # Mute command
    application.add_handler(CommandHandler("unmute", unmute_user))  # Unmute command
    application.add_handler(CommandHandler("ban", ban_user))    # Ban command
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )  # Profanity handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_advertisement)
    )  # Advertisement detection
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spam)
    )  # Spam handler

    await application.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    # Apply nest_asyncio to handle nested event loops
    nest_asyncio.apply()

    # Run the main coroutine
    asyncio.run(main())
