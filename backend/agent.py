import os
import time
import webbrowser
import subprocess
import platform
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['jpriq_yordamchi_db']
commands_col = db['buyruqlar']

print("✅ Jpriq Yordamchi: Laptop Agent ishga tushdi...")

def execute_command(cmd):
    try:
        if cmd == "open_chrome":
            webbrowser.open("https://google.com")
            return True

        elif cmd == "open_youtube":
            webbrowser.open("https://youtube.com")
            return True

        elif cmd == "open_telegram":
            # Windows uchun barcha mumkin bo'lgan o'rnatilish manzillarini tekshiramiz
            user_home = os.path.expanduser("~")
            possible_paths = [
                f"{user_home}\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
                "C:\\Program Files\\Telegram Desktop\\Telegram.exe",
                "C:\\Program Files (x86)\\Telegram Desktop\\Telegram.exe"
            ]
            
            opened = False
            for path in possible_paths:
                if os.path.exists(path):
                    subprocess.Popen([path])
                    opened = True
                    print(f"✅ Telegram EXE orqali ochildi: {path}")
                    break
            
            if not opened:
                # Agar kompyuterdan EXE topilmasa, brauzerda ochib yuboradi (100% ishlaydigan variant)
                webbrowser.open("tg://resolve")
                print("✅ Telegram protokol orqali ochildi.")
            return True

        elif cmd == "open_vscode":
            user_home = os.path.expanduser("~")
            # VS Code odatda mana shu papkada bo'ladi
            vscode_path = f"{user_home}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
            
            if os.path.exists(vscode_path):
                subprocess.Popen([vscode_path])
                print("✅ VS Code EXE orqali ochildi.")
            else:
                # Agar default joyda bo'lmasa, global 'code' buyrug'ini sinaydi
                subprocess.Popen("code", shell=True)
                print("✅ VS Code standart buyruq bilan ochildi.")
            return True

        elif cmd == "open_explorer":
            os.startfile(os.path.expanduser("~"))
            return True

        # Qolgan tizim buyruqlari...
        elif cmd == "lock_screen":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return True
        elif cmd == "sleep":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return True
        elif cmd == "shutdown":
            subprocess.run(["shutdown", "/s", "/t", "30"])
            return True
        elif cmd == "restart":
            subprocess.run(["shutdown", "/r", "/t", "10"])
            return True

        return False
    except Exception as e:
        print(f"❌ Xatolik yuz berdi ({cmd}): {e}")
        return False

# Asosiy sikl o'sha-o'sha qoladi...
while True:
    try:
        active_command = commands_col.find_one({"status": "pending"})
        if active_command:
            cmd = active_command["command"]
            print(f"\n📩 Yangi buyruq keldi: {cmd}")
            success = execute_command(cmd)
            new_status = "done" if success else "failed"
            commands_col.update_one({"_id": active_command["_id"]}, {"$set": {"status": new_status}})
            print(f"Buyruq {new_status} deb belgilandi.\n")
    except Exception as e:
        print(f"Xatolik: {e}")
    time.sleep(2)