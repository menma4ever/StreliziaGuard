from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, ContextTypes
import logging
logger = logging.getLogger(__name__)
import time
import re
from better_profanity import profanity
from datetime import datetime, timedelta, timezone
import json
import random
from telegram.error import BadRequest
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from collections import Counter
import os
from telegram import Bot
import asyncio

from keep_alive import keep_alive



try:
    loop = asyncio.get_running_loop()
    loop.stop()  # Stop the loop instead of closing it
except RuntimeError:
    pass  # Ignore if there is no running loop



warnings = {}


gif_links = {
    "start": "https://t.me/franxxbotsgarage/3",
    "mute": "https://t.me/franxxbotsgarage/10",
    "ban": "https://t.me/franxxbotsgarage/4 ",
    "warn": "https://t.me/franxxbotsgarage/9",
    "help": "https://t.me/franxxbotsgarage/11",
    "smile": "https://t.me/franxxbotsgarage/13",
    "shout": "https://t.me/franxxbotsgarage/15",}



# Load bad words from the 'bad_words.txt' file
# Define the load_bad_words function before using it

BAD_WORDS_FILE = "bad_words.txt"
bad_words = set()

# Load bad words from the file at startup

def load_bad_words(file_path):
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Creating an empty list.")
        return []  # Return an empty list if the file is missing

    with open(file_path, 'r', encoding='utf-8') as file:
        return [word.strip() for word in file.readlines()]



# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialize the profanity filter
profanity.load_censor_words()

# Store warnings and cooldowns
warnings = {}
cooldowns = {}
admins = [1150034136]  # Example admin IDs

# Strelizia's tone and style for bot responses
def strelizia_response(text):
    return f"💫 Strelizia: {text}"

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await context.bot.send_animation(chat_id=update.effective_chat.id, animation=gif_links["start"])
    await update.message.reply_text(
        "💫 Hello, I am Strelizia, the protector of this realm! How can I assist you today?"
    )




# List of random emojis
emojis = [
    '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '🥲', '😊', '😇', '🙂', 
    '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '🤗', '🤭', '🤫', 
    '🤔', '🫡', '🤨', '😐', '😑', '😶', '🫥', '😏', '😒', '🙄', '😬', '😮‍💨', 
    '🤥', '🫨', '😌', '😔', '😪', '🤤', '😴', '🥴', '😵', '😵‍💫', '🤯', '😎', 
    '🤠', '🥳', '🥺', '😧', '😮', '😲', '😳', '🥵', '🥶', '😱', '😨', '😰', 
    '😥', '😢', '😭', '😤', '😡', '😠', '🤬', '💀', '☠️', '👻', '🤡', '🫣', 
    '😯', '😶‍🌫️', '😈', '👿', '🤩', '🤑', '😵‍😲', '🫠', '😜', '😝', '😛', '🫢'
]






def escape_markdown_v2(text):
    special_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)

def is_admin(user_id, chat_administrators):
    for admin in chat_administrators:
        if admin.user.id == user_id:
            return True
    return False

async def callall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Check if the user is an admin
    if is_admin(user.id, await chat.get_administrators()):
        # Fetch the chat administrators as a proxy for all users
        admins = await context.bot.get_chat_administrators(chat.id)
        member_ids = {admin.user.id for admin in admins}

        call_messages = []
        emoji_line = []

        for member_id in member_ids:
            random_emoji = random.choice(emojis)
            mention = f"[{random_emoji}](tg://user?id={member_id})"
            emoji_line.append(mention)

            if len(emoji_line) == 5:
                call_messages.append(' '.join(emoji_line) + 'ᅠ')
                emoji_line = []

        if emoji_line:
            call_messages.append(' '.join(emoji_line) + 'ᅠ')

        call_message = "\n".join(call_messages) + "\ncall ended"

        # Send the final message
        await update.message.reply_text(call_message, parse_mode='MarkdownV2')

    else:
        await update.message.reply_text("💫 Only administrators can use this command.")






