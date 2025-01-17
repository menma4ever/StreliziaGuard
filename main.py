from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
logger = logging.getLogger(__name__)
import time
import re
from better_profanity import profanity
from datetime import datetime, timedelta
import json
from telegram.error import BadRequest
from keep_alive import keep_alive


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
def load_bad_words(file_path: str):
    """
    Load bad words from a text file into a list.
    Each line in the file should contain one bad word.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        bad_words = [line.strip().lower() for line in file.readlines()]
    return bad_words

# Now you can safely call it
uzbek_bad_words = load_bad_words('bad_words.txt')


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
admins = [123456789]  # Example admin IDs

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
ad_patterns = [
    r"http[s]?://",  # Links (e.g., http://, https://)
    r"www\.",        # URLs starting with www
    r"\b(cheap|sale|discount|buy|offer|limited time)\b",  # Common advertising words
    r"\b(deal|promo|free)\b",  # More advertising words
]

# Updated handle_message function
# Updated handle_message function
import re
from telegram.error import BadRequest

# Profanity detection and message handling with warning system
import logging

# Set up logging
logger = logging.getLogger(__name__)





import re

# Define improved ad patterns to catch all potential ad-like behavior
ad_patterns = [
    r"http[s]?://",  # Detect links (http://, https://)
    r"www\.",        # Detect links starting with www
    r"\b(cheap|sale|discount|buy|offer|limited time|deal|promo|free)\b",  # Ads common words
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure the message exists
    if not update.message:
        return  # Exit if there is no message to process

    message_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    chat_id = update.message.chat_id

    # Safely check if the message is forwarded
    is_forwarded = hasattr(update.message, 'forward_from') or hasattr(update.message, 'forward_sender_name')

    try:
        # Initialize warnings if this is the first warning for the user
        if user_id not in warnings:
            warnings[user_id] = 0

        # Check if the message is forwarded
        if is_forwarded:
            await update.message.delete()  # Delete the forwarded message
            await context.bot.send_message(
                chat_id=user_id,
                text=strelizia_response("💫 Forwarded messages are not allowed here. Please send original content."),
            )
            return  # Stop further processing for this message

        # Check if the message contains inappropriate language
        if contains_uzbek_profanity(message_text) or profanity.contains_profanity(message_text):
            await update.message.delete()  # Delete the message
            warnings[user_id] += 1  # Increment the warning count

            if warnings[user_id] == 3:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=strelizia_response(f"💫 @{username}, this is your 3rd and final warning. You’ve been banned.")
                )
                await context.bot.ban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id
                )
                warnings[user_id] = 0
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=strelizia_response(f"💫 @{username}, you’ve used inappropriate language. This is your {warnings[user_id]} warning.")
                )
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_links["shout"]
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=strelizia_response(f"💫 @{username}, you’ve used inappropriate language. This is their {warnings[user_id]} warning. Please be mindful of your language!")
            )
            return  # Stop further processing for this message

        # Check for advertisements and links
        elif re.search(r"https://t\.me/[a-zA-Z0-9_]+", message_text.lower()) or \
             any(re.search(pattern, message_text.lower()) for pattern in ad_patterns):
            await update.message.delete()  # Delete the message with a link or advertisement

            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_links["warn"]
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=strelizia_response(f"💫 @{username}, links or advertisements are not allowed. Keep the chat on topic!")
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=strelizia_response(f"💫 @{username}, your message contained a link or advertisement. Please follow the rules!")
            )
            return  # Stop further processing for this message

        # Handle uppercase messages
        elif message_text.isupper():
            await update.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text=strelizia_response("💫 Excessive shouting is not permitted. Maintain decorum.")
            )
            return  # Stop further processing for this message

        # Handle positive behavior (e.g., kind words)
        elif any(keyword in message_text.lower() for keyword in positive_keywords):
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_links["smile"]
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=strelizia_response(f"💫 @{username if username else update.message.from_user.first_name}, your kindness has been noted. Continue to inspire others!")
            )
            return  # Stop further processing for this message

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")










def load_bad_words(file_path: str):
    """
    Load bad words from a text file into a list.
    Each line in the file should contain one bad word.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        bad_words = [line.strip().lower() for line in file.readlines()]
    return bad_words

