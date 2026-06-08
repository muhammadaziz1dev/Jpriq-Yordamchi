import os
import telebot
from google import genai
from dotenv import load_dotenv
from pymongo import MongoClient
from threading import Thread
import http.server
import socketserver

# 1. Sozlamalarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))
GEMINI_KEY = os.getenv("GEMINI_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# 2. MongoDB ulanishi
db_client = MongoClient(MONGO_URI)
db = db_client["jpriq_yordamchi_db"]
history_collection = db["chat_logs"]

# 3. AI va Botni yaratish
client = genai.Client(api_key=GEMINI_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# Render o'chib qolmasligi uchun yashirin veb-server
def run_health_server():
    PORT = int(os.getenv("PORT", 8080))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server {PORT}-portda ishlamoqda...")
        httpd.serve_forever()

Thread(target=run_health_server, daemon=True).start()

print("Jpriq Yordamchi muvaffaqiyatli ishga tushdi...")

# 4. Xabarlarni qabul qilish va AI ga uzatish
@bot.message_handler(func=lambda message: True)
def javob_berish(message):
    if message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "❌ TIZIM QULFLANGAN!")
        return

    user_text = message.text
    
    # Eskidan qolgan 5 ta xabarni bazadan olish (AI eslab qolishi uchun)
    past_messages = history_collection.find({"chat_id": MY_CHAT_ID}).sort("_id", -1).limit(5)
    
    context = "Siz aqlli Jpriq yordamchisiz. Suhbatdoshning oldingi yozganlari:\n"
    for msg in reversed(list(past_messages)):
        context += f"Xo'jayin: {msg['user']}\nSiz: {msg['ai']}\n"
    context += f"Yangi savol: {user_text}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=context,
        )
        ai_answer = response.text
        
        # Suhbatni bazaga saqlash
        history_collection.insert_one({
            "chat_id": MY_CHAT_ID,
            "user": user_text,
            "ai": ai_answer
        })
        
        bot.reply_to(message, ai_answer)
    except Exception as e:
        bot.reply_to(message, f"Miyada ozgina xatolik: {str(e)}")

bot.polling(none_stop=True)