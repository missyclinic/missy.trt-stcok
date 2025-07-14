import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from typing import Optional

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

spreadsheet = client.open("Stock Treatment Log CRY")
stock_list_sheet = spreadsheet.worksheet("stock_list")
usage_sheet = spreadsheet.worksheet("treatment_usage")

TREATMENTS_ALL = [
    "TRT-TURBO 5G", "TRT-Super Shape", "TRT-Super Block", "TRT-Super Firm", "TRT-RELAX", "TRT-Reset Body Skin", "TRT-Gold 24K Body", "TRT-Revive (BODY)", "TRT-Revive- Reduce Booster", "TRT-Revive - Immune System Booster", "TRT-Body Scrub", "TRT-Body Mask", "TRT-Back Acne Treatment (สิวหลัง)", "TRT-Breast Massage 15min", "TRT-Breast Massage & Machine(M9)", "TRT-Slim XS", "TRT-Slim FITS", "TRT-Slim Burm", "TRT-Migraine Relief", "TRT-Super Slim - 30min", "TRT-Super Slim - 15min", "TRT-Super Scrub (เฉพาะจุด)", "TRT-Reset (เช็ดเฉพาะรักแร้)", "TRT-Balance (A,B)", "TRT-Revive (HAIR)", "เจลกายภาพ (3P)", "เจลกายภาพ (5P)", "TRT-กกน", "TRT Boxer", "TRT-หมวก", "TRT-ยาชา", "TRT - Shining skin -Botox", "TRT - Shining skin -Collagen", "TRT - Shining skin -Acne", "TRT - Shining skin -Glow", "TRT - Shining skin Pro - 2P", "TRT-Perfect mask -Charcoal", "TRT-Perfact mask -Bulgarian Rose", "TRT-Perfect mask -Anti-Aging", "TRT-Perfect mask -Vit-C", "TRT-Eye action", "TRT-Missy SkinCell", "TRT-Face Lift  5D", "TRT-Revive Face", "TRT-Golden Aura", "TRT-24K Facial Scrub", "TRT-OXY SKIN CELL", "TRT-ชุดทำความสะอาด+บำรุง", "TRT-Milky ทำความสะอาด", "TRT-Water Micellar ทำความสะอาดก่อนกดสิว", "Magnet SkinPro - Peel exfoliator", "Magnet SkinPro - Wish Care", "Magnet SkinPro - BTX", "Magnet SkinPro - Brightening", "Magnet SkinPro - Neo Energy", "Magnet SkinPro -Collagen", "Magnet SkinPro -Hyaluronic", "Magnet SkinPro - Repairing", "TRT-whitamin C", "TRT-GEL กำจัดขน 3P", "TRT-GEL กำจัดขน 1P", "TRT-GEL 9D", "TRT-Missy Vaginal Repair Cream", "TRT-MISSY MADE+", "TCL - IV AURA-WINK-WHITE ตัวยา", "TCL - IV AURA 100ml. ตัวยา", "TCL-IV AURA 20ml PRO ตัวยา", "TCL-IV FAT BUNRNER ตัวยา", "TRT-MESO AURA 1ML", "แล็ปยาชาหน้ากาก", "มีดโกน 1อัน", "บังทรง"
]

THERAPISTS = ["วิ PRY", "รัก PRY", "ปาร์ตี้ SM", "คนที่ 4", "คนที่ 5"]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="ส่งtrt", description="บันทึก Treatment พร้อมอุปกรณ์")
@app_commands.describe(
    สาขา="เลือกสาขา",
    ลูกค้า="ชื่อลูกค้า",
    ใช้อุปกรณ์="เลือกอุปกรณ์ที่ใช้",
    treatment1="ทรีตเมนต์ 1",
    therapist1="พนักงาน 1",
    treatment2="ทรีตเมนต์ 2",
    therapist2="พนักงาน 2",
    treatment3="ทรีตเมนต์ 3",
    therapist3="พนักงาน 3"
)
async def ส่งtrt(interaction: discord.Interaction, สาขา: str, ลูกค้า: str, ใช้อุปกรณ์: str, treatment1: Optional[str], therapist1: Optional[str], treatment2: Optional[str], therapist2: Optional[str], treatment3: Optional[str], therapist3: Optional[str]):
    await interaction.response.defer(thinking=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    records = usage_sheet.get_all_values()
    count_today = sum(1 for row in records[1:] if row[1].startswith(today_date)) + 1
    group_id = f"{today_date.replace('-', '')}-{count_today}"
    treatments = [(treatment1, therapist1), (treatment2, therapist2), (treatment3, therapist3)]
    msg = f"{count_today} ✅ บันทึก Treatment สำหรับ\nชื่อลูกค้า {ลูกค้า}\nทำที่ : {สาขา}\nGroup ID: {group_id}\nรายการTRT\n"
    for t, p in treatments:
        if t and p:
            usage_sheet.append_row([str(uuid.uuid4()), datetime.now().isoformat(), สาขา, t, 1, ลูกค้า, p, group_id, "pending"])
            msg += f"- {t} | {p}\n"
    if ใช้อุปกรณ์ != "ไม่ใช้":
        usage_sheet.append_row([str(uuid.uuid4()), datetime.now().isoformat(), สาขา, ใช้อุปกรณ์, 1, ลูกค้า, "อุปกรณ์", group_id, "pending"])
        msg += f"อุปกรณ์: {ใช้อุปกรณ์}"
    else:
        msg += "ไม่มีอุปกรณ์"
    channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
    await channel.send(msg)
    await interaction.followup.send(f"✅ บันทึกเรียบร้อย Group ID: {group_id}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
