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
treatment_sheet = spreadsheet.worksheet("treatment_list")
therapist_sheet = spreadsheet.worksheet("therapist_list")
stock_list_sheet = spreadsheet.worksheet("stock_list")
usage_sheet = spreadsheet.worksheet("treatment_usage")

TREATMENTS_ALL = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]
EQUIPMENTS = ["TRT-หมวก", "TRT-Milky ทำความสะอาด", "TRT-ยาชา", "TRT-กกน", "TRT-ชุดทำความสะอาด+บำรุง", "แล็ปยาชาหน้ากาก"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="ส่งtrt", description="บันทึก Treatment พร้อมอุปกรณ์")
@app_commands.describe(
    สาขา="เลือกสาขา",
    ลูกค้า="ชื่อลูกค้า",
    treatment1="Treatment 1",
    therapist1="Therapist 1",
    treatment2="Treatment 2",
    therapist2="Therapist 2",
    treatment3="Treatment 3",
    therapist3="Therapist 3",
    treatment4="Treatment 4",
    therapist4="Therapist 4",
    treatment5="Treatment 5",
    therapist5="Therapist 5",
    ใช้_หมวก="ใช้ TRT-หมวก หรือไม่",
    ใช้_กกน="ใช้ TRT-กกน หรือไม่",
    ใช้_ชุดทำความสะอาด="ใช้ TRT-ชุดทำความสะอาด+บำรุง หรือไม่",
    ใช้_milky="ใช้ TRT-Milky ทำความสะอาด หรือไม่",
    ใช้_ยาชา="ใช้ TRT-ยาชา หรือไม่",
    ใช้_แล็ปยาชา="ใช้ แล็ปยาชาหน้ากาก หรือไม่"
)
@app_commands.choices(
    สาขา=[app_commands.Choice(name=b, value=b) for b in BRANCHES],
    treatment1=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_ALL],
    treatment2=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_ALL],
    treatment3=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_ALL],
    treatment4=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_ALL],
    treatment5=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_ALL],
    therapist1=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    therapist2=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    therapist3=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    therapist4=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    therapist5=[app_commands.Choice(name=t, value=t) for t in THERAPISTS]
)
async def ส่งtrt(interaction: discord.Interaction,
    สาขา: app_commands.Choice[str],
    ลูกค้า: str,
    treatment1: Optional[app_commands.Choice[str]] = None,
    therapist1: Optional[app_commands.Choice[str]] = None,
    treatment2: Optional[app_commands.Choice[str]] = None,
    therapist2: Optional[app_commands.Choice[str]] = None,
    treatment3: Optional[app_commands.Choice[str]] = None,
    therapist3: Optional[app_commands.Choice[str]] = None,
    treatment4: Optional[app_commands.Choice[str]] = None,
    therapist4: Optional[app_commands.Choice[str]] = None,
    treatment5: Optional[app_commands.Choice[str]] = None,
    therapist5: Optional[app_commands.Choice[str]] = None,
    ใช้_หมวก: bool = False,
    ใช้_กกน: bool = False,
    ใช้_ชุดทำความสะอาด: bool = False,
    ใช้_milky: bool = False,
    ใช้_ยาชา: bool = False,
    ใช้_แล็ปยาชา: bool = False
):
    await interaction.response.defer(thinking=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    records = usage_sheet.get_all_values()
    count_today = sum(1 for row in records[1:] if row[1].startswith(today_date)) + 1
    group_id = f"{today_date.replace('-', '')}-{count_today}"
    treatments = [(treatment1, therapist1), (treatment2, therapist2), (treatment3, therapist3), (treatment4, therapist4), (treatment5, therapist5)]
    msg = f"{count_today} ✅ บันทึก Treatment สำหรับ\nชื่อลูกค้า {ลูกค้า}\nทำที่ : {สาขา.value}\nGroup ID: {group_id}\nรายการTRT\n"
    for t, p in treatments:
        if t and p:
            usage_sheet.append_row([str(uuid.uuid4()), datetime.now().isoformat(), สาขา.value, t.value, 1, ลูกค้า, p.value, group_id, "pending"])
            msg += f"- {t.value} | {p.value}\n"
    equipment_used = []
    if ใช้_หมวก:
        equipment_used.append("TRT-หมวก")
    if ใช้_กกน:
        equipment_used.append("TRT-กกน")
    if ใช้_ชุดทำความสะอาด:
        equipment_used.append("TRT-ชุดทำความสะอาด+บำรุง")
    if ใช้_milky:
        equipment_used.append("TRT-Milky ทำความสะอาด")
    if ใช้_ยาชา:
        equipment_used.append("TRT-ยาชา")
    if ใช้_แล็ปยาชา:
        equipment_used.append("แล็ปยาชาหน้ากาก")
    for eq in equipment_used:
        usage_sheet.append_row([str(uuid.uuid4()), datetime.now().isoformat(), สาขา.value, eq, 1, ลูกค้า, "อุปกรณ์", group_id, "pending"])
    msg += f"อุปกรณ์: {', '.join(equipment_used)}" if equipment_used else "ไม่มีอุปกรณ์"
    channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
    await channel.send(msg)
    await interaction.followup.send(f"✅ บันทึกเรียบร้อย Group ID: {group_id}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
