import telebot
import json
import os
import openpyxl

TOKEN = '7817780868:AAEd39YD3hDr1JAsQTCmeN9hgrMAtAHnKe4'
GROUP_USERNAME = 'bangloree'  # Group username without '@'
GROUP_ID = -1001518197115  # Use the actual group ID to verify membership
bot = telebot.TeleBot(TOKEN)

user_states = {}
user_data = {}

# Admins list
ADMINS_FILE = 'admins.json'
if os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'r') as f:
        ADMINS = json.load(f)
else:
    ADMINS = ['728623146']
    with open(ADMINS_FILE, 'w') as f:
        json.dump(ADMINS, f)

# Excel file setup
EXCEL_FILE = 'registrations.xlsx'
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Telegram ID', 'Telegram Name', 'Full Name', 'Phone Number'])
    wb.save(EXCEL_FILE)

# Save data to Excel
def save_registration(user_id, data):
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([user_id, data['telegram'], data['name'], data['phone']])
    wb.save(EXCEL_FILE)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    try:
        member = bot.get_chat_member(GROUP_ID, user_id)
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

@bot.message_handler(commands=['download'])
def download_excel(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMINS:
        bot.send_message(message.chat.id, "🚫 You are not authorized to download the registration file.")
        return

    try:
        with open(EXCEL_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Failed to send file.")

bot.infinity_polling()