async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)
    
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(strelizia_response("💫 Only the elite administrators can mute others."))
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(strelizia_response("To mute someone, reply to their message and specify the duration (e.g., 'mute 2h', 'mute 5m')."))
        return
    
    try:
        # Parse duration
        if len(context.args) != 1:
            raise ValueError("Invalid time format")
        
        duration_text = context.args[0].lower()
        match = re.match(r"(\d+)([mhd])", duration_text)
        if not match:
            raise ValueError("Invalid time format")
        
        duration_value, duration_unit = match.groups()
        duration_value = int(duration_value)
        
        if duration_unit == 'm':
            duration = duration_value * 60
        elif duration_unit == 'h':
            duration = duration_value * 3600
        elif duration_unit == 'd':
            duration = duration_value * 86400
        else:
            raise ValueError("Invalid time format")
        
        user_id = update.message.reply_to_message.from_user.id
        until_date = int(time.time() + duration)

        # Prevent muting the bot or administrators
        if user_id == context.bot.id:
            await update.message.reply_text(strelizia_response("💫 I cannot mute myself. I am Strelizia, the protector of this realm!"))
            return

        # Prevent muting administrators
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ['administrator', 'creator']:
            await update.message.reply_text(strelizia_response("💫 I cannot mute an administrator. Even Strelizia must show respect to them!"))
            return

        # Send animation before muting
        await context.bot.send_animation(chat_id=update.effective_chat.id, animation=gif_links["mute"])

        # Mute the user
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )

        # Send confirmation message
        await update.message.reply_text(strelizia_response(f"💫 Strelizia has muted @{update.message.reply_to_message.from_user.username} for {duration_text}. Order must be maintained."))

    except (IndexError, ValueError):
        await update.message.reply_text(strelizia_response("I couldn't understand the time duration. Use formats like 'mute 2m', 'mute 1h', or 'mute 1d'."))



# Unmute handler for admins only
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("💫 Only the elite administrators can unmute others.")
        )
        return

    # If the message is a reply, unmute the user from the reply
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.username
    else:
        # If the message contains a username, extract the username from the command
        if len(context.args) == 1 and context.args[0].startswith('@'):
            username = context.args[0][1:]  # Remove the '@' symbol

            try:
                # Get all members of the chat and attempt to match by username
                chat_members = await context.bot.get_chat_administrators(chat_id)
                matched_member = next(
                    (member for member in chat_members if member.user.username == username), None
                )

                if matched_member:
                    user_id = matched_member.user.id
                else:
                    # If user is not in admin list, directly fetch them by username
                    member = await context.bot.get_chat_member(chat_id, username)
                    user_id = member.user.id

            except Exception as e:
                logger.error(f"Error finding user @{username}: {str(e)}")
                await update.message.reply_text(
                    strelizia_response(
                        f"Error finding user @{username}: Make sure the user is in this chat and has interacted with the bot."
                    )
                )
                return
        else:
            await update.message.reply_text(
                strelizia_response(
                    "Please reply to a user's message or specify a username with '@'."
                )
            )
            return

    # Ensure the bot is not unmuting itself
    if user_id == context.bot.id:
        await update.message.reply_text(
            strelizia_response("💫 I cannot unmute myself. Only the worthy can command such actions.")
        )
        return

    # Unmute the user by adjusting permissions
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ['administrator', 'creator']:
            await update.message.reply_text(
                strelizia_response("💫 I cannot unmute an administrator. Respect the chain of command!")
            )
            return

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

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(strelizia_response("To ban someone, reply to their message with the /ban command."))
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(strelizia_response("💫 Only admins can ban users."))
        return

    banned_user_id = update.message.reply_to_message.from_user.id
    banned_username = update.message.reply_to_message.from_user.username

    if banned_user_id == context.bot.id:
        await update.message.reply_text(strelizia_response("💫 I cannot ban myself. The protector cannot fall!"))
        return

    if banned_user_id == user_id:
        await update.message.reply_text(strelizia_response("💫 I cannot ban you. You are too valuable to the cause!"))
        return

    try:
        logger.info(f"Banning user {banned_username} ({banned_user_id}) from chat {chat_id}")
        await context.bot.ban_chat_member(chat_id, banned_user_id)
        await context.bot.send_animation(
            chat_id=update.effective_chat.id,
            animation=gif_links["ban"]
        )
        await update.message.reply_text(strelizia_response(f"💫 @{banned_username} has permanently been banned."))
    except Exception as e:
        logger.error(f"Failed to ban user {banned_username} ({banned_user_id}) in chat {chat_id}. Error: {str(e)}")
        await update.message.reply_text(strelizia_response(f"💫 Failed to ban @{banned_username}. Error: {str(e)}"))







