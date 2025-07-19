import discord
from discord.ext import commands
from flask import Flask, request
from threading import Thread
import os
import json
from dotenv import load_dotenv

# โหลด token และ channel จาก .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1394115507883606026
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026


# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ฟังก์ชันส่ง Discord
def send_to_discord(data):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ ไม่พบ Discord Channel")
        return

    treatments = []
    for t in data.get("trt", []):
        name = t.get("name", "").strip()
        amount = t.get("amount", "")
        therapist = t.get("therapist", "").strip()
        if name:
            treatments.append(f"- {name} จำนวน {amount} เทอราปิสต์: {therapist}")

    equipment_lines = []
    for eq in data.get("equipment", []):
        eq_name = eq.get("name", "").strip()
        eq_qty = eq.get("qty", 1)
        if eq_name:
            equipment_lines.append(f"- {eq_name} ({eq_qty})")

    if not treatments and not equipment_lines:
        print("❌ ไม่มีข้อมูล TRT หรืออุปกรณ์ ไม่ส่งข้อความ")
        return

    msg = (
        f"💆‍♀️ **รายการส่งทรีตเมนต์ (TRT)**\n"
        f"📅 วันที่: {data.get('วันที่', '-')}\n"
        f"🧾 M-JOB: {data.get('เลขที่ใบM', '-')}\n"
        f"👩‍🦰 ลูกค้า: {data.get('ลูกค้า', '-')}\n"
    )

    if treatments:
        msg += "📄 รายการ TRT:\n" + "\n".join(treatments) + "\n"
    if equipment_lines:
        msg += "🔧 อุปกรณ์ที่ใช้:\n" + "\n".join(equipment_lines)

    if msg.strip():
        bot.loop.create_task(channel.send(msg))
    else:
        print("❌ ข้อความสุดท้ายว่าง ไม่ส่ง Discord")

# Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 ได้รับ webhook:\n", json.dumps(data, ensure_ascii=False, indent=2))
    if data:
        send_to_discord(data)
        return "✅ Received", 200
    return "❌ No data", 400

# Keep alive
def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} พร้อมใช้งานแล้ว!")

keep_alive()
bot.run(TOKEN)
