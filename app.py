import os
import threading
from flask import Flask
import telebot
from telebot import types
import requests
from urllib.parse import urlparse
import time

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

CHANNEL_USERNAME = "RedTeamBDSecurityOperation"
VT_API_KEY = os.environ.get('VT_API_KEY', '')

# --- ডাটা স্টোরেজ (মেমোরিতে) ---
user_data = {} 
ref_codes = {} 

# --- প্রমো কোড সেটআপ ---
PROMO_CODES = {
    "REDBD10A": 10, "REDBD10B": 10, "REDBD10C": 10, "REDBD10D": 10, "REDBD10E": 10,
    "REDBD10F": 10, "REDBD10G": 10, "REDBD10H": 10, "REDBD10I": 10, "REDBD10J": 10,
    "REDBD10K": 10, "REDBD10L": 10, "REDBD10M": 10, "REDBD10N": 10, "REDBD10O": 10
}

# ✅ প্রতি প্রমো কোড সর্বোচ্চ ১৫ জন ব্যবহার করতে পারবে
PROMO_LIMIT = 15 

# প্রমো কোডের ব্যবহারের কাউন্ট
promo_usage = {code: 0 for code in PROMO_CODES}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"credits": 10, "referred_by": None, "links": {}, "used_promos": []}
    return user_data[user_id]

def is_user_member(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def check_link_safety(url):
    if not VT_API_KEY:
        return None, "API Key নেই।"
    try:
        scan_url = "https://www.virustotal.com/api/v3/urls"
        headers = {"x-apikey": VT_API_KEY}
        files = {"url": (None, url)}
        response = requests.post(scan_url, headers=headers, files=files, timeout=15)
        if response.status_code == 200:
            analysis_id = response.json()['data']['id']
            time.sleep(3)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers, timeout=15)
            if res.status_code == 200:
                stats = res.json()['data']['attributes']['stats']
                if stats.get('malicious', 0) > 0 or stats.get('suspicious', 0) > 0:
                    return False, f"⚠️ সতর্কতা! ক্ষতিকর লিংক।"
                return True, "✅ লিংকটি নিরাপদ।"
        return None, "চেক করা যাচ্ছে না।"
    except Exception as e:
        return None, f"Error: {e}"

