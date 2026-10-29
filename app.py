import os
import threading
from flask import Flask
import telebot
from telebot import types
import requests
from urllib.parse import urlparse
import time

# টেলিগ্রাম টোকেন
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# আপনার চ্যানেলের ইউজারনেম
CHANNEL_USERNAME = "RedTeamBDSecurityOperation"

# আপনার দেওয়া VirusTotal API Key
VT_API_KEY = "77f4648d6e1715ac91b59a2b8ed6de0bf7e267052979527fed3217014b073013"

# ইউজারের লিংক সাময়িকভাবে সেভ করার জন্য
user_links = {}

def is_user_member(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def check_link_safety(url):
    if not VT_API_KEY:
        return None, "API Key নেই।"
    
    try:
        # VirusTotal API তে লিংক সাবমিট করা
        scan_url = "https://www.virustotal.com/api/v3/urls"
        headers = {"x-apikey": VT_API_KEY}
        files = {"url": (None, url)}
        
        response = requests.post(scan_url, headers=headers, files=files, timeout=15)
        
        if response.status_code == 200:
            json_resp = response.json()
            analysis_id = json_resp['data']['id']
            
            # রেজাল্ট পাওয়ার জন্য অপেক্ষা
            time.sleep(3)
            analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            res = requests.get(analysis_url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                stats = data['data']['attributes']['stats']
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                
                if malicious > 0 or suspicious > 0:
                    return False, f"⚠️ সতর্কতা! এই লিংকটি ক্ষতিকর হতে পারে।\n\n🚨 Malicious: {malicious}\n⚠️ Suspicious: {suspicious}"
                else:
                    return True, "✅ এই লিংকটি নিরাপদ বলে মনে হচ্ছে।"
        return None, "লিংক চেক করা যাচ্ছে না।"
    except Exception as e:
        return None, f"চেক করতে সমস্যা: {e}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_user_member(user_id):
        show_main_menu(message)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        join_btn = types.InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME}")
        check_btn = types.InlineKeyboardButton("✅ জয়েন হয়েছে (চেক করুন)", callback_data="check_join")
        markup.add(join_btn, check_btn)
        
        text = (
            "🦅 **RED TEAM BD** 🦅\n\n"
            "আমাদের অফিসিয়াল চ্যানেলে জয়েন করুন।\n"
            f"টেলিগ্রাম চ্যানেল লিংক: https://t.me/{CHANNEL_USERNAME}\n\n"
            "DEVELOPER BY SABBIR ØX 🙎\n"
            "\"সর্বদা সর্বোচ্চ দেশের তরে আমরা\"\n"
            "RED TEAM BD 🦅"
        )
        bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_check_join(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("1. SELECT LINK")
    btn2 = types.KeyboardButton("2. CHECK LINK")
    markup.add(btn1, btn2)
    
    text = (
        "✅ আপনি সফলভাবে ভেরিফাই হয়েছেন!\n\n"
        "🛡️ **RED LINK CHECKER** 🛡️\n"
        "নিচের অপশনগুলো ব্যবহার করুন:\n\n"
        "1. SELECT LINK - লিংক সেভ করুন\n"
        "2. CHECK LINK - সেভ করা লিংক চেক করুন"
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "1. SELECT LINK")
def ask_for_link(message):
    msg = bot.reply_to(message, "🔗 অনুগ্রহ করে চেক করার লিংকটি পাঠান:")
    bot.register_next_step_handler(msg, save_user_link)

def save_user_link(message):
    user_id = message.from_user.id
    url = message.text.strip()
    
    if not url.startswith("http"):
        url = "http://" + url
    
    parsed = urlparse(url)
    if not parsed.netloc:
        bot.reply_to(message, "❌ ভুল লিংক! সঠিক লিংক দিন (যেমন: https://example.com)")
        return
    
    user_links[user_id] = url
    bot.reply_to(message, f"✅ লিংক সেভ হয়েছে:\n`{url}`\n\nএবার '2. CHECK LINK' চাপুন।", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "2. CHECK LINK")
def check_saved_link(message):
    user_id = message.from_user.id
    url = user_links.get(user_id)
    
    if not url:
        bot.reply_to(message, "❌ আগে 1 নম্বর অপশনে গিয়ে লিংক সেভ করুন।")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    status_msg = bot.reply_to(message, "🔍 লিংক চেক করা হচ্ছে...")
    
    is_safe, result_text = check_link_safety(url)
    domain = urlparse(url).netloc
    
    if is_safe is True:
        bot.edit_message_text(
            f"✅ **লিংক নিরাপদ**\n\n🔗 ডোমেইন: `{domain}`\n📝 স্ট্যাটাস: {result_text}",
            chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown'
        )
    elif is_safe is False:
        bot.edit_message_text(
            f"🚨 **সতর্কতা!**\n\n🔗 ডোমেইন: `{domain}`\n📝 স্ট্যাটাস: {result_text}\n\n⚠️ এই লিংকে ক্লিক করবেন না!",
            chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown'
        )
    else:
        try:
            resp = requests.get(url, timeout=5, allow_redirects=True)
            bot.edit_message_text(
                f"🔍 **লিংক লাইভ আছে**\n\n🔗 ডোমেইন: `{domain}`\n📊 স্ট্যাটাস কোড: {resp.status_code}\n\n⚠️ API Key না থাকায় ফিশিং চেক করা যাচ্ছে না।",
                chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown'
            )
        except:
            bot.edit_message_text(
                f"❌ **লিংকটি লাইভ নয়**\n\n🔗 ডোমেইন: `{domain}`",
                chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown'
            )

def run_bot():
    print("Bot is running...")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