uzbek_bad_words = load_bad_words('bad_words.txt')

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
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("💫 Only administrators can add bad words to the list.")
        )
        return

    # Ensure bad words are provided in the command
    if len(context.args) < 1:
        await update.message.reply_text(
            strelizia_response("💫 Please provide at least one bad word to add.")
        )
        return

    bad_words = [word.strip() for word in context.args if word.strip()]  # Clean the words
    try:
        # Open the bad_words.txt file, read existing words, and ensure no duplicates
        with open('bad_words.txt', 'r') as f:
            existing_words = set(line.strip() for line in f.readlines())

        new_words = [word for word in bad_words if word not in existing_words]

        # Append only new words to the file
        with open('bad_words.txt', 'a') as f:
            for word in new_words:
                f.write(word + "\n")

        if new_words:
            await update.message.reply_text(
                strelizia_response(f"💫 The following bad words have been added: {', '.join(new_words)}.")
            )
        else:
            await update.message.reply_text(
                strelizia_response("💫 No new bad words were added as they already exist in the list.")
            )
    except Exception as e:
        logger.error(f"Error adding bad words: {str(e)}")
        await update.message.reply_text(
            strelizia_response("💫 There was an error while adding the bad words. Please try again.")
        )


async def import_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("💫 Only administrators can import the bad words list.")
        )
        return

    try:
        # Check if the bad_words.txt file exists
        file_path = 'bad_words.txt'
        with open(file_path, 'r') as f:
            if not f.read().strip():
                await update.message.reply_text(
                    strelizia_response("💫 The bad words list is currently empty.")
                )
                return

        # Send the file as a document to the chat
        await context.bot.send_document(
            chat_id=chat_id,
            document=open(file_path, 'rb'),
            caption="💫 Here is the bad words list."
        )
    except FileNotFoundError:
        await update.message.reply_text(
            strelizia_response("💫 The bad words file does not exist. Please add words first.")
        )
    except Exception as e:
        logger.error(f"Error sending bad words file: {str(e)}")
        await update.message.reply_text(
            strelizia_response("💫 An error occurred while sending the bad words list. Please try again.")
        )





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
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if update.message.text.isupper():
        await update.message.delete()
        await update.message.reply_text(
            strelizia_response(
                "💫 Excessive shouting is not permitted. Maintain decorum."
            )
        )


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
    "thanks", "please", "helpful", "good job", 
    "rahmat", "iltimos", "yordam", "yaxshi ish", 
    "mehribon", "qadriga yetish", "a'lo", 
    # More Uzbek (Latin)
    "mukofot", "g'alaba", "sabr", "do'stona", "ilhomlantiruvchi", "yaxshi", "yaxshi kayfiyat", 
    "yordam berish", "rozi", "tasavvur", "ma'naviyat", 
    # Uzbek (Cyrillic)
    "рахмат", "илтимос", "ёрдам", "яхши иш", "мехрибон", "қадрига етиш", "ало",
    "мукофот", "ғалаба", "сабр", "дўстона", "илҳомлантирувчи", "яхши", "яхши кайфият", "ёрдам бериш", "рози", 
    "тасаввур", "маънавият",
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
async def main():
    application = Application.builder().token("8175120417:AAHqwpE5iMvTibJxZu2atlw_gC4Y60Kdki8").build()

    # Add your handlers here
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("ban", ban_user))  # Add /ban command handler
    application.add_handler(CommandHandler("warn", warn_user))  # Add /warn command handler
    application.add_handler(CommandHandler("help", help))  # Add /help command handler
    application.add_handler(CommandHandler("addbadwords", add_bad_words))  # Add /addbadword handler
    application.add_handler(CommandHandler("import", import_bad_words))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_advertisement))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spam))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_positive_behavior))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_profane_message))

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    import asyncio
    keep_alive()

    nest_asyncio.apply()
    asyncio.run(main())


