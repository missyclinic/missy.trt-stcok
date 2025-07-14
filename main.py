import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ตั้งค่า Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# เปิดชีท
treatment_sheet = client.open("Stock Treatment Config").worksheet("treatment_list")
therapist_sheet = client.open("Stock Treatment Config").worksheet("therapist_list")

# ดึงข้อมูลจาก Google Sheets
TREATMENTS = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]

# ตัวอย่างสาขา
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

stock_data = defaultdict(lambda: defaultdict(int))
usage_log = []

# Channel ID จำกัดการใช้งาน
ADMIN_CHANNEL_ID = 1394115416049061918
TREATMENT_CHANNEL_ID = 1394115507883606026

# คำสั่ง: เพิ่มสต๊อก
@tree.command(name="stock_เพิ่ม", description="เพิ่มสต๊อกสินค้า (Admin)")
async def stock_add(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int):
    if interaction.channel_id != ADMIN_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้", ephemeral=True)
        return
    stock_data[สาขา][treatment] += จำนวน
    await interaction.response.send_message(f"✅ เพิ่ม {treatment} {จำนวน} ชิ้น ให้กับ {สาขา}")

# คำสั่ง: ตัดสต๊อก
@tree.command(name="stock_ตัด", description="ตัดสต๊อกเมื่อใช้ทรีตเมนต์กับลูกค้า")
async def stock_cut(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int, ชื่อลูกค้า: str, เทรพิจ: str):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    if treatment not in TREATMENTS:
        await interaction.response.send_message("❌ ไม่พบชื่อ Treatment ในระบบ", ephemeral=True)
        return
    if เทรพิจ not in THERAPISTS:
        await interaction.response.send_message("❌ ไม่พบชื่อพนักงานในระบบ", ephemeral=True)
        return
    if stock_data[สาขา][treatment] < จำนวน:
        await interaction.response.send_message("❌ สต๊อกไม่พอ", ephemeral=True)
        return
    stock_data[สาขา][treatment] -= จำนวน
    log_entry = {
        "uuid": str(uuid.uuid4()),
        "date": datetime.now().isoformat(),
        "branch": สาขา,
        "treatment": treatment,
        "amount": จำนวน,
        "customer": ชื่อลูกค้า,
        "therapist": เทรพิจ,
        "status": "pending"
    }
    usage_log.append(log_entry)
    await interaction.response.send_message(f"✅ ตัด {treatment} {จำนวน} ชิ้น จาก {สาขา} ให้ {ชื่อลูกค้า} โดย {เทรพิจ}")

# คำสั่ง: เช็คคงเหลือ
@tree.command(name="stock_คงเหลือ", description="เช็คสต๊อกคงเหลือตามสาขา")
async def stock_check(interaction: discord.Interaction, สาขา: str):
    msg = f"📦 สต๊อกคงเหลือ {สาขา}:\n"
    for t in TREATMENTS:
        qty = stock_data[สาขา][t]
        msg += f"- {t}: {qty} ชิ้น\n"
    await interaction.response.send_message(msg)

# ลงทะเบียนคำสั่งทั้งหมด
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
