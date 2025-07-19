import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask, request
from threading import Thread
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1394115507883606026
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

app = Flask(__name__)

# ตั้งค่า Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ฟังก์ชันส่งข้อความ
def send_to_discord(data):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ ไม่พบช่อง Discord")
        return

    if "trt" in data:  # เช็คว่าเป็นข้อมูลจากการส่ง TRT
        # สร้างข้อความ TRT
        treatments = []
        for t in data["trt"]:
            if t["name"]:
                treatments.append(f"- {t['name']} จำนวน {t['amount']} เทอราปิสต์: {t['therapist']}")
        
        # สร้างข้อความอุปกรณ์
        equipment_lines = []
        for eq in data.get("equipment", []):
            equipment_lines.append(f"- {eq['name']} ({eq['qty']})")

        msg = (
            f"💆‍♀️ **รายการส่งทรีตเมนต์ (TRT)**\n"
            f"📅 วันที่: {data.get('วันที่')}\n"
            f"🧾 M-JOB: {data.get('เลขที่ใบM')}\n"
            f"👩‍🦰 ลูกค้า: {data.get('ลูกค้า')}\n"
            f"📄 รายการ TRT:\n" + "\n".join(treatments) + "\n"
            f"🔧 อุปกรณ์ที่ใช้:\n" + "\n".join(equipment_lines)
        )
        bot.loop.create_task(channel.send(msg))
    else:
        bot.loop.create_task(channel.send("❌ ไม่สามารถอ่านข้อมูลจาก webhook ได้"))

# Web server สำหรับ webhook
app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 รับข้อมูลจาก Google Sheets:", data)
    if data:
        send_to_discord(data)
        return "✅ Data received", 200
    return "❌ No data", 400

# Run Flask ใน Thread (ให้ Railway ตรวจว่า bot ยังตื่น)
def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# เริ่มต้น Bot
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"📝 Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync error:", e)

keep_alive()
bot.run(TOKEN)
