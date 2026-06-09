import os
import time
import webbrowser
import subprocess
import platform
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ Xatolik: .env faylidan MONGO_URI topilmadi!")
    exit()

try:
    client = MongoClient(MONGO_URI)
    db = client['jpriq_yordamchi_db']
    commands_col = db['buyruqlar']
    print("✅ Jpriq Yordamchi: Laptop Agent ishga tushdi va buyruqlarni kutmoqda...")
except Exception as e:
    print(f"❌ Baza bilan aloqa o'rnatilmadi: {e}")
    exit()

OS = platform.system()  # 'Windows', 'Linux', 'Darwin'

def execute_command(cmd):
    """Buyruqni bajarish va natijani qaytarish"""
    try:
        # Brauzer / Dastur buyruqlari
        if cmd == "open_chrome":
            webbrowser.open("https://google.com")
            print("✅ Chrome ochildi.")

        elif cmd == "open_youtube":
            webbrowser.open("https://youtube.com")
            print("✅ YouTube ochildi.")

        elif cmd == "open_telegram":
            if OS == "Windows":
                subprocess.Popen(["start", "telegram://"], shell=True)
            elif OS == "Linux":
                subprocess.Popen(["xdg-open", "telegram://"])
            elif OS == "Darwin":
                subprocess.Popen(["open", "telegram://"])
            print("✅ Telegram ochilmoqda...")

        elif cmd == "open_vscode":
            if OS == "Windows":
                subprocess.Popen(["code"], shell=True)
            else:
                subprocess.Popen(["code"])
            print("✅ VS Code ochilmoqda...")

        elif cmd == "open_explorer":
            if OS == "Windows":
                subprocess.Popen(["explorer", os.path.expanduser("~")])
            elif OS == "Linux":
                subprocess.Popen(["xdg-open", os.path.expanduser("~")])
            elif OS == "Darwin":
                subprocess.Popen(["open", os.path.expanduser("~")])
            print("✅ Fayl menejeri ochildi.")

        # Kompyuter boshqaruv buyruqlari
        elif cmd == "shutdown":
            print("⚠️ Kompyuter o'chirilmoqda (30 soniya)...")
            if OS == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "30"])
            elif OS in ("Linux", "Darwin"):
                subprocess.run(["shutdown", "-h", "+0.5"])

        elif cmd == "restart":
            print("⚠️ Kompyuter qayta yuklanmoqda...")
            if OS == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "10"])
            elif OS in ("Linux", "Darwin"):
                subprocess.run(["reboot"])

        elif cmd == "sleep":
            print("💤 Uyqu rejimiga o'tilmoqda...")
            if OS == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            elif OS == "Darwin":
                subprocess.run(["pmset", "sleepnow"])
            elif OS == "Linux":
                subprocess.run(["systemctl", "suspend"])

        elif cmd == "lock_screen":
            print("🔒 Ekran qulflanmoqda...")
            if OS == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            elif OS == "Darwin":
                subprocess.run(["pmset", "displaysleepnow"])
            elif OS == "Linux":
                subprocess.run(["loginctl", "lock-session"])

        else:
            print(f"⚠️ Noma'lum buyruq: {cmd}")
            return False

        return True

    except Exception as e:
        print(f"❌ Buyruq bajarishda xatolik ({cmd}): {e}")
        return False


while True:
    try:
        active_command = commands_col.find_one({"status": "pending"})
        if active_command:
            cmd = active_command["command"]
            print(f"\n📩 Yangi buyruq keldi: {cmd}")

            success = execute_command(cmd)

            new_status = "done" if success else "failed"
            commands_col.update_one(
                {"_id": active_command["_id"]},
                {"$set": {"status": new_status}}
            )
            print(f"{'✅' if success else '❌'} Buyruq {new_status} deb belgilandi.\n")

    except Exception as e:
        print(f"❌ Asosiy sikldagi xatolik: {e}")

    time.sleep(2)
