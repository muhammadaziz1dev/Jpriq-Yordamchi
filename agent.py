import os
import time
import webbrowser
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("Xatolik: .env faylidan MONGO_URI topilmadi!")
    exit()

try:
    client = MongoClient(MONGO_URI)
    db = client['jpriq_yordamchi_db']
    commands_col = db['buyruqlar']
    print("Jpriq Yordamchi: Laptop Agent ishga tushdi va buyruqlarni kutmoqda... 💻")
except Exception as e:
    print(f"Baza bilan aloqa o'rnatilmadi: {e}")
    exit()

while True:
    try:
        active_command = commands_col.find_one({"status": "pending"})
        if active_command:
            cmd = active_command["command"]
            print(f"🔔 Yangi buyruq keldi: {cmd}")
            
            if cmd == "open_chrome":
                webbrowser.open("https://google.com")
                print("-> Chrome ochildi.")
            elif cmd == "open_youtube":
                webbrowser.open("https://youtube.com")
                print("-> YouTube ochildi.")
                
            commands_col.update_one(
                {"_id": active_command["_id"]},
                {"$set": {"status": "done"}}
            )
            print("✅ Buyruq bajarildi.")
    except Exception as e:
        print(f"Xatolik: {e}")
        
    time.sleep(2)