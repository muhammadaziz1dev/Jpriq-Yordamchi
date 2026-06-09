import os
import telebot
from google import genai
from dotenv import load_dotenv
from pymongo import MongoClient
from threading import Thread
# Oddiy http.server o'rniga professional Flask'ni olib kiramiz
from flask import Flask, render_template, request, jsonify

# 1. Sozlamalarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
GEMINI_KEY = os.getenv("GEMINI_KEY")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 8080))

# 2. MongoDB ulanishi
db_client = MongoClient(MONGO_URI)
db = db_client["jpriq_yordamchi_db"]
history_collection = db["chat_logs"]
commands_collection = db["buyruqlar"] # Noutbuk buyruqlari uchun yangi jadval

# 3. AI, Telegram Bot va Flask ilovasini yaratish
client = genai.Client(api_key=GEMINI_KEY)
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__) # Veb-saytimiz asosi

print("Jpriq Yordamchi: Tizimlar tayyorlanmoqda...")

# ==========================================
# MANTIQIY QISM (Miya va Kompyuter Boshqaruvi)
# ==========================================

def check_and_add_command(text):
    """ Kelgan matn ichida noutbuk uchun buyruq borligini tekshiradi """
    text_lower = text.lower()
    
    if "chrome och" in text_lower or "brauzerni och" in text_lower:
        commands_collection.insert_one({"command": "open_chrome", "status": "pending"})
        return "Xo'p bo'ladi, noutbukda Chrome brauzerini ochish buyrug'ini yubordim. 🌐"
        
    elif "youtube och" in text_lower:
        commands_collection.insert_one({"command": "open_youtube", "status": "pending"})
        return "Tushundim, noutbukda YouTube sahifasini ochish buyrug'i yuborildi. 📺"
        
    return None

def get_ai_response(user_text):
    """ Telegram va Veb-sayt uchun umumiy yagona miya """
    # 1. Avval noutbuk uchun buyruqmi yoki yo'qligini tekshiramiz
    command_reply = check_and_add_command(user_text)
    if command_reply:
        return command_reply

    # 2. Agar oddiy suhbat bo'lsa, eslab qolish tizimi bilan Gemini'ga jo'natamiz
    past_messages = history_collection.find({"chat_id": MY_CHAT_ID}).sort("_id", -1).limit(5)
    
    context = "Siz aqlli Jpriq yordamchisiz. Suhbatdoshning oldingi yozganlari:\n"
    for msg in reversed(list(past_messages)):
        context += f"Xo'jayin: {msg['user']}\nSiz: {msg['ai']}\n"
    context += f"Yangi savol: {user_text}"

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=context,
    )
    ai_answer = response.text
    
    # Suhbatni umumiy bazaga saqlash
    history_collection.insert_one({
        "chat_id": MY_CHAT_ID,
        "user": user_text,
        "ai": ai_answer
    })
    
    return ai_answer

# ==========================================
# FLASK VEB-SAYT QISMI (Frontend ulanishi)
# ==========================================

@app.route('/')
def index():
    # templates/index.html faylini brauzerga ochib beradi
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_ai():
    # HTML ichidagi JavaScript so'rovini qabul qiladi
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Xabar bo'sh bo'lishi mumkin emas."}), 400
        
        # Miyadan javob olamiz
        ai_answer = get_ai_response(user_message)
        return jsonify({"reply": ai_answer})
    except Exception as e:
        return jsonify({"reply": f"Veb-serverda xatolik: {str(e)}"}), 500

# ==========================================
# TELEGRAM BOT QISMI
# ==========================================

@bot.message_handler(func=lambda message: True)
def javob_berish(message):
    if message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "❌ TIZIM QULFLANGAN!")
        return

    try:
        ai_answer = get_ai_response(message.text)
        bot.reply_to(message, ai_answer)
    except Exception as e:
        bot.reply_to(message, f"Miyada ozgina xatolik: {str(e)}")

# ==========================================
# IKKALA TIZIMNI BIR VAQTDA ISHGA TUSHIRISH
# ==========================================

def run_telegram_bot():
    print("Telegram Bot polling rejimida ishga tushdi... 🤖")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # 1. Telegram botni orqa fonda (Thread) alohida liniyada yoqamiz
    Thread(target=run_telegram_bot, daemon=True).start()
    
    # 2. Flask veb-serverni asosiy liniyada yoqamiz (Render portni nazorat qilishi uchun)
    print(f"Flask Veb-Interfeysi {PORT}-portda ishga tushdi... 🚀")
    app.run(host='0.0.0.0', port=PORT)