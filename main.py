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
try:
    stock_sheet = spreadsheet.worksheet("stock_list")
except gspread.exceptions.WorksheetNotFound:
    stock_sheet = spreadsheet.add_worksheet(title="stock_list", rows="100", cols="5")
    stock_sheet.append_row(["สาขา", "Treatment", "จำนวนคงเหลือ"])

treatment_sheet = spreadsheet.worksheet("treatment_list")
therapist_sheet = spreadsheet.worksheet("therapist_list")
TREATMENTS = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="ลงทรีตเมนต์", description="บันทึก Treatment แบบ Dropdown")
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
)
async def ลงทรีตเมนต์(interaction: discord.Interaction,
    สาขา: str,
    ลูกค้า: str,
    treatment1: Optional[str] = None,
    therapist1: Optional[str] = None,
    treatment2: Optional[str] = None,
    therapist2: Optional[str] = None,
    treatment3: Optional[str] = None,
    therapist3: Optional[str] = None,
    treatment4: Optional[str] = None,
    therapist4: Optional[str] = None,
    treatment5: Optional[str] = None,
    therapist5: Optional[str] = None,
):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)

    usage_sheet = spreadsheet.worksheet("treatment_usage")
    today = datetime.now().isoformat()
    group_id = str(uuid.uuid4())

    pairs = [(treatment1, therapist1), (treatment2, therapist2), (treatment3, therapist3), (treatment4, therapist4), (treatment5, therapist5)]
    summary = []
    for treatment, therapist in pairs:
        if treatment and therapist:
            usage_sheet.append_row([str(uuid.uuid4()), today, สาขา, treatment, 1, ลูกค้า, therapist, group_id, "pending"])
            summary.append(f"- {treatment} | {therapist}")

    msg = f"✅ บันทึก Treatment สำหรับ {ลูกค้า} สาขา {สาขา}\nGroup UUID: {group_id}\n" + "\n".join(summary)
    channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
    await channel.send(msg)
    await interaction.followup.send(f"✅ บันทึกเรียบร้อย Group UUID: {group_id}", ephemeral=True)

@ลงทรีตเมนต์.autocomplete("treatment1")
@ลงทรีตเมนต์.autocomplete("treatment2")
@ลงทรีตเมนต์.autocomplete("treatment3")
@ลงทรีตเมนต์.autocomplete("treatment4")
@ลงทรีตเมนต์.autocomplete("treatment5")
async def autocomplete_treatment(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=t, value=t) for t in TREATMENTS if current.lower() in t.lower()][:20]

@ลงทรีตเมนต์.autocomplete("therapist1")
@ลงทรีตเมนต์.autocomplete("therapist2")
@ลงทรีตเมนต์.autocomplete("therapist3")
@ลงทรีตเมนต์.autocomplete("therapist4")
@ลงทรีตเมนต์.autocomplete("therapist5")
async def autocomplete_therapist(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=t, value=t) for t in THERAPISTS if current.lower() in t.lower()][:20]

@tree.command(name="stock_เพิ่ม", description="เพิ่มสต๊อกสินค้า (Admin)")
async def stock_add(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int):
    if interaction.channel_id not in [ADMIN_CHANNEL_ID, ADMIN_ONLY_CHANNEL_ID]:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    stock_sheet.append_row([สาขา, treatment, จำนวน])
    await interaction.response.send_message(f"✅ เพิ่ม {treatment} {จำนวน} ชิ้น ให้กับ {สาขา}")

@tree.command(name="stock_คงเหลือ", description="เช็คคงเหลือตามสาขา")
async def stock_check(interaction: discord.Interaction, สาขา: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    records = stock_sheet.get_all_values()
    msg = f"📦 สต๊อกคงเหลือ {สาขา}:\n"
    for row in records[1:]:
        if row[0] == สาขา:
            msg += f"- {row[1]}: {row[2]} ชิ้น\n"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="พนักงานรับทรีตเมนต์ยืนยัน", description="พนักงานยืนยันว่าได้รับทรีตเมนต์ในกลุ่มนั้นแล้ว")
async def stock_confirm_group(interaction: discord.Interaction, group_uuid: str):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    updated = 0
    for i, row in enumerate(records):
        if row[7] == group_uuid and row[8] == "pending":
            usage_sheet.update_cell(i+1, 9, "completed")
            updated += 1
    if updated > 0:
        await interaction.response.send_message(f"✅ ยืนยันกลุ่ม {group_uuid} ทั้งหมด {updated} รายการ", ephemeral=True)
    else:
        await interaction.response.send_message("❌ ไม่พบหรือยืนยันไปแล้ว", ephemeral=True)

@tree.command(name="รายงานทรีตเมนต์วันนี้", description="ดูรายการทรีตเมนต์ทั้งหมดที่ถูกส่งวันนี้")
async def treatment_report_today(interaction: discord.Interaction):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    today_date = datetime.now().date().isoformat()
    msg = "📊 รายการทรีตเมนต์วันนี้\n"
    count = 0
    for row in records[1:]:
        if row[1][:10] == today_date:
            msg += f"• ลูกค้า: {row[5]}, Therapist: {row[6]}, Treatment: {row[3]}, สาขา: {row[2]}\n"
            count += 1
    if count == 0:
        msg += "ไม่มีรายการวันนี้"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="รายงานทรีตเมนต์ลายพนักงาน", description="ดูสรุปการใช้ทรีตเมนต์แยกตามพนักงานวันนี้")
async def treatment_summary_by_therapist(interaction: discord.Interaction):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    today_date = datetime.now().date().isoformat()
    summary = defaultdict(int)
    for row in records[1:]:
        if row[1][:10] == today_date and row[8] == "completed":
            summary[row[6]] += 1
    msg = "📊 สรุปทรีตเมนต์วันนี้แยกตามพนักงาน\n"
    if summary:
        for therapist, total in summary.items():
            msg += f"- {therapist}: {total} รายการ"
    else:
        msg += "ไม่มีรายการวันนี้"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="stock_ยกเลิกบางรายการ", description="ยกเลิก Treatment หลายรายการ")
@app_commands.describe(uuid_codes="เลือก UUID หลายรายการ พร้อมแสดงชื่อลูกค้า")
async def stock_cancel(interaction: discord.Interaction, uuid_codes: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    uuid_list = [u.split("|")[0].strip() for u in uuid_codes.split(",") if u.strip()]
    cancelled = 0
    for i, row in enumerate(records):
        if row[0] in uuid_list and row[8] == "pending":
            usage_sheet.update_cell(i + 1, 9, "cancelled")
            cancelled += 1
    if cancelled > 0:
        await interaction.response.send_message(f"✅ ยกเลิกทั้งหมด {cancelled} รายการเรียบร้อย", ephemeral=True)
    else:
        await interaction.response.send_message("❌ ไม่พบ UUID ที่ระบุหรือไม่สามารถยกเลิกได้", ephemeral=True)

@stock_cancel.autocomplete("uuid_codes")
async def autocomplete_cancel_uuid(interaction: discord.Interaction, current: str):
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    today_date = datetime.now().date().isoformat()
    options = []
    for row in records[1:]:
        if row[1][:10] == today_date and row[8] == "pending" and current.lower() in row[0].lower():
            options.append(app_commands.Choice(name=f"{row[0]} | {row[5]}", value=f"{row[0]} | {row[5]}"))
        if len(options) >= 20:
            break
    return options

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
