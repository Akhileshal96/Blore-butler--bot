import telebot
import json
import openpyxl
import os

# --- Bot Configuration ---
TOKEN = '7817780868:AAEd39YD3hDr1JAsQTCmeN9hgrMAtAHnKe4'
GROUP_ID = -1001518197115  # Only group members allowed
ADMINS_FILE = "admins.json"
EXCEL_FILE = "registrations.xlsx"

bot = telebot.TeleBot(TOKEN)

# --- File Initialization ---
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "w") as f:
        json.dump(["728623146"], f)  # Add your Telegram user ID here as default admin

if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Telegram ID", "Telegram Name", "Full Name", "Phone Number"])
    wb.save(EXCEL_FILE)

# --- Helpers ---
def load_admins():
    with open(ADMINS_FILE, "r") as f:
        return json.load(f)

def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f)

def is_group_member(user_id):
    try:
        member = bot.get_chat_member(GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- Registration Flow ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_group_member(user_id):
        bot.reply_to(message, "❌ You must be a member of the Bangalore Meetups group to register.")
        return
    msg = bot.reply_to(message, "✅ *Welcome to Bangalore Meetups Registration!*\n\nPlease enter your full name:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_name)

def process_name(message):
    full_name = message.text.strip()
    if not full_name:
        msg = bot.reply_to(message, "Please enter a valid full name:")
        bot.register_next_step_handler(msg, process_name)
        return
    message.chat._custom_data = {'full_name': full_name}
    msg = bot.reply_to(message, "Please enter your 10-digit phone number:")
    bot.register_next_step_handler(msg, process_phone)

def process_phone(message):
    phone = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    name = message.from_user.first_name or ""
    full_name = getattr(message.chat, '_custom_data', {}).get('full_name', '')

    if not phone.isdigit() or len(phone) != 10:
        msg = bot.reply_to(message, "❌ Invalid phone number. Please enter a valid 10-digit number:")
        bot.register_next_step_handler(msg, process_phone)
        return

    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([user_id, f"{name} (@{username})", full_name, phone])
    wb.save(EXCEL_FILE)

    bot.reply_to(message, "✅ You’ve been registered successfully for the Bangalore Meetup!")

# --- Admin Commands ---
@bot.message_handler(commands=['reset'])
def reset(message):
    user_id = str(message.from_user.id)
    if user_id not in load_admins():
        bot.reply_to(message, "❌ Only admins can reset the registration list.")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Telegram ID", "Telegram Name", "Full Name", "Phone Number"])
    wb.save(EXCEL_FILE)
    bot.reply_to(message, "✅ Registration list has been reset.")

@bot.message_handler(commands=['download'])
def download(message):
    user_id = str(message.from_user.id)
    if user_id not in load_admins():
        bot.reply_to(message, "❌ Only admins can download the registration data.")
        return

    with open(EXCEL_FILE, "rb") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(commands=['addadmin'])
def addadmin(message):
    user_id = str(message.from_user.id)
    admins = load_admins()
    if user_id not in admins:
        bot.reply_to(message, "❌ Only admins can add other admins.")
        return
    try:
        new_admin_id = message.text.split(" ")[1]
        if new_admin_id not in admins:
            admins.append(new_admin_id)
            save_admins(admins)
            bot.reply_to(message, f"✅ Admin {new_admin_id} added successfully.")
        else:
            bot.reply_to(message, "⚠️ User is already an admin.")
    except:
        bot.reply_to(message, "Usage: /addadmin <telegram_user_id>")

# --- Catch-All Handler ---
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(message, "ℹ️ Use /start to register for the meetup.")

# --- Start Bot ---
bot.infinity_polling()
