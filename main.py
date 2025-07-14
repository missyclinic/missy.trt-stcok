import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
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
TREATMENTS = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="ส่งtrt", description="บันทึก Treatment พร้อมอุปกรณ์")
@app_commands.describe(
    สาขา="เลือกสาขา",
    ลูกค้า="ชื่อลูกค้า",
    ใช้_หมวก="ใช้หมวกหรือไม่",
    ใช้_กกน="ใช้กกนหรือไม่",
    ใช้_ชุดทำความสะอาด="ใช้ชุดทำความสะอาดหรือไม่",
    ใช้_milky="ใช้ Milky หรือไม่",
    ใช้_ยาชา="ใช้ยาชาหรือไม่",
    ใช้_แล็ปยาชา="ใช้แล็ปยาชาหรือไม่",
    treatment1="Treatment 1",
    therapist1="Therapist 1",
    treatment2="Treatment 2",
    therapist2="Therapist 2",
    treatment3="Treatment 3",
    therapist3="Therapist 3",
    treatment4="Treatment 4",
    therapist4="Therapist 4",
    treatment5="Treatment 5",
    therapist5="Therapist 5"
)
@app_commands.choices(
    สาขา=[app_commands.Choice(name=b, value=b) for b in BRANCHES]
)
async def ส่งtrt(interaction: discord.Interaction,
    สาขา: app_commands.Choice[str],
    ลูกค้า: str,
    ใช้_หมวก: Optional[bool] = False,
    ใช้_กกน: Optional[bool] = False,
    ใช้_ชุดทำความสะอาด: Optional[bool] = False,
    ใช้_milky: Optional[bool] = False,
    ใช้_ยาชา: Optional[bool] = False,
    ใช้_แล็ปยาชา: Optional[bool] = False,
    treatment1: Optional[str] = None,
    therapist1: Optional[str] = None,
    treatment2: Optional[str] = None,
    therapist2: Optional[str] = None,
    treatment3: Optional[str] = None,
    therapist3: Optional[str] = None,
    treatment4: Optional[str] = None,
    therapist4: Optional[str] = None,
    treatment5: Optional[str] = None,
    therapist5: Optional[str] = None
):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)

    usage_sheet = spreadsheet.worksheet("treatment_usage")
    today = datetime.now().isoformat()
    today_short = datetime.now().strftime("%Y-%m-%d")
    records = usage_sheet.get_all_values()
    count_today = len({row[7] for row in records[1:] if row[1].startswith(today_short)}) + 1

    group_id = f"{today_short.replace('-', '')}-{count_today}"

    pairs = [(treatment1, therapist1), (treatment2, therapist2), (treatment3, therapist3), (treatment4, therapist4), (treatment5, therapist5)]
    summary = []
    for treatment, therapist in pairs:
        if treatment and therapist and treatment in TREATMENTS and therapist in THERAPISTS:
            usage_sheet.append_row([str(uuid.uuid4()), today, สาขา.value, treatment, 1, ลูกค้า, therapist, group_id, "pending"])
            summary.append(f"- {treatment} | {therapist}")

    selected_equipment = []
    if ใช้_หมวก: selected_equipment.append("TRT-หมวก")
    if ใช้_กกน: selected_equipment.append("TRT-กกน")
    if ใช้_ชุดทำความสะอาด: selected_equipment.append("TRT-ชุดทำความสะอาด+บำรุง")
    if ใช้_milky: selected_equipment.append("TRT-Milky ทำความสะอาด")
    if ใช้_ยาชา: selected_equipment.append("TRT-ยาชา")
    if ใช้_แล็ปยาชา: selected_equipment.append("แล็ปยาชาหน้ากาก")

    for equipment in selected_equipment:
        usage_sheet.append_row([str(uuid.uuid4()), today, สาขา.value, equipment, 1, ลูกค้า, "อุปกรณ์", group_id, "pending"])

    msg = f"{count_today} ✅ บันทึก Treatment สำหรับ\nชื่อลูกค้า {ลูกค้า}\nทำที่ : {สาขา.value}\nGroup ID: {group_id}\nรายการTRT"
    if summary:
        msg += "\n" + "\n".join(summary)
    if selected_equipment:
        msg += f"\nอุปกรณ์: {', '.join(selected_equipment)}"

    channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
    await channel.send(msg)
    await interaction.followup.send(f"✅ บันทึกเรียบร้อย Group ID: {group_id}", ephemeral=True)

@ส่งtrt.autocomplete("treatment1")
@ส่งtrt.autocomplete("treatment2")
@ส่งtrt.autocomplete("treatment3")
@ส่งtrt.autocomplete("treatment4")
@ส่งtrt.autocomplete("treatment5")
async def autocomplete_treatment(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=t, value=t) for t in TREATMENTS if current.lower() in t.lower()][:20]

@ส่งtrt.autocomplete("therapist1")
@ส่งtrt.autocomplete("therapist2")
@ส่งtrt.autocomplete("therapist3")
@ส่งtrt.autocomplete("therapist4")
@ส่งtrt.autocomplete("therapist5")
async def autocomplete_therapist(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=t, value=t) for t in THERAPISTS if current.lower() in t.lower()][:20]

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
