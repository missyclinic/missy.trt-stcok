import discord
from flask import Flask, request
import threading
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ใส่ใน .env

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook received:", data)

    # ส่งเข้า Discord ผ่าน background thread
    threading.Thread(target=send_to_discord, args=(data,)).start()
    return {"status": "ok"}, 200

def send_to_discord(data):
    channel = bot.get_channel(CHANNEL_ID)
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
