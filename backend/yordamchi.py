import os
import telebot
from google import genai
from dotenv import load_dotenv
from pymongo import MongoClient
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS

# 1. Sozlamalarni yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID")) if os.getenv("MY_CHAT_ID") else None
GEMINI_KEY = os.getenv("GEMINI_KEY")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

# 2. MongoDB ulanishi
db_client = MongoClient(MONGO_URI)
db = db_client["jpriq_yordamchi_db"]
history_collection = db["chat_logs"]
commands_collection = db["buyruqlar"]

# 3. AI, Telegram Bot va Flask ilovasini yaratish
client = genai.Client(api_key=GEMINI_KEY)
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
CORS(app)  # Netlify'dan keladigan so'rovlarga ruxsat

print("Jpriq Yordamchi: Tizimlar tayyorlanmoqda...")

# =============================================
# BUYRUQLARNI TEKSHIRISH VA QO'SHISH
# =============================================
def check_and_add_command(text):
    text_lower = text.lower()

    # Brauzer buyruqlari
    if any(k in text_lower for k in ["chrome och", "brauzerni och", "chrome oч"]):
        commands_collection.insert_one({"command": "open_chrome", "status": "pending"})
        return "Xo'p bo'ladi, noutbukda Chrome brauzerini ochish buyrug'ini yubordim. ✅"

    elif any(k in text_lower for k in ["youtube och", "ютуб оч"]):
        commands_collection.insert_one({"command": "open_youtube", "status": "pending"})
        return "Tushundim, noutbukda YouTube sahifasini ochish buyrug'i yuborildi. ✅"

    elif any(k in text_lower for k in ["telegram och", "telegramni och"]):
        commands_collection.insert_one({"command": "open_telegram", "status": "pending"})
        return "Noutbukda Telegram ochish buyrug'i yuborildi. ✅"

    elif any(k in text_lower for k in ["vscode och", "vs code och", "kodni och"]):
        commands_collection.insert_one({"command": "open_vscode", "status": "pending"})
        return "VS Code ochish buyrug'i yuborildi. ✅"

    elif any(k in text_lower for k in ["fileni och", "fayl menejer", "explorer och"]):
        commands_collection.insert_one({"command": "open_explorer", "status": "pending"})
        return "Fayl menejeri ochish buyrug'i yuborildi. ✅"

    # Kompyuter boshqaruv buyruqlari
    elif any(k in text_lower for k in ["o'chir", "ochir", "shutdown", "kompyuterni o'chir"]):
        commands_collection.insert_one({"command": "shutdown", "status": "pending"})
        return "⚠️ Noutbukni o'chirish buyrug'i yuborildi! Saqlanmagan ma'lumotlaringizni saqlang."

    elif any(k in text_lower for k in ["qayta yoq", "restart", "reboot", "kompyuterni qayta"]):
        commands_collection.insert_one({"command": "restart", "status": "pending"})
        return "⚠️ Noutbukni qayta yuklash buyrug'i yuborildi."

    elif any(k in text_lower for k in ["uyquga yoq", "sleep", "uxlat", "suspendga"]):
        commands_collection.insert_one({"command": "sleep", "status": "pending"})
        return "Noutbukni uyqu rejimiga o'tkazish buyrug'i yuborildi. 💤"

    elif any(k in text_lower for k in ["ekranni qulf", "lock screen", "qulfla"]):
        commands_collection.insert_one({"command": "lock_screen", "status": "pending"})
        return "Ekranni qulflash buyrug'i yuborildi. 🔒"

    # TUZATILDI: O'zbekiston vaqti (UTC+5) to'g'rilandi
    elif any(k in text_lower for k in ["hozir soat necha", "vaqt necha", "soat qancha"]):
        import datetime
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        uzb_now = utc_now + datetime.timedelta(hours=5)
        now_str = uzb_now.strftime("%H:%M, %d-%B-%Y")
        return f"🕐 Hozirgi vaqt (O'zbekiston): {now_str}"

    return None


# =============================================
# AI JAVOB OLISH
# =============================================
def get_ai_response(user_text):
    command_reply = check_and_add_command(user_text)
    if command_reply:
        return command_reply

    try:
        past_messages = history_collection.find({"chat_id": MY_CHAT_ID}).sort("_id", -1).limit(6)
        context = (
            "Siz 'Jpriq Yordamchi' deb ataladigan aqlli shaxsiy AI yordamchisiz. "
            "Siz foydalanuvchining shaxsiy yordamchisi sifatida ishlaysiz. "
            "Qisqa, aniq va foydali javob bering. O'zbek tilida javob bering. "
            "Suhbat tarixi:\n"
        )
        for msg in reversed(list(past_messages)):
            context += f"Foydalanuvchi: {msg['user']}\nSiz: {msg['ai']}\n"
        context += f"Yangi savol: {user_text}"

        ai_answer = ""
        models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash-lite', 'gemini-2.0-flash']
        
        # TUZATILDI: Model almashish sikli ancha xavfsiz va toza holatga keltirildi
        for i, model_name in enumerate(models_to_try):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=context
                )
                ai_answer = response.text
                break  # Javob muvaffaqiyatli olinsa, sikldan chiqamiz
            except Exception as model_err:
                # Agar ro'yxatdagi eng oxirgi model ham xato bersa, xatolikni tashqariga otadi
                if i == len(models_to_try) - 1:
                    raise model_err
                print(f"⚠️ {model_name} xato berdi, zaxira modelga o'tilmoqda...")
                continue

        history_collection.insert_one({
            "chat_id": MY_CHAT_ID,
            "user": user_text,
            "ai": ai_answer
        })
        return ai_answer

    except Exception as e:
        return f"Gemini AI bilan ulanishda xatolik yuz berdi. Qaytadan urinib ko'ring. (Xatolik: {str(e)})"


# =============================================
# TELEGRAM BOT
# =============================================
@bot.message_handler(func=lambda message: True)
def handle_telegram_message(message):
    if MY_CHAT_ID and message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "🔒 Tizim qulflangan. Siz ushbu bot egasi emassiz!")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    reply = get_ai_response(message.text)
    bot.reply_to(message, reply)


# =============================================
# FLASK API (Netlify Frontend uchun)
# =============================================
@app.route('/')
def index():
    return "✅ Jpriq Yordamchi Backend Serveri Muvaffaqiyatli Ishlamoqda!"

@app.route('/ask', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"reply": "JSON format noto'g'ri."}), 400

        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"reply": "Xabar bo'sh bo'lishi mumkin emas."}), 400

        ai_answer = get_ai_response(user_message)
        return jsonify({"reply": ai_answer})

    except Exception as e:
        return jsonify({"reply": f"Serverda ichki xatolik: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Server ishlayapti!"})


# =============================================
# ISHGA TUSHIRISH
# =============================================
def run_telegram_bot():
    print("📱 Telegram Bot polling rejimida ishga tushdi...")
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Bot pollingda xatolik: {e}")

if __name__ == '__main__':
    Thread(target=run_telegram_bot, daemon=True).start()
    print(f"🌐 Flask Veb-Interfeysi {PORT}-portda ishga tushdi...")
    app.run(host='0.0.0.0', port=PORT)