# Warn user function
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)
    
    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(strelizia_response("💫 Only the elite administrators can warn others."))
        return
    
    if not update.message.reply_to_message and len(context.args) != 1:
        await update.message.reply_text(strelizia_response("To warn someone, reply to their message or provide their username."))
        return

    # Get the user to warn (either from a reply or from a username argument)
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.username
    else:
        username = context.args[0][1:]  # Remove the '@' symbol from the username argument
        try:
            member = await context.bot.get_chat_member(chat_id, username)
            user_id = member.user.id
        except Exception as e:
            await update.message.reply_text(strelizia_response(f"💫 Could not find user {username}."))
            return

    # Track warnings for the user
    if user_id not in warnings:
        warnings[user_id] = 0
    warnings[user_id] += 1

    # Send the group warning notification with GIF
    try:
        await context.bot.send_animation(
            chat_id=update.effective_chat.id,
            animation=gif_links["warn"]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=strelizia_response(f"💫 @{username} has received a warning! This is their {warnings[user_id]} warning. Be mindful of your behavior!")
        )
    except Exception as e:
        await update.message.reply_text(strelizia_response(f"💫 Failed to send group notification. Error: {str(e)}"))

    # If the user reaches 3 warnings, ban them automatically
    if warnings[user_id] >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            warnings[user_id] = 0  # Reset warning count after banning
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_links["ban"]
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=strelizia_response(f"💫 @{username} has been banned due to accumulating 3 warnings! Bye bye!")
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=strelizia_response(f"💫 Failed to ban @{username}. Error: {str(e)}")
            )







# Profanity detection and message handling with warning system
# Updated profanity detection and message deletion with Strelizia's style# Define ad patterns globally at the top
import re
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# Set up logging
logger = logging.getLogger(__name__)

# Initialize warnings dictionary
warnings = {}

# Define ad patterns
ad_patterns = [
    r"http[s]?://",  
    r"www\.",          
    r"\.[a-z]{2,}(?:\/[^\s]*)?",  
]

