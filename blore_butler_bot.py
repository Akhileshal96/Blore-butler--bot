import telebot
import json
import os

TOKEN = '7817780868:AAEd39YD3hDr1JAsQTCmeN9hgrMAtAHnKe4'
GROUP_USERNAME = 'BangaloreMeetups'  # Group username without '@'
bot = telebot.TeleBot(TOKEN)

user_states = {}
user_data = {}

# Admins list
ADMINS_FILE = 'admins.json'
if os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'r') as f:
        ADMINS = json.load(f)
else:
    ADMINS = []
    with open(ADMINS_FILE, 'w') as f:
        json.dump(ADMINS, f)

# Save data (simulate Excel or DB save here)
def save_registration(user_id, data):
    file = 'registrations.json'
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                records = json.load(f)
        else:
            records = []
        records.append(data)
        with open(file, 'w') as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        print(f"Error saving: {e}")

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    try:
        member = bot.get_chat_member(f"@{GROUP_USERNAME}", user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            bot.send_message(message.chat.id, "🚫 You must be a member of the Bangalore Meetups group to register.")
            return
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Could not verify membership. Make sure the bot is an admin in the group.")
        return

    user_states[user_id] = 'awaiting_name'
    bot.send_message(message.chat.id, "✅ Welcome to Bangalore Meetups Registration!\n\nPlease enter your full name:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_name')
def handle_name(message):
    user_id = message.from_user.id
    user_data[user_id] = {"name": message.text}
    user_states[user_id] = 'awaiting_phone'
    bot.send_message(message.chat.id, "📞 Please enter your 10-digit phone number:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'awaiting_phone')
def handle_phone(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    if not phone.isdigit() or len(phone) != 10:
        bot.send_message(message.chat.id, "❌ Please enter a valid 10-digit phone number:")
        return

    user_data[user_id]["phone"] = phone
    user_data[user_id]["telegram"] = f"{message.from_user.first_name} (@{message.from_user.username})"
    user_data[user_id]["id"] = user_id

    save_registration(user_id, user_data[user_id])
    bot.send_message(message.chat.id, "🎉 Thank you! Your registration is complete.")
    user_states.pop(user_id, None)

bot.infinity_polling()
