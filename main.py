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
EQUIPMENTS = ["TRT-หมวก", "TRT-Milky ทำความสะอาด", "TRT-ยาชา", "TRT-กกน", "TRT-ชุดทำความสะอาด+บำรุง", "แล็ปยาชาหน้ากาก"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

class EquipmentMultiSelectView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.equipment_select = Select(
            placeholder="เลือกอุปกรณ์ที่ใช้",
            options=[discord.SelectOption(label=e) for e in EQUIPMENTS],
            min_values=0,
            max_values=len(EQUIPMENTS)
        )
        self.add_item(self.equipment_select)
        self.confirm_button = Button(label="ยืนยัน", style=discord.ButtonStyle.green)
        self.confirm_button.callback = self.confirm_callback
        self.add_item(self.confirm_button)

    async def confirm_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"คุณเลือกอุปกรณ์: {', '.join(self.equipment_select.values)}", ephemeral=True)

@tree.command(name="เลือกอุปกรณ์", description="เลือกอุปกรณ์หลายรายการ")
async def choose_equipment(interaction: discord.Interaction):
    await interaction.response.send_message("กรุณาเลือกอุปกรณ์", view=EquipmentMultiSelectView(), ephemeral=True)

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
@app_commands.choices(
    สาขา=[app_commands.Choice(name=b, value=b) for b in BRANCHES]
)
async def ลงทรีตเมนต์(interaction: discord.Interaction,
    สาขา: app_commands.Choice[str],
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
            usage_sheet.append_row([str(uuid.uuid4()), today, สาขา.value, treatment, 1, ลูกค้า, therapist, group_id, "pending"])
            summary.append(f"- {treatment} | {therapist}")

    msg = f"✅ บันทึก Treatment สำหรับ {ลูกค้า} สาขา {สาขา.value}\nGroup UUID: {group_id}\n" + "\n".join(summary)
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