# Define positive behavior keywords
positive_keywords = ["thanks", "please", "helpful", "good job", "rahmat", "iltimos", "yordam", "mehribon"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return  # Exit if there is no message to process

    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    chat_id = update.message.chat_id
    group_chat_id = 2262322366  # Replace with your target group ID where media should be forwarded

    message_text = update.message.text or ""

    is_forwarded = (
        getattr(update.message, "forward_origin", None) is not None or
        getattr(update.message, "forward_sender_name", None) is not None or
        getattr(update.message, "forward_from_chat", None) is not None or
        hasattr(update.message, "forward_date")  # ✅ This ensures only actual forwarded messages get detected
    )
    if is_forwarded:
        try:
            await update.message.delete()
            await context.bot.send_animation(chat_id=chat_id, animation=gif_links["warn"])
            await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, forwarded messages are not allowed!")
        except BadRequest as e:
            logger.error(f"Failed to delete forwarded message: {e}")
        return  # **Stop further processing**
    has_media = (
        update.message.photo or 
        update.message.video or 
        update.message.audio or 
        update.message.document
    )

    try:
        # 🚨 **Forward Media Messages to Group**
        if has_media and is_forwarded:
            try:
                await update.message.forward(group_chat_id)  # Forward media to the group
                return  # Stop further processing for media messages
            except BadRequest as e:
                logger.error(f"Failed to forward media: {e}")
                return

        # 🚨 **Delete Forwarded Text Messages (Including Channels)**
        if is_forwarded:
            try:
                await update.message.delete()  # Delete forwarded message
                await context.bot.send_animation(chat_id=chat_id, animation=gif_links["warn"])
                await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, don't forward messages.")
            except BadRequest as e:
                logger.error(f"Failed to delete message or notify: {e}")
            return

        # 🚨 **Check for inappropriate language**
        if contains_uzbek_profanity(message_text) or profanity.contains_profanity(message_text):
            try:
                await update.message.delete()
                await context.bot.send_animation(chat_id=chat_id, animation=gif_links["warn"])
                await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, don't use bad words.")
            except BadRequest as e:
                logger.error(f"Failed to delete message or notify: {e}")
            return

        # 🚨 **Check for advertisements and links**
        elif re.search(r"https://t\.me/[a-zA-Z0-9_]+", message_text.lower()) or \
             any(re.search(pattern, message_text.lower()) for pattern in ad_patterns):
            try:
                await update.message.delete()
                await context.bot.send_animation(chat_id=chat_id, animation=gif_links["warn"])
                await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, don't post links or advertisements.")
            except BadRequest as e:
                logger.error(f"Failed to delete message or notify: {e}")
            return

        # 🚨 **Handle uppercase messages**
        elif message_text.isupper():
            try:
                await update.message.delete()
                await context.bot.send_animation(chat_id=chat_id, animation=gif_links["warn"])
                await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, don't shout.")
            except BadRequest as e:
                logger.error(f"Failed to delete message or notify: {e}")
            return

        # 🎉 **Handle positive behavior (e.g., kind words)**
        elif any(keyword in message_text.lower() for keyword in positive_keywords):
            try:
                await context.bot.send_animation(chat_id=chat_id, animation=gif_links["smile"])
                await context.bot.send_message(chat_id=chat_id, text=f"💫 @{username}, your kindness is appreciated!")
            except BadRequest as e:
                logger.error(f"Failed to send animation or message: {e}")
            return

        # 🚀 **Now, check for excessive stickers**
        await restrict_sticker_spam(update, context)

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")






import time
import asyncio
from collections import defaultdict
from telegram import ChatPermissions

# Track sticker messages per user
sticker_tracking = defaultdict(lambda: [])

async def restrict_sticker_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    chat_id = update.message.chat_id

    # 🚀 **Detect Stickers**
    is_sticker = update.message.sticker is not None

    if is_sticker:
        current_time = time.time()

        # Track user's sticker activity
        sticker_tracking[user_id].append(current_time)

        # Remove old timestamps beyond 3 seconds
        sticker_tracking[user_id] = [t for t in sticker_tracking[user_id] if current_time - t <= 3]

        # 🚨 **Check if the user has sent more than 6 stickers within 3 seconds**
        if len(sticker_tracking[user_id]) > 6:
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True, 
                        can_send_media_messages=True,
                        can_send_other_messages=False,  # Disable stickers
                        can_add_web_page_previews=True
                    )
                )

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"💫 @{username}, you've sent too many stickers! Sticker permissions revoked for 1 hour."
                )

                # 🚀 **Schedule permission restoration after 1 hour**
                async def restore_permissions():
                    await asyncio.sleep(3600)  # Wait 1 hour
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,  # Restore stickers
                            can_add_web_page_previews=True
                        )
                    )
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"💫 @{username}, sticker permissions restored!"
                    )

                asyncio.create_task(restore_permissions())

            except Exception as e:
                logger.error(f"Failed to restrict sticker permissions: {e}")








