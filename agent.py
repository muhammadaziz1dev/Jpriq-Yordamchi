import time
import webbrowser
from pymongo import MongoClient

# DIQQAT: O'zingizning yashirin MongoDB Atlas havolangizni shu yerga qo'ying!
MONGO_URI = "SIZNING_MONGODB_ATLAS_CONNECTION_STRING_SHU_YERDA"

try:
    client = MongoClient(MONGO_URI)
    db = client['jpriq_yordamchi_db'] # yordamchi.py dagi bilan bir xil
    commands_col = db['buyruqlar']
    print("Jpriq Yordamchi: Laptop Agent muvaffaqiyatli ulandi va ishga tushdi... 💻")
except Exception as e:
    print(f"Bazaga ulanishda xatolik: {e}")
    exit()

while True:
    try:
        # Bazadan 'pending' (bajarilishi kerak bo'lgan) buyruqni qidiramiz
        active_command = commands_col.find_one({"status": "pending"})
        
        if active_command:
            cmd = active_command["command"]
            print(f"🔔 Yangi buyruq qabul qilindi: {cmd}")
            
            # 1. Chrome ochish buyrug'i
            if cmd == "open_chrome":
                webbrowser.open("https://google.com")
                print("-> Chrome brauzeri ochildi.")
                
            # 2. YouTube ochish buyrug'i
            elif cmd == "open_youtube":
                webbrowser.open("https://youtube.com")
                print("-> YouTube sahifasi ochildi.")
            
            # Buyruq bajarilgach, statusini 'done' qilamiz
            commands_col.update_one(
                {"_id": active_command["_id"]},
                {"$set": {"status": "done"}}
            )
            print("✅ Buyruq statusi 'done' qilib yangilandi.")
            
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        
    # Har 2 soniyada bazani tekshirib turadi
    time.sleep(2)