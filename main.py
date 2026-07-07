#!/usr/bin/python3
import telebot
from telebot import types
import sqlite3
from datetime import datetime
import csv
import os

# ⚠️ የራስህን የቦት ቶከን (Token) እዚህ አስገባ
BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ------------------------------------------------------------------
# 🛠️ ክፍል 1፡ የዳታቤዝ (Database) አወቃቀር
# ------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    
    # የተማሪዎች ሠንጠረዥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            chat_id INTEGER PRIMARY KEY,
            full_name TEXT,
            gender TEXT,
            student_class TEXT,
            christian_name TEXT,
            mother_name TEXT,
            phone_number TEXT,
            emergency_phone TEXT,
            reg_date TEXT,
            language TEXT,
            role TEXT DEFAULT 'student',
            assigned_class TEXT,
            parent_chat_id INTEGER,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # የአቴንዳንስ ሠንጠረዥ (ይህንን ጨምር)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            marked_by INTEGER
        )
    ''')
        
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------
# 🛠️ ክፍል 2፡ ረዳት ፈንክሽኖች እና በተኖች
# ------------------------------------------------------------------
def get_language_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("አማርኛ 🇪🇹"), types.KeyboardButton("Afaan Oromoo 🌳"))
    return markup

# አዲስ የተጨመረው የስታርት ኮማንድ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    # ተጠቃሚው መዝገብ ውስጥ ካለ ቋንቋውን እናውጣ፣ ከሌለ ምርጫ እናቅርብ
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM students WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        show_main_menu(chat_id, row[0])
    else:
        bot.send_message(chat_id, "እንኳን ደህና መጡ! እባክዎ ቋንቋ ይምረጡ / Welcome! Please select language:", reply_markup=get_language_markup())

def show_main_menu(chat_id, lang_code):
    role = get_user_role(chat_id)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # የጋራ በተኖች
    btn_report = "📊 ሪፖርት ማውጫ" if lang_code == "amharic" else "📊 Gabaasa"
    btn_lang = "🌐 ቋንቋ ቀይር" if lang_code == "amharic" else "🌐 Jijjiiri Afanii"

    # 1. አድሚን ቲቸር እና ሱፐር አድሚን (መገኘት መዝግብ መብት ያላቸው)
    if role in ['super_admin', 'admin_teacher']:
        if lang_code == "amharic":
            markup.add("📝 መገኘት መዝግብ", btn_report, btn_lang, "⚙️ አድሚን ፓናል")
        else:
            markup.add("📝 Galmee Kamisaa", btn_report, btn_lang, "⚙️ Admin Panel")

    # 2. ኤክስኪዩቲቭ አድሚን (ሪፖርት እና አድሚን ፓናል ብቻ)
    elif role == 'admin_executive':
        if lang_code == "amharic":
            markup.add(btn_report, "⚙️ አድሚን ፓናል", btn_lang)
        else:
            markup.add(btn_report, "⚙️ Admin Panel", btn_lang)

    # 3. ተማሪዎች (ሪፖርት እና ቋንቋ ብቻ)
    else:
        markup.add(btn_report, btn_lang)
        
    bot.send_message(chat_id, "ዋና ማውጫ / Baafata Duraa", reply_markup=markup)

def get_user_lang(chat_id):
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM students WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'amharic'

def get_user_role(chat_id):
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM students WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 'student'

def get_cancel_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn = "❌ ምዝገባን አቋርጥ" if lang == "amharic" else "❌ Galmee Addaan Kuti"
    markup.add(types.KeyboardButton(btn))
    return markup

def get_gender_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == "amharic":
        markup.add(types.KeyboardButton("👦 ወንድ"), types.KeyboardButton("👧 ሴት"), types.KeyboardButton("❌ ምዝገባን አቋርጥ"))
    else:
        markup.add(types.KeyboardButton("👦 Dhiira"), types.KeyboardButton("👧 Dhalaa"), types.KeyboardButton("❌ Galmee Addaan Kuti"))
    return markup

def get_class_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == "amharic":
        markup.add(types.KeyboardButton("👶 የሕፃናት"), types.KeyboardButton("🧑 የወጣቶች"), 
                   types.KeyboardButton("👨 የጎልማሶች / አዋቂዎች"), types.KeyboardButton("❌ ምዝገባን አቋርጥ"))
    else:
        markup.add(types.KeyboardButton("👶 Daaimman"), types.KeyboardButton("🧑 Daree Dargaggootaa"), 
                   types.KeyboardButton("👨 Daree Ga'eessotaa"), types.KeyboardButton("❌ Galmee Addaan Kuti"))
    return markup
def get_teacher_class_markup(chat_id, lang):
    role = get_user_role(chat_id)
    if role == 'admin_teacher':
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT assigned_class FROM students WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        assigned_class = row[0] if row else ""
        # ኢሞጂውን እና ጽሁፉን አንድ ላይ እናድርግ
        btn_text = "🧑 " + assigned_class if "ወጣቶች" in assigned_class else "👶 " + assigned_class
        
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton(btn_text))
        markup.add(types.KeyboardButton("🔙 ወደ ዋናው ማውጫ" if lang=="amharic" else "🔙 Gara Baafata Duraa"))
        return markup
    else:
        return get_class_markup(lang)


def get_class_report_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == "amharic":
        markup.add(types.KeyboardButton("👶 የሕፃናት"), types.KeyboardButton("🧑 የወጣቶች"), 
                   types.KeyboardButton("👨 የጎልማሶች / አዋቂዎች"), types.KeyboardButton("🔙 ወደ ዋናው ማውጫ"))
    else:
        markup.add(types.KeyboardButton("👶 Daaimman"), types.KeyboardButton("🧑 Daree Dargaggootaa"), 
                   types.KeyboardButton("👨 Daree Ga'eessotaa"), types.KeyboardButton("🔙 Gara Baafata Duraa"))
    return markup

def get_back_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn = "🔙 ወደ ዋናው ማውጫ" if lang == "amharic" else "🔙 Gara Baafata Duraa"
    markup.add(types.KeyboardButton(btn))
    return markup

def get_report_menu_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if lang == "amharic":
        markup.add(types.KeyboardButton("🔢 የተማሪዎች ጠቅላላ ብዛት"),
                   types.KeyboardButton("📋 የክፍል ተማሪዎች ዝርዝር"),
                   types.KeyboardButton("📝 ዕለታዊ የመገኘት (Attendance) ሪፖርት"),
                   types.KeyboardButton("📄 ሪፖርት በፋይል አውርድ"),
                   types.KeyboardButton("🔙 ወደ ዋናው ማውጫ"))
    else:
        markup.add(types.KeyboardButton("🔢 Baay'ina Barataa"),
                   types.KeyboardButton("📋 Tarreeffama Barataa Daree"),
                   types.KeyboardButton("📝 Gabaasa HIrnaa (Attendance)"),
                   types.KeyboardButton("📄 Gabaasa fayilaan buufadhu"),
                   types.KeyboardButton("🔙 Gara Baafata Duraa"))
    return markup

def get_file_report_markup(lang):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    if lang == "amharic":
        markup.add("👤 የተማሪዎች ዝርዝር ፋይል", "📝 የአቴንዳንስ ዝርዝር ፋይል", "🔙 ወደ ዋናው ማውጫ")
    else:
        markup.add("👤 Tarreeffama Barataa", "📝 Gabaasa HIrnaa (Attendance)", "🔙 Gara Baafata Duraa")
    return markup

@bot.message_handler(func=lambda message: message.text in ["⚙️ አድሚን ፓናል", "⚙️ Admin Panel"])
def admin_panel_handler(message):
    admin_panel(message.chat.id)

def admin_panel(chat_id):
    lang = get_user_lang(chat_id)
    role = get_user_role(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if lang == "amharic":
        if role == 'super_admin':
            markup.add("➕ አዲስ ተማሪ መዝግብ", "✏️ መረጃ አስተካክል", "👑 አድሚን ሹመት")
            markup.add("🗑️ ተማሪ ሰርዝ", "📊 ሪፖርት አውጣ", "❌ አድሚን ሰርዝ")
            markup.add("🔑 ስልጣን አስረክብ", "♻️ ሪሳይክል ቢን") # አዲሱ በተን
            markup.add("🧹 የአመቱ መጨረሻ ጽዳት")
        # ... (ሌሎች ኮዶችህ እንዳሉ ይቆዩ)
        elif role == 'admin_teacher':
            markup.add("➕ አዲስ ተማሪ መዝግብ", "✏️ መረጃ አስተካክል", "🗑️ ተማሪ ሰርዝ")
            markup.add("📊 ሪፖርት አውጣ", "♻️ ሪሳይክል ቢን")
        elif role == 'admin_executive':
            # ለኤክስኪዩቲቭ አድሚን ሪፖርት ብቻ እንዲታይ ተደረገ
            markup.add("📊 ሪፖርት አውጣ")
        
        markup.add("🔙 ወደ ዋናው ማውጫ")
        text = "⚙️ እንኳን ወደ አድሚን ፓናል በደህና መጡ!"
    else:
        # ለኦሮምኛ ቋንቋ
        # በ admin_panel ውስጥ የኦሮምኛ ክፍል ላይ እንዲህ ጨምረው
        if role == 'super_admin':
    # ... (የድሮ ኮድህ) ...
            markup.add("➕ Barataa haaraa galmeessi", "✏️ Odeeffannoo sirreessi", "👑 Bulchaa muudi")
            markup.add("🗑️ Barataa haqi", "📊 Gabaasa", "❌ Bulchaa haqi")
            markup.add("🔑 Aangoo dabarsii", "♻️ Qulqulleessituu") # አዲሱ በተን
            markup.add("🧹 Qulqullina dhuma waggaa")
        elif role == 'admin_teacher':
            markup.add("➕ Barataa Haaraa Galmeessi", "✏️ Odeeffannoo sirreessi", "🗑️ Barataa haqi")
            markup.add("📊 Gabaasa", "♻️ Qulqulleessituu")
        elif role == 'admin_executive':
            markup.add("📊 Gabaasa")
            
        markup.add("🔙 Gara Baafata Duraa")
        text = "⚙️ Welcome to Admin Panel!"
        
    bot.send_message(chat_id, text, reply_markup=markup)

# ------------------------------------------------------------------
# 🛠️ ክፍል 3፡ አሰሳ እና የመጀመርያ ደረጃዎች
# ------------------------------------------------------------------
user_data = {} 
teacher_sessions = {} 

def check_cancel(message, lang):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # ተጠቃሚው ምዝገባን አቋርጥ የሚለውን በተን ከነካ
    if text in ["❌ ምዝገባን አቋርጥ", "❌ Galmee Addaan Kuti"]:
        msg = "❌ ምዝገባው ተቋርጧል!" if lang == "amharic" else "❌ Galmeen addaan citeera!"
        bot.send_message(chat_id, msg)
        
        # 🔄 ወደ ኋላ ወደ ዋናው ማውጫ እንዲመለስ የሚያደርገው መስመር እዚህ ተጨመረ
        show_main_menu(chat_id, lang)
        
        # ከምዝገባ ሂደቱ እንዲወጣ True ይመልሳል
        return True
    return False

@bot.message_handler(commands=['promote_me'])
def promote_me(message):
    chat_id = message.chat.id
    # እዚህ ጋር የራስህን የቴሌግራም chat_id አስገባ
    # የራስህን ID ለማወቅ ቦቱን በአንድ ሌላ አካውንት አናግረህ ማየት ትችላለህ
    MY_ID = 5274717090  # <--- እዚህ ቁጥር ቦታ የራስህን የቴሌግራም ID አስገባ!

    if chat_id == MY_ID:
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET role = 'super_admin' WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✅ እንኳን ደስ አለዎት! አሁን Super Admin ሆነዋል።")
    else:
        bot.send_message(chat_id, "❌ ይቅርታ፣ ይህንን ትዕዛዝ ለመፈጸም ፈቃድ የለዎትም።")
        
        show_main_menu(chat_id, lang)
        return True
    return False

@bot.message_handler(func=lambda message: message.text in ["አማርኛ 🇪🇹", "Afaan Oromoo 🌳", "🌐 ቋንቋ ቀይር", "🌐 Jijjiiri Afanii", "🔙 ወደ ዋናው ማውጫ", "🔙 Gara Baafata Duraa"])
def handle_navigation(message):
    chat_id = message.chat.id
    selected_text = message.text
    if selected_text in ["🌐 ቋንቋ ቀይር", "🌐 Jijjiiri Afanii"]:
        bot.send_message(chat_id, "እባክዎ አዲስ ቋንቋ ይምረጡ፦", reply_markup=get_language_markup())
        return
    lang_code = get_user_lang(chat_id)
    if selected_text == "አማርኛ 🇪🇹": lang_code = "amharic"
    elif selected_text == "Afaan Oromoo 🌳": lang_code = "oromo"
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (chat_id, language) VALUES(?, ?) ON CONFLICT(chat_id) DO UPDATE SET language=excluded.language", (chat_id, lang_code))
    conn.commit()
    conn.close()
    show_main_menu(chat_id, lang_code)
    
@bot.message_handler(func=lambda message: message.text in ["🧹 የአመቱ መጨረሻ ጽዳት", "🧹 Qulqullina dhuma waggaa"])
def trigger_reset(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ አዎ፣ አጽዳ", "❌ አይ") if lang == "amharic" else markup.add("✅ Eyyee, haqi", "❌ Lakki")
    
    msg = "⚠️ ማስጠንቀቂያ፡ ይህ እርምጃ አቴንዳንስን ያጸዳል እና ኢናክቲቭ ተማሪዎችን ይሰርዛል! እርግጠኛ ነዎት?" if lang == "amharic" else "⚠️ Akeekkachiisa: Tarkaanfiin kun attendance ni qulqulleessa fi barattoota inactive ta'an ni haqa! Mirkanneessitaa?"
    
    sent_msg = bot.send_message(message.chat.id, msg, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, confirm_and_execute)

def confirm_and_execute(message):
    if message.text in ["✅ አዎ፣ አጽዳ", "✅ Eyyee, haqi"]:
        export_and_reset_yearly(message)
    else:
        lang = get_user_lang(message.chat.id)
        msg = "❌ ስራው ተሰርዟል።" if lang == "amharic" else "❌ Tarkaanfichi haqameera."
        bot.send_message(message.chat.id, msg)
    

# ------------------------------------------------------------------
# ➕ ክፍል 4፡ የተማሪ መመዝገቢያ ፎርም
# ------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text in ["➕ አዲስ ተማሪ መዝግብ", "➕ Barataa Haaraa Galmeessi"])
def start_registration(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    user_data[chat_id] = {}
    msg = "የተማሪውን ሙሉ ስም ያስገቡ፦" if lang == "amharic" else "Maqaa guutuu barataa galchi:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_full_name)

def process_full_name(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    user_data[chat_id]['full_name'] = message.text.strip()
    msg = "የተማሪውን ጾታ ይምረጡ፦" if lang == "amharic" else "Saala barataa filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_gender_markup(lang))
    bot.register_next_step_handler(sent_msg, process_gender)

def process_gender(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    g = message.text.strip()
    user_data[chat_id]['gender'] = "ወንድ" if "ወንድ" in g or "Dhiira" in g else "ሴት"
    msg = "የተማሪውን የክፍል ደረጃ ይምረጡ፦" if lang == "amharic" else "Daree barataa filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_class_markup(lang))
    bot.register_next_step_handler(sent_msg, process_class_selection)

def process_class_selection(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    c = message.text.strip()
    class_val = "የሕፃናት" if "ሕፃናት" in c or "Daaimman" in c else "የወጣቶች" if "ወጣቶች" in c or "Dargaggootaa" in c else "የጎልማሶች / አዋቂዎች"
    user_data[chat_id]['student_class'] = class_val
    msg = "የተማሪውን የክርስትና ስም ያስገቡ፦" if lang == "amharic" else "Maqaa Kiristinnaa barataa galchi:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_christian_name)

def process_christian_name(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    user_data[chat_id]['christian_name'] = message.text.strip()
    msg = "የተማሪውን የእናት ስም ያስገቡ፦" if lang == "amharic" else "Maqaa haadha barataa galchi:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_mother_name)

def process_mother_name(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    user_data[chat_id]['mother_name'] = message.text.strip()
    msg = "የተማሪውን የግል ስልክ ቁጥር ያስገቡ፦" if lang == "amharic" else "Lakkoofsa bilbilaa barataa galchi:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_phone)

def process_phone(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    user_data[chat_id]['phone'] = message.text.strip()
    msg = "የአደጋ ጊዜ ተጠሪ ስልክ ቁጥር ያስገቡ፦" if lang == "amharic" else "Lakkoofsa bilbilaa nama muddamaa:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_emergency_phone)

def process_emergency_phone(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    user_data[chat_id]['emergency_phone'] = message.text.strip()
    msg = "የተማሪውን የቴሌግራም መለያ ቁጥር (Telegram ID) ያስገቡ፦"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, process_telegram_id)

def process_telegram_id(message):
    teacher_id = message.chat.id
    lang = get_user_lang(teacher_id)
    if check_cancel(message, lang): return
    try:
        student_id = int(message.text.strip())
        info = user_data.get(teacher_id)
        current_date = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO students (chat_id, full_name, gender, student_class, christian_name, mother_name, phone_number, emergency_phone, reg_date, language) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (student_id, info['full_name'], info['gender'], info['student_class'], info['christian_name'], info['mother_name'], info['phone'], info['emergency_phone'], current_date, lang))
        conn.commit()
        conn.close()
        msg = (f"🎉 ተማሪው በተሳካ ሁኔታ ተመዝግቧል! 🎉\n\n"
               f"👤 ሙሉ ስም:- {info['full_name']}\n"
               f"👥 ጾታ:- {info['gender']}\n"
               f"🏫 የክፍል ደረጃ:- {info['student_class']}\n"
               f"✝️ የክርስትና ስም:- {info['christian_name']}\n"
               f"👩‍🦱 የእናት ስም:- {info['mother_name']}\n"
               f"📞 የግል ስልክ:- {info['phone']}\n"
               f"🚨 የአደጋ ጊዜ ስልክ:- {info['emergency_phone']}\n"
               f"🆔 የቴሌግራም መለያ ቁጥር (Telegram ID):- {student_id}\n"
               f"📅 የተመዘገበበት ቀን:- {current_date}\n\n"
               f"👇 ወደ ዋናው ማውጫ ለመመለስ ከታች ያለውን ንካ::")
        bot.send_message(teacher_id, msg, parse_mode="Markdown", reply_markup=get_back_markup(lang))
        if teacher_id in user_data: del user_data[teacher_id]
    except ValueError:
        bot.send_message(teacher_id, "❌ ስህተት፦ Telegram ID ቁጥር መሆን አለበት።")
        show_main_menu(teacher_id, lang)

# ------------------------------------------------------------------
# 📝 ክፍል 5፡ የዘወትር አቴንዳንስ መመዝገቢያ
# ------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text in ["📝 መገኘት መዝግብ", "📝 Galmee Kamisaa"])
def ask_attendance_class(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    msg = "እባክዎ መገኘት የሚመዘግብለትን ክፍል ይምረጡ፦" if lang == "amharic" else "Maaloo daree galmeeffamu filadhu:"
    
    # ማርክአፕ
    markup = get_teacher_class_markup(chat_id, lang)
    sent_msg = bot.send_message(chat_id, msg, reply_markup=markup)
    
    # ⚠️ በጣም አስፈላጊ፡ ወደሚቀጥለው ፈንክሽን ይሄዳል
    bot.register_next_step_handler(sent_msg, ask_attendance_date)

def ask_attendance_date(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    text = message.text
    
    # የኋላ መመለሻ
    if "ወደ ዋናው ማውጫ" in text or "Gara Baafata Duraa" in text:
        show_main_menu(chat_id, lang)
        return

    # ክፍል መለየት
    class_val = ""
    if "ወጣቶች" in text: class_val = "የወጣቶች"
    elif "ሕፃናት" in text: class_val = "የሕፃናት"
    else: class_val = "የጎልማሶች / አዋቂዎች"
    
    user_data[chat_id] = {'selected_class': class_val}
    
    msg = "እባክዎ የዛሬውን ቀን ያስገቡ (ለምሳሌ፦ 05-12-2018)፦" if lang == "amharic" else "Maaloo guyyaa har'aa galchi (Fkn: 2018-06-25):"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_cancel_markup(lang))
    bot.register_next_step_handler(sent_msg, start_roll_call)

def start_roll_call(message):
    teacher_id = message.chat.id
    lang = get_user_lang(teacher_id)
    if check_cancel(message, lang): return
    
    date_text = message.text.strip()
    selected_class = user_data[teacher_id].get('selected_class')
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    
    # እዚህ ላይ status = 'active' የሚለው ተጨምሯል
    cursor.execute("SELECT chat_id, full_name, gender FROM students WHERE student_class = ? AND status = 'active'", (selected_class,))
    students_list = cursor.fetchall()
    conn.close()
    
    if not students_list:
        msg = f"❌ በ'{selected_class}' ክፍል ውስጥ ምንም ንቁ ተማሪ የለም!" if lang == "amharic" else f"❌ Daree '{selected_class}' keessatti barataan hojjetu hin jiru!"
        bot.send_message(teacher_id, msg)
        show_main_menu(teacher_id, lang)
        return
        
    teacher_sessions[teacher_id] = {'date': date_text, 'students': students_list, 'current_index': 0}
    send_next_student(teacher_id)

def send_next_student(teacher_id):
    session = teacher_sessions[teacher_id]
    index = session['current_index']
    students = session['students']
    date = session['date']
    if index >= len(students):
        lang = get_user_lang(teacher_id)
        bot.send_message(teacher_id, f"🎉 የዕለቱ ({date}) አቴንዳንስ በተሳካ ሁኔታ ተቀምጧል!", reply_markup=get_back_markup(lang))
        del teacher_sessions[teacher_id]
        return
    student_id, student_name, gender = students[index]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ ተገኝቷል", callback_data=f"att_Present_{student_id}"),
               types.InlineKeyboardButton("❌ አልተገኘም", callback_data=f"att_Absent_{student_id}"))
    bot.send_message(teacher_id, f"📅 ቀን፦ {date}\n👤 **ተማሪ፦ {student_name} ({gender})**\n\nይህ ተማሪ ዛሬ ተገኝቷል?", reply_markup=markup, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: call.data.startswith('att_'))
def handle_attendance_click(call):
    teacher_id = call.message.chat.id
    lang = get_user_lang(teacher_id) # ቋንቋውን እናውቅ
    
    # 1. Session መኖሩን ቼክ አድርግ
    if teacher_id not in teacher_sessions:
        bot.answer_callback_query(call.id, "❌ ክፍለ ጊዜው ተቋርጧል!" if lang == "amharic" else "❌ Yeroon qabame kuteera!")
        return
        
    data_parts = call.data.split('_')
    status = data_parts[1] # Present ወይም Absent
    student_id = data_parts[2]
    
    # 2. Database ላይ መመዝገብ
    session = teacher_sessions[teacher_id]
    try:
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attendance (student_id, date, status, marked_by) VALUES (?, ?, ?, ?)", 
                       (student_id, session['date'], status, teacher_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    
    # 3. በተኑን ወደ ጽሁፍ መቀየር (ለሁለቱም ቋንቋ)
    if lang == "amharic":
        mark = "✅ ተገኝቷል" if status == "Present" else "❌ አልተገኘም"
    else:
        mark = "✅ Argameera" if status == "Present" else "❌ Hin argamne"
        
    new_text = f"{call.message.text}\n\nምላሽ/Deebii: {mark}"
    
    try:
        bot.edit_message_text(chat_id=teacher_id, message_id=call.message.message_id, text=new_text)
    except:
        pass 
    
    # 4. ቀጣይ ተማሪ
    session['current_index'] += 1
    if session['current_index'] < len(session['students']):
        send_next_student(teacher_id)
    else:
        # ሁሉም ተጠናቀቀ (ለሁለቱም ቋንቋ)
        msg = "🎉 የዕለቱ አቴንዳንስ ተጠናቋል!" if lang == "amharic" else "🎉 Gabaasaan hirmaannaa (Attendance) guyyaa har'aa xumurameera!"
        bot.send_message(teacher_id, msg, reply_markup=get_back_markup(lang))
        if teacher_id in teacher_sessions:
            del teacher_sessions[teacher_id]
    
    bot.answer_callback_query(call.id)

# ------------------------------------------------------------------
# 📊 ክፍል 6፡ የሪፖርት ማውጫ
# ------------------------------------------------------------------
# ተማሪ የግል ሪፖርቱን የሚያይበት ፈንክሽን
def show_student_personal_report(chat_id):
    lang = get_user_lang(chat_id)
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT date, status FROM attendance WHERE student_id = ? ORDER BY date DESC', (chat_id,))
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        msg = "አሁንም ምንም የአቴንዳንስ መረጃ የለዎትም::" if lang == "amharic" else "Odeeffannoon attendance kee hin jiru."
    else:
        msg = "የእርስዎ የአቴንዳንስ መረጃ:\n\n" if lang == "amharic" else "Gabaasa attendance kee:\n\n"
        for date, status in records:
            mark = "✅ ተገኝተዋል" if status == "Present" else "❌ አልተገኙም"
            msg += f"📅 {date}: {mark}\n"
    bot.send_message(chat_id, msg, reply_markup=get_back_markup(lang))
# አድሚን ፓናል ውስጥ ላለው "ሪፖርት አውጣ" በተን የሚሰራ ሃንድለር
@bot.message_handler(func=lambda message: message.text in ["📊 ሪፖርት አውጣ"])
def admin_panel_report_handler(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    
    # የድሮውን ሪፖርት ሜኑ (get_report_menu_markup) እንዲያመጣ እናዘዋለን
    msg = "እባክዎ የሚፈልጉትን የሪፖርት አይነት ይምረጡ፦" if lang == "amharic" else "Maaloo gabaasa barbaaddan filadhu:"
    bot.send_message(chat_id, msg, reply_markup=get_report_menu_markup(lang))
    

# ሪፖርት ማውጫ ሲነካ የሚሰራው አዲሱ ሃንድለር
@bot.message_handler(func=lambda message: message.text in ["📊 ሪፖርት ማውጫ", "📊 Gabaasa"])
def handle_report_request(message):
    chat_id = message.chat.id
    role = get_user_role(chat_id)
    lang = get_user_lang(chat_id)
    
    # 1. ተማሪ ከሆነ - የአማርኛውን የሪፖርት ፈንክሽን ኮል ያድርግ (ለሁለቱም ቋንቋ)
    if role == 'student':
        show_student_personal_report(chat_id)
        return

    # 2. አድሚን ከሆነ - የጻፍናቸውን መግለጫዎች እንደ ሮሉ ይጥራ
    if role == 'admin_teacher':
        msg = "እርሶ የዶዶላ ደብረ ቅዱሳን ቅዱስ ገብረ ክርስቶስ ፈለገ ህይወት ሰንበት ትምህርት ቤት የመዝሙር ክፍል ተጠሪ ኖት።\nስለ አገልግሎቶት እናመሰግናለን🙏"
        # ለኦሮምኛ የሚሆን ትርጉም
        if lang == 'oromo':
            msg = "Ati itti gaafatamaa kutaa faarfannaa mana kirstaana Qulqulluu gabra kirstos mana barnootaa sanbataa Falaga Hiwoti ti.\nTajaajila kennaa jirtaniif galatoomaa🙏"
        bot.send_message(chat_id, msg)

    elif role == 'admin_executive':
        msg = "እርሶ የዶዶላ ደብረ ቅዱሳን ቅዱስ ገብረ ክርስቶስ ፈለገ ህይወት ሰንበት ትምህርት ቤት የስራ አስፈጻሚ አባል ኖት።\nስለ አገለግሎቶት እናመሰግናለን🙏"
        # ለኦሮምኛ የሚሆን ትርጉም
        if lang == 'oromo':
            msg = "Ati miseensa qaama raawwachiiftuu mana kirstaana Qulqulluu gabra kirstos mana barnootaa sanbataa Falaga Hiwoti ti.\nTajaajila kennaa jirtaniif galatoomaa🙏"
        bot.send_message(chat_id, msg)

    elif role == 'super_admin':
        msg = "እርሶ የዶዶላ ደብረ ቅዱሳን ቅዱስ ገብረ ክርስቶስ ፈለገ ህይወት ሰንበት ትምህርት ቤት ስራ አስፈጻሚ አባል እና የዚህ ቦት ዋና ተቆጣጣሪ ኖት።\nለአገልግሎቶት እናመሰግናለን 🙏"
        # ለኦሮምኛ የሚሆን ትርጉም
        if lang == 'oromo':
            msg = "Ati miseensa qaama raawwachiiftuu fi to'ataa olaanaa baatii kanaa (Super Admin) mana kirstaana Qulqulluu gabra kirstos mana barnootaa sanbataa Falaga Hiwoti ti.\nTajaajila kennaa jirtaniif galatoomaa🙏"
        bot.send_message(chat_id, msg)


@bot.message_handler(func=lambda message: message.text in ["🔢 የተማሪዎች ጠቅላላ ብዛት", "🔢 Baay'ina Barataa"])
def report_total_count(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    classes = ["የሕፃናት", "የወጣቶች", "የጎልማሶች / አዋቂዎች"]
    
    title = "📊 **የተማሪዎች ጠቅላላ ብዛት ሪፖርት (ንቁ ተማሪዎች ብቻ)**" if lang == "amharic" else "📊 **Gabaasa Baay'ina Barattootaa (Barattootaa hojjetan qofa)**"
    report = title + "\n\n"
    
    for c in classes:
        # ማስተካከያው እዚህ ጋር ነው (AND status = 'active' ተጨመረ)
        cursor.execute("SELECT COUNT(*) FROM students WHERE student_class = ? AND gender = 'ወንድ' AND status = 'active'", (c,))
        m = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE student_class = ? AND gender = 'ሴት' AND status = 'active'", (c,))
        f = cursor.fetchone()[0]
        
        report += f"🏫 {c}፦\n  👦 ወንድ፦ {m} | 👧 ሴት፦ {f} | ✅ ድምር፦ {m+f}\n\n"
        
    conn.close()
    bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=get_report_menu_markup(lang))

# 📊 የክፍል ተማሪዎች ዝርዝር በተን (ይህንን ሃንድለር ጨምር)
@bot.message_handler(func=lambda message: message.text in ["📋 የክፍል ተማሪዎች ዝርዝር", "📋 Tarreeffama Barataa Daree"])
def list_students_step1(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    msg = "እባክዎ ክፍሉን ይምረጡ፦" if lang == "amharic" else "Maaloo daree filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_class_report_markup(lang))
    bot.register_next_step_handler(sent_msg, report_class_list_step2)

# የክፍል ዝርዝር አሳዩ (የኢሞጂ ሎጂክ ያለው)
def report_class_list_step2(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    
    c = message.text.strip()
    class_val = "የሕፃናት" if "ሕፃናት" in c or "Daaimman" in c else \
                "የወጣቶች" if "ወጣቶች" in c or "Dargaggootaa" in c else \
                "የጎልማሶች / አዋቂዎች"
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    # status-ንም ጭምር ነው የምንጠይቀው
    cursor.execute("SELECT full_name, phone_number, status FROM students WHERE student_class = ?", (class_val,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, "በዚህ ክፍል ምንም ተማሪ የለም።", reply_markup=get_report_menu_markup(lang))
        return

    report = f"📋 **የ'{class_val}' ክፍል የተማሪዎች ዝርዝር**\n\n"
    for i, row in enumerate(rows, 1):
        # የኢሞጂ ሎጂክ (Active ከሆነ 👤፣ ካልሆነ 🚫)
        emoji = "👤" if row[2] == 'active' else "🚫"
        report += f"{i}. {emoji} {row[0]} | 📞 {row[1]}\n"
    
    bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=get_report_menu_markup(lang))

@bot.message_handler(func=lambda message: message.text in ["📝 ዕለታዊ የመገኘት (Attendance) ሪፖርት", "📝 Gabaasa HIrnaa (Attendance)"])
def report_attendance_step1(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    msg = "ክፍሉን ይምረጡ፦" if lang == "amharic" else "Maaloo daree filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=get_class_report_markup(lang))
    bot.register_next_step_handler(sent_msg, report_attendance_step2)

def report_attendance_step2(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return
    c = message.text.strip()
    
    class_val = "የሕፃናት" if "ሕፃናት" in c or "Daaimman" in c else "የወጣቶች" if "ወጣቶች" in c or "Dargaggootaa" in c else "የጎልማሶች / አዋቂዎች"
        
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT chat_id, full_name, status FROM students WHERE student_class = ?", (class_val,))
    students = cursor.fetchall()
    
    title = f"📝 **የ'{class_val}' ክፍል አቴንዳንስ ሪፖርት**" if lang == "amharic" else f"📝 **Gabaasa HIrnaa kutaa '{class_val}'**"
    report = title + "\n\n"
    
    if not students:
        report += "⚠️ ምንም ተማሪ አልተገኘም\n"
    else:
        for s_id, name, status in students:
            prefix = "🚫 " if status == 'inactive' else "👤 "
            
            cursor.execute("SELECT status FROM attendance WHERE student_id = ?", (s_id,))
            records = cursor.fetchall()
            total = len(records)
            
            if total == 0:
                status_text = "መረጃ የለም"
            else:
                presents = sum(1 for r in records if r[0] == "Present")
                absents = total - presents
                percentage = (presents / total) * 100
                # እዚህ ጋር ነው ፐርሰንቱን ከመገኘት/ከመቅረት ጋር ያካተትነው
                status_text = f"{percentage:.1f}% (✅ {presents} | ❌ {absents})"
            
            report += f"{prefix}{name} ➭ {status_text}\n"
            
    conn.close()
    bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=get_report_menu_markup(lang))

@bot.message_handler(func=lambda message: message.text in ["📄 ሪፖርት በፋይል አውርድ", "📄 Gabaasa fayilaan buufadhu"])
def choose_file_type(message):
    lang = get_user_lang(message.chat.id)
    bot.send_message(message.chat.id, "ምን አይነት ሪፖርት ይፈልጋሉ?" if lang=="amharic" else "Gabaasa akkamii barbaaddu?", 
                     reply_markup=get_file_report_markup(lang))

@bot.message_handler(func=lambda message: message.text in ["👤 የተማሪዎች ዝርዝር ፋይል", "📝 የአቴንዳንስ ዝርዝር ፋይል", "👤 Tarreeffama Barataa", "📝 Gabaasa HIrnaa (Attendance)"])
def ask_class_for_file(message):
    lang = get_user_lang(message.chat.id)
    user_data[message.chat.id] = {'file_type': message.text} 
    msg = "እባክዎ ክፍሉን ይምረጡ፦" if lang == "amharic" else "Maaloo daree filadhu:"
    sent_msg = bot.send_message(message.chat.id, msg, reply_markup=get_class_report_markup(lang))
    bot.register_next_step_handler(sent_msg, generate_file)
    # ... (በgenerate_file ውስጥ Attendance ክፍል ስር) ...
        # እዚህ ጋር ሁሉንም ተማሪዎች እናምጣ (active/inactive ሳንል)
def generate_file(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if check_cancel(message, lang): return 
    
    c = message.text.strip()
    class_val = "የሕፃናት" if "ሕፃናት" in c or "Daaimman" in c else "የወጣቶች" if "ወጣቶች" in c or "Dargaggootaa" in c else "የጎልማሶች / አዋቂዎች"
    file_type = user_data[chat_id].get('file_type')
    safe_class_name = class_val.replace("/", "-").replace(" ", "")
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()

       # 1. የተማሪዎች ዝርዝር ፋይል (Excel/CSV)
    if "ተማሪዎች" in file_type or "Tarreeffama" in file_type:
        # ሁሉንም (active እና inactive) እናምጣ
        cursor.execute('''
            SELECT full_name, gender, student_class, christian_name, mother_name, 
                   phone_number, emergency_phone, reg_date, status 
            FROM students WHERE student_class = ?
        ''', (class_val,))
        rows = cursor.fetchall()
        
        file_name = f"Students_{safe_class_name}.csv"
        with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['የተማሪዎች ዝርዝር ሪፖርት'])
            # የመጨረሻው ኮለመን 'Status' ተጨምሯል
            writer.writerow(['ተ.ቁ', 'ሙሉ ስም', 'ጾታ', 'የክፍል ደረጃ', 'የክርስትና ስም', 'የእናት ስም', 'የግል ስልክ', 'የአደጋ ጊዜ ስልክ', 'የተመዘገበበት ቀን', 'Status'])
            
            for i, row in enumerate(rows, 1):
                # row[-1] ማለት የመጨረሻው 'status' ነው (active ወይም inactive)
                # ስሙ ላይ ምልክት እንዲኖር ከፈለግክ ከፈለግክ ይህንን መጠቀም ትችላለህ፡
                data = list(row)
                if data[-1] == 'inactive':
                    data[0] = f"🚫 {data[0]}" # ስሙ ላይ ምልክት
                
                writer.writerow([i] + data)

    # 2. የአቴንዳንስ ሪፖርት ፋይል (ሁሉንም ተማሪዎች ያካተተ)
    else:
        cursor.execute("SELECT chat_id, full_name, status FROM students WHERE student_class = ?", (class_val,))
        students = cursor.fetchall()
        
        cursor.execute('''
            SELECT DISTINCT date FROM attendance 
            WHERE student_id IN (SELECT chat_id FROM students WHERE student_class = ?) 
            ORDER BY date
        ''', (class_val,))
        dates = [row[0] for row in cursor.fetchall()]
        
        file_name = f"Attendance_{safe_class_name}.csv"
        with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['የአቴንዳንስ ሪፖርት'])
            headers = ['ተ.ቁ', 'ሙሉ ስም'] + dates + ['አጠቃላይ (ተገኘ/ቀረ)']
            writer.writerow(headers)
            
            for i, (s_id, name, status) in enumerate(students, 1):
                display_name = f"🚫 {name}" if status == 'inactive' else name
                row = [i, display_name]
                p, a = 0, 0
                for d in dates:
                    cursor.execute("SELECT status FROM attendance WHERE student_id = ? AND date = ?", (s_id, d))
                    res = cursor.fetchone()
                    if res:
                        if res[0] == "Present":
                            row.append("x"); p += 1
                        else:
                            row.append("A"); a += 1
                    else:
                        row.append("-")
                row.append(f"ተገኘ:{p} | ቀረ:{a}")
                writer.writerow(row)
    
    conn.close()
    
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            bot.send_document(chat_id, f)
        os.remove(file_name)
        bot.send_message(chat_id, "✅ ፋይሉ ተዘጋጅቶ ተልኳል!")
    else:
        bot.send_message(chat_id, "❌ ምንም መረጃ አልተገኘም።")
    
    show_main_menu(chat_id, lang)

# ------------------------------------------------------------------
# ✏️ የተማሪ መረጃ ማስተካከያ (Edit Student)
# ------------------------------------------------------------------

# 1. ተማሪ መፈለጊያ
@bot.message_handler(func=lambda message: message.text == "✏️ መረጃ አስተካክል")
def start_edit_flow(message):
    bot.send_message(message.chat.id, "እባክዎን ማስተካከል የሚፈልጉትን የተማሪ ሙሉ ስም ያስገቡ፦")
    bot.register_next_step_handler(message, search_student_for_edit)

def search_student_for_edit(message):
    name = message.text.strip()
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, full_name, student_class FROM students WHERE full_name LIKE ?", ('%'+name+'%',))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        # የተማሪውን መረጃ በ temporary memory እንይዛለን
        user_data[message.chat.id] = {'editing_id': student[0], 'full_name': student[1]}
        
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("👤 ስም አስተካክል", "🏫 ክፍል አስተካክል", "🔙 ሰርዝ")
        bot.send_message(message.chat.id, f"ተገኝቷል፦ {student[1]} ({student[2]})\nምን ማስተካከል ይፈልጋሉ?", reply_markup=markup)
        bot.register_next_step_handler(message, choose_field_to_edit)
    else:
        bot.send_message(message.chat.id, "❌ ተማሪው አልተገኘም!")

# 2. የትኛው መረጃ እንደሚስተካከል መምረጫ
def choose_field_to_edit(message):
    chat_id = message.chat.id
    if message.text == "🔙 ወደ ዋናው ማውጫ":
        if chat_id in user_data: del user_data[chat_id]
        lang = get_user_lang(chat_id)
        show_main_menu(chat_id, lang)
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("👤 ስም አስተካክል", "🏫 ክፍል አስተካክል", "📞 ስልክ ቁጥር አስተካክል", "🚨 የአደጋ ጊዜ ስልክ አስተካክል", "🔙 ወደ ዋናው ማውጫ")
    bot.send_message(chat_id, "ምን ማስተካከል ይፈልጋሉ?", reply_markup=markup)
    bot.register_next_step_handler(message, process_edit_choice)

# 3. ዳታቤዝ ማሻሻያ (ስም)
def update_name(message):
    chat_id = message.chat.id
    new_name = message.text
    student_id = user_data[chat_id]['editing_id']
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET full_name = ? WHERE chat_id = ?", (new_name, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ ስም በተሳካ ሁኔታ ተስተካክሏል!")
    del user_data[chat_id]

# 4. ዳታቤዝ ማሻሻያ (ክፍል)
def update_class(message):
    chat_id = message.chat.id
    new_class = message.text
    student_id = user_data[chat_id]['editing_id']
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET student_class = ? WHERE chat_id = ?", (new_class, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ ክፍል በተሳካ ሁኔታ ተስተካክሏል!")
    del user_data[chat_id]
# ✏️ የተማሪ መረጃ ማስተካከያ (Edit Student)

@bot.message_handler(func=lambda message: message.text == "✏️ መረጃ አስተካክል")
def start_edit_flow(message):
    bot.send_message(message.chat.id, "እባክዎን ማስተካከል የሚፈልጉትን የተማሪ ሙሉ ስም ያስገቡ፦")
    bot.register_next_step_handler(message, search_student_for_edit)

def search_student_for_edit(message):
    name = message.text.strip()
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, full_name, student_class FROM students WHERE full_name LIKE ?", ('%'+name+'%',))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        user_data[message.chat.id] = {'editing_id': student[0], 'full_name': student[1]}
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("👤 ስም አስተካክል", "🏫 ክፍል አስተካክል", "📞 ስልክ ቁጥር አስተካክል", "🚨 የአደጋ ጊዜ ስልክ አስተካክል", "🔙 ወደ ዋናው ማውጫ")
        bot.send_message(message.chat.id, f"ተገኝቷል፦ {student[1]} ({student[2]})\nምን ማስተካከል ይፈልጋሉ?", reply_markup=markup)
        bot.register_next_step_handler(message, process_edit_choice)
    else:
        bot.send_message(message.chat.id, "❌ ተማሪው አልተገኘም!")

def process_edit_choice(message):
    chat_id = message.chat.id
    text = message.text
    if text == "👤 ስም አስተካክል":
        bot.send_message(chat_id, "አዲሱን ሙሉ ስም ያስገቡ፦")
        bot.register_next_step_handler(message, update_name)
    elif text == "🏫 ክፍል አስተካክል":
        bot.send_message(chat_id, "አዲሱን ክፍል ያስገቡ (ሕፃናት/ወጣቶች/አዋቂዎች)፦")
        bot.register_next_step_handler(message, update_class)
    elif text == "📞 ስልክ ቁጥር አስተካክል":
        bot.send_message(chat_id, "አዲሱን የግል ስልክ ቁጥር ያስገቡ፦")
        bot.register_next_step_handler(message, update_phone)
    elif text == "🚨 የአደጋ ጊዜ ስልክ አስተካክል":
        bot.send_message(chat_id, "አዲሱን የአደጋ ጊዜ ስልክ ቁጥር ያስገቡ፦")
        bot.register_next_step_handler(message, update_emergency_phone)
    elif text == "🔙 ወደ ዋናው ማውጫ":
        if chat_id in user_data: del user_data[chat_id]
        show_main_menu(chat_id, get_user_lang(chat_id))
    else:
        bot.send_message(chat_id, "እባክዎ ከላይ ያሉትን በተኖች ይምረጡ።")
        bot.register_next_step_handler(message, process_edit_choice)

def update_name(message):
    chat_id = message.chat.id
    new_name = message.text
    student_id = user_data[chat_id]['editing_id']
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET full_name = ? WHERE chat_id = ?", (new_name, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ ስም በተሳካ ሁኔታ ተስተካክሏል!")
    del user_data[chat_id]

def update_class(message):
    chat_id = message.chat.id
    new_class = message.text
    student_id = user_data[chat_id]['editing_id']
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET student_class = ? WHERE chat_id = ?", (new_class, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ ክፍል በተሳካ ሁኔታ ተስተካክሏል!")
    del user_data[chat_id]

def update_phone(message):
    chat_id = message.chat.id
    student_id = user_data[chat_id]['editing_id']
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET phone_number = ? WHERE chat_id = ?", (message.text, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ ስልክ ቁጥር ተስተካክሏል!")
    del user_data[chat_id]

def update_emergency_phone(message):
    chat_id = message.chat.id
    student_id = user_data[chat_id]['editing_id']
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET emergency_phone = ? WHERE chat_id = ?", (message.text, student_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✅ የአደጋ ጊዜ ስልክ ተስተካክሏል!")
    del user_data[chat_id]
# 🗑️ ተማሪ ሰርዝ (ወጥቷል የሚል ምልክት መስጫ)
@bot.message_handler(func=lambda message: message.text == "🗑️ ተማሪ ሰርዝ")
def start_delete_flow(message):
    bot.send_message(message.chat.id, "ወጥቷል ለማለት የሚፈልጉትን የተማሪ ስም ያስገቡ፦")
    bot.register_next_step_handler(message, search_student_for_delete)

def search_student_for_delete(message):
    name = message.text.strip()
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    # active የሆኑትን ብቻ እንፈልግ
    cursor.execute("SELECT chat_id, full_name FROM students WHERE full_name LIKE ? AND status = 'active'", ('%'+name+'%',))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        user_data[message.chat.id] = {'delete_id': student[0]}
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("✅ አዎ፣ ወጥቷል በል", "🔙 ወደ ዋናው ማውጫ")
        bot.send_message(message.chat.id, f"ተማሪ፦ {student[1]} ወጥቷል ብለን ምልክት እናድርግ?", reply_markup=markup)
        bot.register_next_step_handler(message, confirm_status_change)
    else:
        bot.send_message(message.chat.id, "❌ ተማሪው አልተገኘም ወይም ቀድሞ ተሰርዟል!")
        admin_panel(message.chat.id)

def confirm_status_change(message):
    chat_id = message.chat.id
    if message.text == "✅ አዎ፣ ወጥቷል በል":
        student_id = user_data[chat_id]['delete_id']
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        # እዚህ ጋር ነው status-ን ወደ 'inactive' የምንቀይረው
        cursor.execute("UPDATE students SET status = 'inactive' WHERE chat_id = ?", (student_id,))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✅ ተማሪው 'ወጥቷል' ተብሎ ተመዝግቧል።")
    
    if chat_id in user_data: del user_data[chat_id]
    admin_panel(chat_id)
    
@bot.message_handler(func=lambda message: message.text == "👑 አድሚን ሹመት") # ይህንን በ admin_panel ውስጥ ጨምረው
def start_admin_promotion(message):
    chat_id = message.chat.id
    if get_user_role(chat_id) != 'super_admin':
        bot.send_message(chat_id, "❌ ይህንን ለማድረግ ፈቃድ የለዎትም።")
        return
        
    msg = "የትኛውን ተማሪ ወደ አድሚንነት መሾም ይፈልጋሉ? (ሙሉ ስም ያስገቡ)"
    sent_msg = bot.send_message(chat_id, msg)
    bot.register_next_step_handler(sent_msg, find_student_for_promotion)

def find_student_for_promotion(message):
    name = message.text.strip()
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, full_name FROM students WHERE full_name LIKE ?", ('%'+name+'%',))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        user_data[message.chat.id] = {'target_id': student[0]}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👨‍🏫 Admin Teacher", "💼 Admin Executive", "🔙 ወደ ዋናው ማውጫ")
        bot.send_message(message.chat.id, f"ተማሪ፦ {student[1]}\nምን አይነት ሮል ይስጡት?", reply_markup=markup)
        bot.register_next_step_handler(message, set_role_type)
    else:
        bot.send_message(message.chat.id, "❌ ተማሪው አልተገኘም!")

def set_role_type(message):
    chat_id = message.chat.id
    role = 'admin_teacher' if "Teacher" in message.text else 'admin_executive'
    target_id = user_data[chat_id]['target_id']
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET role = ? WHERE chat_id = ?", (role, target_id))
    conn.commit()
    conn.close()
    
    bot.send_message(chat_id, f"✅ ተማሪው ወደ {role} ተሹሟል!")
    if role == 'admin_teacher':
        bot.send_message(chat_id, "ለዚህ አስተማሪ የትኛውን ክፍል ይመድቡለታል? (ለምሳሌ: የወጣቶች)")
        bot.register_next_step_handler(message, set_teacher_class)
    else:
        show_main_menu(chat_id, get_user_lang(chat_id))

def set_teacher_class(message):
    # መጀመሪያ user_data ውስጥ target_id መኖሩን እናረጋግጥ
    chat_id = message.chat.id
    if chat_id not in user_data or 'target_id' not in user_data[chat_id]:
        bot.send_message(chat_id, "❌ ስህተት ተፈጥሯል፣ እባክዎ እንደገና ይሞክሩ።")
        return

    target_id = user_data[chat_id]['target_id']
    assigned_class = message.text # የወጣቶች ወይም ሌላ የጻፍከው ክፍል ስም
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET assigned_class = ? WHERE chat_id = ?", (assigned_class, target_id))
    conn.commit()
    conn.close()
    
    bot.send_message(chat_id, f"✅ ተማሪው ወደ አድሚን ቲቸር ተሹሟል እና '{assigned_class}' ክፍል ተመድቧል!")
    
    # እዚህ ጋር ነው ወደ ዋናው ማውጫ የሚመልስህ
    # (ማሳሰቢያ: get_user_lang ስህተት ካመጣ፣ ቀጥታ 'amharic' ብለህ መጻፍ ትችላለህ)
    lang = 'amharic' # ካለህ get_user_lang(chat_id) ተጠቀም
    show_main_menu(chat_id, lang)
    
 # ❌ አድሚን መሰረዝ (በሁለቱም ቋንቋ)
@bot.message_handler(func=lambda message: message.text in ["❌ አድሚን ሰርዝ", "❌ Bulchaa haqi"])
def list_admins_to_remove(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, full_name, role FROM students WHERE role IN ('admin_teacher', 'admin_executive')")
    admins = cursor.fetchall()
    conn.close()
    
    if not admins:
        msg = "ምንም አድሚን አልተገኘም።" if lang == "amharic" else "Bulchaan tokkollee hin argamne."
        bot.send_message(chat_id, msg)
        return
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for admin in admins:
        markup.add(f"{admin[1]} ({admin[2]})")
    markup.add("🔙 ወደ ዋናው ማውጫ" if lang == "amharic" else "🔙 Gara Baafata Duraa")
    
    msg = "የአድሚንነት መብታቸውን ለመንጠቅ የሚፈልጉትን ሰው ይምረጡ፦" if lang == "amharic" else "Namicha mirga bulchaa irraa fuudhuu barbaaddu filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, confirm_admin_removal)

def confirm_admin_removal(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if "ወደ ዋናው ማውጫ" in message.text or "Gara Baafata Duraa" in message.text: 
        return show_main_menu(chat_id, lang)
    
    name_part = message.text.split(" (")[0]
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET role = 'student', assigned_class = NULL WHERE full_name = ?", (name_part,))
    conn.commit()
    conn.close()
    
    success_msg = f"✅ {name_part} ከአድሚንነት ተነስተው ወደ ተማሪነት ተመልሰዋል።" if lang == "amharic" else f"✅ {name_part} mirga bulchaa irraa ka'anii gara barataa deebi'aniiru."
    bot.send_message(chat_id, success_msg)
    show_main_menu(chat_id, lang)
 
 # 🔑 ስልጣን ማስተላለፊያ (ሁለቱንም ቋንቋዎች የያዘ)
@bot.message_handler(func=lambda message: message.text in ["🔑 ስልጣን አስረክብ", "🔑 Aangoo dabarsii"])
def transfer_super_admin_start(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, full_name, role FROM students WHERE role IN ('admin_teacher', 'admin_executive')")
    admins = cursor.fetchall()
    conn.close()
    
    if not admins:
        msg = "ስልጣን የሚያስተላልፉለት አድሚን አልተገኘም።" if lang == "amharic" else "Bulchaan aangoo itti dabarsitan hin jiru."
        bot.send_message(chat_id, msg)
        return
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for admin in admins:
        markup.add(f"{admin[1]} ({admin[2]})")
    markup.add("🔙 ወደ ዋናው ማውጫ" if lang == "amharic" else "🔙 Gara Baafata Duraa")
    
    msg = "ለማን ነው ስልጣኑን ማስረከብ የሚፈልጉት? ከአድሚኖች ዝርዝር ይምረጡ፦" if lang == "amharic" else "Nama kamiif aangoo dabarsuu barbaaddu? Bulchoota keessaa filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, confirm_transfer_admin)

def confirm_transfer_admin(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    
    if message.text in ["🔙 ወደ ዋናው ማውጫ", "🔙 Gara Baafata Duraa"]: 
        return show_main_menu(chat_id, lang)
    
    target_info = message.text
    name_part = target_info.split(" (")[0]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == "amharic":
        markup.add("✅ አዎ፣ አስተላልፍ", "❌ አይ")
        msg = f"{name_part} የሚባለውን ሰው ሱፐር አድሚን ለማድረግ እርግጠኛ ነዎት?"
    else:
        markup.add("✅ Eyyee, dabarsi", "❌ Lakki")
        msg = f"Nama {name_part} jedhamu 'Super Admin' gochuuf mirkaneessitaa?"
    
    user_data[chat_id] = {'target_name': name_part}
    sent_msg = bot.send_message(chat_id, msg, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, execute_transfer)

def execute_transfer(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    
    # የሁለቱንም ቋንቋ አወንታዊ መልስ ማረጋገጥ
    if message.text in ["✅ አዎ፣ አስተላልፍ", "✅ Eyyee, dabarsi"]:
        target_name = user_data[chat_id]['target_name']
        
        conn = sqlite3.connect('church_system.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET role = 'super_admin' WHERE full_name = ?", (target_name,))
        cursor.execute("UPDATE students SET role = 'admin_executive' WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        
        msg = "✅ ስልጣን በተሳካ ሁኔታ ተላልፏል።" if lang == "amharic" else "✅ Aangoon milkaa'inaan dabarfameera."
        bot.send_message(chat_id, msg)
        show_main_menu(chat_id, lang)
    else:
        msg = "❌ ስልጣን ማስተላለፉ ተሰርዟል።" if lang == "amharic" else "❌ Aangoo dabarsuun haqameera."
        bot.send_message(chat_id, msg)
        show_main_menu(chat_id, lang)
        
    if chat_id in user_data: del user_data[chat_id]
  
# ♻️ ሪሳይክል ቢን (Inactive ተማሪዎችን ማየት እና ወደ አክቲቭ መመለስ)
@bot.message_handler(func=lambda message: message.text in ["♻️ ሪሳይክል ቢን", "♻️ Qulqulleessituu"])
def list_inactive_students(message):
    chat_id = message.chat.id
    role = get_user_role(chat_id)
    lang = get_user_lang(chat_id)
    
    if role not in ['super_admin', 'admin_teacher']:
        msg = "ይህንን ክፍል የመጠቀም ፈቃድ የለዎትም።" if lang == "amharic" else "Ajaja kana fayyadamuuf hayyama hin qabdan."
        bot.send_message(chat_id, msg)
        return

    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    
    # ሱፐር አድሚን ከሆነ ሁሉንም ኢናክቲቭ ያያል፣ አስተማሪ ከሆነ ደግሞ የራሱን ክፍል ብቻ
    if role == 'super_admin':
        cursor.execute("SELECT full_name FROM students WHERE status = 'inactive'")
    elif role == 'admin_teacher':
        # መጀመሪያ የአስተማሪውን ክፍል እናውጣ
        cursor.execute("SELECT assigned_class FROM students WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        assigned_class = row[0] if row else ""
        
        # የዛን ክፍል ኢናክቲቭ ተማሪዎች ብቻ እንፈልግ
        cursor.execute("SELECT full_name FROM students WHERE status = 'inactive' AND student_class = ?", (assigned_class,))
        
    inactive_students = cursor.fetchall()
    conn.close()
    
    if not inactive_students:
        msg = "ሪሳይክል ቢን ባዶ ነው። (በክፍልዎ የተሰረዘ ተማሪ የለም)" if lang == "amharic" else "Qulqulleessituun duwwaa dha. (Kutaa keessan keessaa barataan haqame hin jiru)"
        bot.send_message(chat_id, msg)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for student in inactive_students:
        markup.add(student[0])
    markup.add("🔙 ወደ ዋናው ማውጫ" if lang == "amharic" else "🔙 Gara Baafata Duraa")
    
    msg = "መልሰው ለማስፈር የሚፈልጉትን ተማሪ ይምረጡ፦" if lang == "amharic" else "Barataa deebisanii hojjetu gochuuf barbaaddan filadhu:"
    sent_msg = bot.send_message(chat_id, msg, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, restore_student)

def restore_student(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    if "ወደ ዋናው ማውጫ" in message.text or "Gara Baafata Duraa" in message.text: 
        return show_main_menu(chat_id, lang)
        
    student_name = message.text
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET status = 'active' WHERE full_name = ?", (student_name,))
    conn.commit()
    conn.close()
    
    msg = f"✅ {student_name} በተሳካ ሁኔታ ወደ አክቲቭ ተመልሰዋል።" if lang == "amharic" else f"✅ {student_name} gara hojjetutti deebi'aniiru."
    bot.send_message(chat_id, msg)
    admin_panel(chat_id)
    
import csv
import sqlite3
import os
from telebot import types # ቦትህ ላይ እንደተጠቀመህ

# 🧹 የአመቱ መጨረሻ ሪፖርት ማውጫ እና ዳታ ማጽጃ ፈንክሽን (የተሻሻለ)
def export_and_reset_yearly(message):
    chat_id = message.chat.id
    lang = get_user_lang(chat_id)
    file_name = "yearly_report.csv"
    
    conn = sqlite3.connect('church_system.db')
    cursor = conn.cursor()
    
    try:
        with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # ክፍሎችን ለመለየት (የእናት ስም ተካቷል)
            classes = [
                ("የህፃናት ክፍል አመታዊ ሪፖርት", "Daaimman - Gabaasa Waggaa", "የሕፃናት"),
                ("የወጣቶች ክፍል አመታዊ ሪፖርት", "Dargaggootaa - Gabaasa Waggaa", "የወጣቶች"),
                ("የዚህ አመት የጎልማሶች አመታዊ ሪፖርት", "Ga'eessotaa - Gabaasa Waggaa", "የጎልማሶች / አዋቂዎች")
            ]
            
            # ለእያንዳንዱ ክፍል ሪፖርት መጻፍ
            for am_title, or_title, class_name in classes:
                writer.writerow([am_title if lang == "amharic" else or_title])
                writer.writerow(['ሙሉ ስም', 'የክርስትና ስም', 'የእናት ስም', 'ስልክ ቁጥር', 'የአደጋ ጊዜ ስልክ', 'የመጡበት ቀን', 'የቀሩበት ቀን', 'ፐርሰንት (%)'])
                
                # የእናት ስም (mother_name) በ table-ህ ውስጥ እንዳለ አስበናል
                cursor.execute("SELECT full_name, christian_name, mother_name, phone_number, emergency_phone FROM students WHERE student_class = ? AND status = 'active'", (class_name,))
                students = cursor.fetchall()
                
                for s in students:
                    s_name = s[0]
                    s_id = cursor.execute("SELECT chat_id FROM students WHERE full_name = ?", (s_name,)).fetchone()[0]
                    cursor.execute("SELECT status FROM attendance WHERE student_id = ?", (s_id,))
                    att = cursor.fetchall()
                    presents = sum(1 for r in att if r[0] == "Present")
                    absents = len(att) - presents
                    total = len(att)
                    perc = (presents / total * 100) if total > 0 else 0
                    writer.writerow([s[0], s[1], s[2], s[3], s[4], presents, absents, f"{perc:.1f}%"])
                
                writer.writerow([]) # ስፔስ
                writer.writerow([]) # ስፔስ
            
            # ኢናክቲቭ ተማሪዎች
            writer.writerow(["በዚህ አመት የለቀቁ አገልጋዮች" if lang == "amharic" else "Tajaajiltoota waggaa kana gadii dhiisan"])
            writer.writerow(['ሙሉ ስም', 'የክርስትና ስም', 'የእናት ስም', 'ስልክ ቁጥር', 'ክፍል'])
            cursor.execute("SELECT full_name, christian_name, mother_name, phone_number, student_class FROM students WHERE status = 'inactive'")
            for row in cursor.fetchall():
                writer.writerow(row)

        # ሪፖርቱን መላክ
        with open(file_name, 'rb') as f:
            bot.send_document(chat_id, f)
        
        # የጽዳት ስራዎች
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM students WHERE status = 'inactive'")
        conn.commit()
        
                # ሪፖርቱን ከላኩ በኋላ የሚከተለውን ያድርጉ
        success_msg = "✅ ሪፖርቱ ተዘጋጅቶ ተልኳል፣ ሲስተሙም ተጸድቷል! 🧹" if lang == "amharic" else "✅ Gabaasni qophaa'ee ergameera, sirnichis qulqulleeffameera! 🧹"
        bot.send_message(chat_id, success_msg)
        
        # ያስተካከሉት መስመር (ከታች ያለው)
        show_main_menu(chat_id, lang)
        # አሁን ወደ ዋናው ሜኑ ይመለሳል
        
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ ስህተት: {e}")
    finally:
        conn.close()
        if os.path.exists(file_name):
            os.remove(file_name)

   
print("ቦቱ እየሰራ ነው...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)