def load_bad_words(file_path: str):
    """
    Load bad words from a text file into a list.
    Each line in the file should contain one bad word.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        bad_words = [line.strip().lower() for line in file.readlines()]
    return bad_words

uzbek_bad_words = load_bad_words('bad_words.txt')



ADMIN_USER_ID = 1150034136  # Replace with target user ID
BOT_TOKEN = "8175120417:AAHqwpE5iMvTibJxZu2atlw_gC4Y60Kdki8"

async def send_bad_words_file():
    bot = Bot(token=BOT_TOKEN)

    while True:
        try:
            await bot.send_document(
                chat_id=ADMIN_USER_ID,
                document=open("bad_words.txt", "rb"),
                caption="💫 Here is the updated bad words list."
            )
            print("Bad words file sent successfully!")  # Debugging log

        except Exception as e:
            print(f"Error sending file: {e}")

        await asyncio.sleep(24 * 60 * 60)  # Wait for 24 hours before sending again

# Run the background task

import urllib.request

async def upload_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id

    # Ensure only user 1150034136 can use this command in private chat
    if chat_id != user_id_admin or user_id_admin != 1150034136:
        return  # Exit without processing

    # Check if the user replied to a document
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("💫 Please reply to a valid .txt file with /upload_bad_words.")
        return

    document = update.message.reply_to_message.document

    # Ensure the file is a text file
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("💫 Only .txt files are allowed!")
        return

    try:
        # Get file path from Telegram API
        file = await context.bot.get_file(document.file_id)
        file_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file.file_path}"

        # Download the file and replace bad_words.txt
        import requests
        response = requests.get(file_url)

        if response.status_code == 200:
            with open("bad_words.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            await update.message.reply_text("💫 Bad words list has been successfully updated!")

            # 🔄 Refresh bad words in memory
            global bad_words
            bad_words = set(load_bad_words("bad_words.txt"))

        else:
            await update.message.reply_text("💫 Failed to retrieve the file from Telegram.")

    except Exception as e:
        logger.error(f"Error updating bad words file: {str(e)}")
        await update.message.reply_text("💫 An error occurred while updating the bad words list. Please try again.")


def contains_uzbek_profanity(text: str) -> bool:
    """
    Check if the input text contains any words from the custom bad words library.
    """
    text = text.lower()  # Convert the text to lowercase for case-insensitive checking
    for word in uzbek_bad_words:
        if word in text:
            return True
    return False

async def add_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id

    # Ensure the command only works for the specified admin user in private chat
    if chat_id != user_id_admin or user_id_admin != 1150034136:
        return  # Exit without processing

    # Check if bad words are provided
    if len(context.args) < 1:
        await update.message.reply_text("💫 Please provide at least one bad word to add.")
        return

    bad_words_list = [word.strip() for word in context.args if word.strip()]  # Clean words

    try:
        # Read existing bad words
        with open(BAD_WORDS_FILE, 'r') as f:
            existing_words = set(line.strip() for line in f.readlines())

        new_words = [word for word in bad_words_list if word not in existing_words]

        # Append only new words to the file
        with open(BAD_WORDS_FILE, 'a') as f:
            for word in new_words:
                f.write(word + "\n")

        if new_words:
            await update.message.reply_text(f"💫 The following bad words have been added: {', '.join(new_words)}.")

            # 🔄 **Reload bad words into memory instantly**
            global bad_words
            bad_words = set(load_bad_words(BAD_WORDS_FILE))  # Refresh bad words without restarting

        else:
            await update.message.reply_text("💫 No new bad words were added as they already exist in the list.")

    except Exception as e:
        logger.error(f"Error adding bad words: {str(e)}")
        await update.message.reply_text("💫 There was an error while adding the bad words. Please try again.")


async def import_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id

    # Ensure only user 1150034136 can use this command
    if user_id_admin != 1150034136:
        return  # Exit without processing

    try:
        # Check if the bad_words.txt file exists and isn't empty
        file_path = 'bad_words.txt'
        with open(file_path, 'r') as f:
            if not f.read().strip():
                await update.message.reply_text("💫 The bad words list is currently empty.")
                return

        # Send the file as a document
        await context.bot.send_document(
            chat_id=chat_id,
            document=open(file_path, 'rb'),
            caption="💫 Here is the bad words list."
        )

    except FileNotFoundError:
        await update.message.reply_text("💫 The bad words file does not exist. Please add words first.")
    except Exception as e:
        logger.error(f"Error sending bad words file: {str(e)}")
        await update.message.reply_text("💫 An error occurred while sending the bad words list. Please try again.")




# Admin profanity handling
async def handle_admin_profane_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id

    # Check if the user issuing the message is an admin
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status in ['administrator', 'creator']:
        # Delete the admin's message
        await update.message.delete()

        # Send a message in Strelizia's character
        await update.message.reply_text(
            strelizia_response(f"💫 @{update.message.from_user.username}, do you think you can act this way just because you're an admin? Even Strelizia must respect the chain of command!")
        )




# Spam detection



# Advertisement detection
# Advertisement detection with improved patterns
# Advertisement detection with improved patterns
async def handle_advertisement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Check for common ad patterns, improved regex for better ad detection
    ad_patterns = [
        r"http[s]?://",  # Links (e.g., http://, https://)
        r"www\.",        # URLs starting with www
        r"\b(cheap|sale|discount|buy|offer|limited time)\b",  # Common advertising words
        r"\b(deal|promo|free)\b",  # More advertising words
    ]

    # If any pattern matches, delete the message
    if any(re.search(pattern, message) for pattern in ad_patterns):
        await update.message.delete()
        # Directly address the user with their nickname in Strelizia's tone
        await update.message.reply_text(
            strelizia_response(f"💫 @{update.message.from_user.username}, advertisement is not allowed here. Keep the chat on topic!")
        )



# Profanity detection and message deletion with Strelizia's style


# Handle positive behavior
positive_keywords = [
    "thanks", "good job", "nice",
    "rahmat", "iltimos", "yordam", 
    "mehribon", 
    # More Uzbek (Latin 
    # Uzbek (Cyrillic
    # Russian
    "спасибо", "пожалуйста", "помощь", "хорошая работа", "дружелюбный", "прекрасно", "отлично", "молодец", 
    "вдохновляющий", "добрый", "уважаемый", "благодарный", "спокойствие"
]


# Handle positive behavior
async def handle_positive_behavior(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.lower()
    if any(keyword in message_text for keyword in positive_keywords):
        chat_id = update.message.chat_id  # Get the group chat ID
        
        # Use username if it exists, otherwise fall back to first name
        username = update.message.from_user.username
        first_name = update.message.from_user.first_name
        display_name = username if username else first_name  # Use username or first name
        
        # Send a private message to the user
        await update.message.reply_text(
            strelizia_response(f"💫 @{display_name}, your positive attitude is appreciated! Keep inspiring others in this realm!")
        )

        # Send the commendation to the group
        await context.bot.send_message(
            chat_id=chat_id,
            text=strelizia_response(f"💫 @{display_name} has shown exceptional kindness and positivity. Let's follow their example!")
        )



# Main function
# Help command handler
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when the /help command is issued."""
    await context.bot.send_animation(chat_id=update.effective_chat.id, animation=gif_links["help"])
    help_text = (
        "💫 Strelizia: Greetings, dear user! I am Strelizia, the protector of this realm. "
        "Here are the ways I can assist you:\n\n"
        "1. **/start** - Start interacting with me! I'll welcome you to this realm.\n"
        "2. **/mute [duration]** - Mute a user for a specified duration (e.g., 'mute 2h', 'mute 5m').\n"
        "3. **/unmute [username]** - Unmute a user, or reply to their message.\n"
        "4. **/warn [username]** - Warn a user for inappropriate behavior or language.\n"
        "5. **/ban [username]** - Ban a user from the chat after multiple warnings or violations.\n"
        "6. **Message with profanity** - I will delete any messages with profane language and warn you.\n"
        "7. **Advertisement detection** - I will delete any advertisements and remind you to keep the chat on topic.\n"
        "8. **Spam detection** - If you shout in all caps, I will delete your message and remind you to maintain decorum.\n"
        "9. **Positive behavior** - I appreciate kindness and will acknowledge your good behavior.\n\n"
        "💫 If you are an admin, you can also mute, unmute, warn, or ban users. I will respect your decisions as long as they are just!"
    )
    await update.message.reply_text(strelizia_response(help_text))



# Main function
import nest_asyncio
nest_asyncio.apply()  # Allows nested event loops

from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

async def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Add your handlers here
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("addbadwords", add_bad_words))
    application.add_handler(CommandHandler("import", import_bad_words))
    application.add_handler(CommandHandler("callall", callall))
    application.add_handler(CommandHandler("upload", upload_bad_words))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_advertisement))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_positive_behavior))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_profane_message))

    # Background task (if needed)
    asyncio.create_task(send_bad_words_file())

    # Run the bot without closing the event loop when done
    await application.run_polling(close_loop=False)

if __name__ == "__main__":    
    # Load additional resources if required
    bad_words = load_bad_words("bad_words.txt")  # Load bad words list
    keep_alive()  # Keeps the service running if applicable

    # Start the main asynchronous function with asyncio.run
    asyncio.run(main())
