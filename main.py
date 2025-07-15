import discord
import os
from flask import Flask, request
import threading
from dotenv import load_dotenv
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


load_dotenv()  # เผื่อรัน local ยังใช้ .env, ถ้าบน Railway จะดึงจาก Environment Variables เอง

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1394115507883606026
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026


app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook received:", data)

    # ส่งเข้า Discord ผ่าน background thread
    threading.Thread(target=send_to_discord, args=(data,)).start()
    return {"status": "ok"}, 200

def send_to_discord(data):
    print("Sending to Discord Channel:", CHANNEL_ID)
    channel = bot.get_channel(CHANNEL_ID)
    print("Channel Object:", channel)
    if channel:
        treatments = "\n".join([f"- {t['name']} | {t['therapist']}" for t in data.get("treatments", [])])
        equipment = ", ".join(data.get("equipment", []))

        message = (
            f"✅ บันทึกทรีตเมนต์ผ่าน Google Sheets\n"
            f"ลูกค้า: {data.get('customer')}\n"
            f"สาขา: {data.get('branch')}\n"
            f"รายการ TRT:\n{treatments}\n"
            f"อุปกรณ์: {equipment}\n"
        )
        bot.loop.create_task(channel.send(message))

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