# --- মূল মেনু ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) > 1:
        ref_code = args[1]
        if ref_code in ref_codes:
            referrer_id = ref_codes[ref_code]
            if referrer_id != user_id:
                new_user = get_user(user_id)
                if new_user["referred_by"] is None:
                    new_user["referred_by"] = referrer_id
                    referrer = get_user(referrer_id)
                    referrer["credits"] += 5
                    try:
                        bot.send_message(referrer_id, f"🎉 অভিনন্দন 💐\n\nআপনার লিংকের মাধ্যমে নতুন একজন যুক্ত হয়েছে!\n👤 নাম: {message.from_user.first_name}\n\n🎁 আপনি ৫টি নতুন চেক পারমিশন পেয়েছেন!")
                    except: pass

    if is_user_member(user_id):
        show_main_menu(message)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME}"))
        markup.add(types.InlineKeyboardButton("✅ জয়েন হয়েছে (চেক করুন)", callback_data="check_join"))
        text = (
            "🦅 **RED TEAM BD** 🦅\n\nআমাদের অফিসিয়াল চ্যানেলে জয়েন করুন।\n"
            f"টেলিগ্রাম চ্যানেল লিংক: https://t.me/{CHANNEL_USERNAME}\n\n"
            "DEVELOPER BY SABBIR ØX 🙎\n\"সর্বদা সর্বোচ্চ দেশের তরে আমরা\"\nRED TEAM BD 🦅"
        )
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check_join(call):
    if is_user_member(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("1. SELECT LINK", "2. CHECK LINK", "3. REFER & EARN", "4. MY CREDITS", "5. PROMO CODE 🎉")
    
    user = get_user(message.from_user.id)
    text = (
        f"✅ আপনি সফলভাবে ভেরিফাই হয়েছেন!\n\n"
        f"🛡️ **RED LINK CHECKER** 🛡️\n"
        f"💳 আপনার বর্তমান ক্রেডিট: **{user['credits']}**\n\n"
        f"নিচের অপশনগুলো ব্যবহার করুন:"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# --- SELECT LINK ---
@bot.message_handler(func=lambda m: m.text == "1. SELECT LINK")
def ask_for_link(message):
    msg = bot.reply_to(message, "🔗 অনুগ্রহ করে চেক করার লিংকটি পাঠান:")
    bot.register_next_step_handler(msg, save_user_link)

def save_user_link(message):
    user_id = message.from_user.id
    url = message.text.strip()
    if not url.startswith("http"): url = "http://" + url
    if not urlparse(url).netloc:
        bot.reply_to(message, "❌ ভুল লিংক!")
        return
    get_user(user_id)["links"]["saved"] = url
    bot.reply_to(message, f"✅ লিংক সেভ হয়েছে:\n`{url}`\n\nএবার '2. CHECK LINK' চাপুন।", parse_mode='Markdown')

# --- CHECK LINK ---
@bot.message_handler(func=lambda m: m.text == "2. CHECK LINK")
def check_saved_link(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    url = user["links"].get("saved")
    
    if not url:
        bot.reply_to(message, "❌ আগে 1 নম্বর অপশনে গিয়ে লিংক সেভ করুন।")
        return
    
    if user["credits"] <= 0:
        bot.reply_to(message, "❌ আপনার ক্রেডিট শেষ! রেফার বা প্রমো কোড ব্যবহার করুন।")
        return
    
    user["credits"] -= 1
    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "🔍 লিংক চেক করা হচ্ছে...")
    
    is_safe, res_text = check_link_safety(url)
    domain = urlparse(url).netloc
    remaining = user["credits"]
    
    if is_safe is True:
        bot.edit_message_text(f"✅ **লিংক নিরাপদ**\n\n🔗 ডোমেইন: `{domain}`\n📝 {res_text}\n\n💳 বাকি ক্রেডিট: {remaining}", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
    elif is_safe is False:
        bot.edit_message_text(f"🚨 **সতর্কতা!**\n\n🔗 ডোমেইন: `{domain}`\n📝 {res_text}\n\n💳 বাকি ক্রেডিট: {remaining}", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(f"❌ লিংক চেক করা যায়নি।\n\n💳 বাকি ক্রেডিট: {remaining}", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')

# --- REFER ---
@bot.message_handler(func=lambda m: m.text == "3. REFER & EARN")
def refer_menu(message):
    user_id = message.from_user.id
    ref_code = str(user_id)
    if ref_code not in ref_codes:
        ref_codes[ref_code] = user_id
    
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    text = (
        "🎁 **রেফারেল প্রোগ্রাম** 🎁\n\n"
        "আপনার লিংক শেয়ার করুন। কেউ আপনার লিংকে জয়েন করলে আপনি পাবেন **৫টি চেক পারমিশন**!\n\n"
        f"🔗 আপনার রেফারেল লিংক:\n`{ref_link}`\n\n"
        "লিংকটি কপি করে শেয়ার করুন।"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# --- MY CREDITS ---
@bot.message_handler(func=lambda m: m.text == "4. MY CREDITS")
def show_credits(message):
    user = get_user(message.from_user.id)
    bot.reply_to(message, f"💳 **আপনার ক্রেডিট**\n\nবর্তমান চেক পারমিশন: **{user['credits']}**\n\nরেফার বা প্রমো কোড ব্যবহার করে আরও ক্রেডিট পান।", parse_mode='Markdown')

# --- PROMO CODE ---
@bot.message_handler(func=lambda m: m.text == "5. PROMO CODE 🎉")
def ask_promo(message):
    msg = bot.reply_to(message, "🎉 অনুগ্রহ করে আপনার প্রমো কোডটি লিখুন:")
    bot.register_next_step_handler(msg, apply_promo)

def apply_promo(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    code = message.text.strip().upper()
    
    if code not in PROMO_CODES:
        bot.reply_to(message, "❌ ভুল প্রমো কোড! সঠিক কোড দিন।")
        return
    
    if code in user["used_promos"]:
        bot.reply_to(message, "❌ আপনি ইতিমধ্যে এই প্রমো কোডটি ব্যবহার করেছেন!")
        return
    
    if promo_usage[code] >= PROMO_LIMIT:
        bot.reply_to(message, "❌ দুঃখিত! এই প্রমো কোডের লিমিট শেষ হয়ে গেছে।")
        return
    
    reward = PROMO_CODES[code]
    user["credits"] += reward
    user["used_promos"].append(code)
    promo_usage[code] += 1
    
    bot.reply_to(message, f"✅ **প্রমো কোড সফল!**\n\n🎁 আপনি পেয়েছেন **{reward}টি চেক পারমিশন**।\n💳 বর্তমান ক্রেডিট: {user['credits']}", parse_mode='Markdown')

def run_bot():
    print("Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
