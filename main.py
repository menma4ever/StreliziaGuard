from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import time
import re
from better_profanity import profanity
from datetime import datetime, timedelta
import json
from telegram.error import BadRequest

from keep_alive import keep_alive  # Import the keep_alive function from the separate module


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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "💫 Hello, I am Strelizia, the protector of this realm! How can I assist you today?"
    )

# Mute handler for admins only
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is an admin
    user_id_admin = update.message.from_user.id
    chat_id = update.message.chat_id
    chat_member = await context.bot.get_chat_member(chat_id, user_id_admin)

    if chat_member.status not in ['administrator', 'creator']:
        await update.message.reply_text(
            strelizia_response("💫 Only the elite administrators can mute others.")
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            strelizia_response(
                "To mute someone, reply to their message and specify the duration (e.g., 'mute 2h', 'mute 5m')."
            )
        )
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
            await update.message.reply_text(
                strelizia_response("💫 I cannot mute myself. I am Strelizia, the protector of this realm!")
            )
            return

        # Prevent muting administrators
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ['administrator', 'creator']:
            await update.message.reply_text(
                strelizia_response("💫 I cannot mute an administrator. Even Strelizia must show respect to them!")
            )
            return

        await context.bot.restrict_chat_member(
            chat_id=chat_id,
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
                "I couldn't understand the time duration. Use formats like 'mute 2m', 'mute 1h', or 'mute 1d'."
            )
        )


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


# Profanity detection and message deletion
# Profanity detection and message handling with warning system
# Warning system
# Warning system
# Warning system
warnings = {}

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
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_patterns = [
        r"http[s]?://",  # Links (e.g., http://, https://)
        r"www\.",        # URLs starting with www
        r"\b(cheap|sale|discount|buy|offer|limited time)\b",  # Common advertising words
        r"\b(deal|promo|free)\b",  # More advertising words
    ]
    
    message_text = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    chat_id = update.message.chat_id

    try:
        # Check if the message contains any bad words from the custom Uzbek list
        if contains_uzbek_profanity(message_text) or profanity.contains_profanity(message_text):
            # Delete the message
            await update.message.delete()

            # Log the action
            logger.info(f"Deleted a message from {username} due to profanity.")

            # Handle warning system
            if user_id not in warnings:
                warnings[user_id] = 0
            warnings[user_id] += 1

            # Handle warning and mute logic
            if warnings[user_id] >= 3:
                await mute_user(update, context)  # Automatically mute after 3 warnings
                warnings[user_id] = 0  # Reset warning count after muting
            else:
                # Send a warning privately to the user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=strelizia_response(f"💫 @{username}, you’ve used inappropriate language. This is your {warnings[user_id]} warning. Be careful.")
                )

                # Send a warning to the group to show others
                await context.bot.send_message(
                    chat_id=chat_id,  # Group chat_id
                    text=strelizia_response(f"💫 @{username}, you’ve used inappropriate language. This is their {warnings[user_id]} warning. Please be mindful of your language!")
                )

        # Check if the message contains advertisement
        elif any(re.search(pattern, message_text.lower()) for pattern in ad_patterns):
            await update.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text=strelizia_response(f"💫 @{username}, advertisement is not allowed here. Keep the chat on topic!")
            )

        # Check for spam (uppercase messages)
        elif message_text.isupper():
            await update.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text=strelizia_response("💫 Excessive shouting is not permitted. Maintain decorum.")
            )

        # Handle positive behavior (send to the group, not the user privately)
        elif any(keyword in message_text.lower() for keyword in positive_keywords):
            await context.bot.send_message(
                chat_id=chat_id,  # Send to the group, not the user privately
                text=strelizia_response(f"💫 @{username if username else update.message.from_user.first_name}, your kindness has been noted. Continue to inspire others!")
            )

    except BadRequest as e:
        # Log the error if message was deleted and cannot be replied to
        if "Message to be replied not found" in str(e):
            logger.warning(f"Message from {username} deleted, no reply sent.")
        else:
            raise e  # Re-raise the error for unexpected issues






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
    help_text = (
        "💫 Strelizia: Greetings, dear user! I am Strelizia, the protector of this realm. "
        "Here are the ways I can assist you:\n\n"
        "1. **/start** - Start interacting with me! I'll welcome you to this realm.\n"
        "2. **/mute [duration]** - Mute a user for a specified duration (e.g., 'mute 2h', 'mute 5m').\n"
        "3. **/unmute [username]** - Unmute a user, or reply to their message.\n"
        "4. **Message with profanity** - I will delete any messages with profane language and warn you.\n"
        "5. **Advertisement detection** - I will delete any advertisements and remind you to keep the chat on topic.\n"
        "6. **Spam detection** - If you shout in all caps, I will delete your message and remind you to maintain decorum.\n"
        "7. **Positive behavior** - I appreciate kindness and will acknowledge your good behavior.\n\n"
        "💫 If you are an admin, you can also mute or unmute users, and I will respect your decisions as long as they are just!"
    )
    await update.message.reply_text(strelizia_response(help_text))


# Main function
async def main():
    application = Application.builder().token("8175120417:AAHqwpE5iMvTibJxZu2atlw_gC4Y60Kdki8").build()

    # Add your handlers here
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("help", help))  # Add /help command handler here
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
    keep_alive()  # Start the keep_alive function

    nest_asyncio.apply()
    asyncio.run(main())

