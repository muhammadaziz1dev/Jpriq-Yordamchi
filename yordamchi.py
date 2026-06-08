import os
import telebot
from google import genai
from dotenv import load_dotenv  # .env faylini o'qish uchun kutubxona

# 1. .env fayli ichidagi o'zgaruvchilarni tizimga yuklash
load_dotenv()

# 2. Kalitlarni operatsion tizim xotirasidan o'qib olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))  # ID raqam bo'lgani uchun int() ga o'giramiz
GEMINI_KEY = os.getenv("GEMINI_KEY")

# 3. Yangi AI mijozini va Botni yaratish
client = genai.Client(api_key=GEMINI_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

print("Jpriq Yordamchi (.env tizimida) muvaffaqiyatli ishga tushdi...")
print("Miya holati: Onlayn. Buyruqlarni kutyapti...")

# 4. Xabarlarni qabul qilish va AI ga uzatish
@bot.message_handler(func=lambda message: True)
def javob_berish(message):
    # Xavfsizlik tizimi
    if message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "❌ TIZIM QULFLANGAN: Siz mening xo'jayinim emassiz!")
        return

    user_text = message.text
    print(f"Xo'jayindan xabar keldi: {user_text}")
    
    try:
        # AI ga savol yuborish
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
        )
        # AI javobini qaytarish
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Miyada xatolik bo'ldi: {str(e)}")

# Botni tinimsiz ishlab turishini ta'minlash
bot.polling(none_stop=True)