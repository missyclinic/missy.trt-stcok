import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Select, Button
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
treatment_sheet = spreadsheet.worksheet("treatment_list")
therapist_sheet = spreadsheet.worksheet("therapist_list")
TREATMENTS = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

class EquipmentSelectView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.equipment_select = Select(
            placeholder="เลือกอุปกรณ์ที่ใช้ประจำ",
            options=[discord.SelectOption(label=item) for item in [
                "TRT-หมวก", "TRT-Milky ทำความสะอาด", "TRT-ยาชา",
                "TRT-กกน", "TRT-ชุดทำความสะอาด+บำรุง", "แล็ปยาชาหน้ากาก"
            ]],
            min_values=0, max_values=6
        )
        self.add_item(self.equipment_select)
        self.confirm_button = Button(label="ยืนยันและลงข้อมูล", style=discord.ButtonStyle.green)
        self.confirm_button.callback = self.confirm_callback
        self.add_item(self.confirm_button)

    async def confirm_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MultiTreatmentModal(self.equipment_select.values))

class MultiTreatmentModal(Modal):
    def __init__(self, equipments):
        super().__init__(title="ลง Treatment ลูกค้าหนึ่งคน")
        self.equipments = equipments
        self.customer_input = TextInput(label="ชื่อลูกค้า", required=True)
        self.branch_input = TextInput(label="สาขา", required=True)
        self.treatment_input = TextInput(label="Treatment", required=True)
        self.therapist_input = TextInput(label="Therapist", required=True)
        self.add_item(self.customer_input)
        self.add_item(self.branch_input)
        self.add_item(self.treatment_input)
        self.add_item(self.therapist_input)

    async def on_submit(self, interaction: discord.Interaction):
        usage_sheet = spreadsheet.worksheet("treatment_usage")
        today = datetime.now().isoformat()
        group_id = str(uuid.uuid4())
        rows = [
            [str(uuid.uuid4()), today, self.branch_input.value.strip(), self.treatment_input.value.strip(), 1,
             self.customer_input.value.strip(), self.therapist_input.value.strip(), group_id, "pending"]
        ]
        for equipment in self.equipments:
            rows.append([str(uuid.uuid4()), today, self.branch_input.value.strip(), equipment, 1,
                         self.customer_input.value.strip(), "อุปกรณ์", group_id, "pending"])
        usage_sheet.append_rows(rows)
        await interaction.response.send_message(f"✅ บันทึกเรียบร้อย Group UUID: {group_id}", ephemeral=True)

@tree.command(name="stock_ส่งทรีตเมนต์", description="ส่งทรีตเมนต์หลายรายการสำหรับลูกค้าคนเดียว")
async def stock_cut_multi(interaction: discord.Interaction):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.send_message("เลือกอุปกรณ์ที่ใช้ก่อน แล้วกด ยืนยันและลงข้อมูล", view=EquipmentSelectView(), ephemeral=True)

@tree.command(name="stock_เพิ่ม", description="เพิ่มสต๊อกสินค้า (Admin)")
@app_commands.autocomplete(สาขา=lambda i, c: [app_commands.Choice(name=b, value=b) for b in BRANCHES if c.lower() in b.lower()])
@app_commands.autocomplete(treatment=lambda i, c: [app_commands.Choice(name=t, value=t) for t in TREATMENTS if c.lower() in t.lower()])
async def stock_add(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int):
    if interaction.channel_id not in [ADMIN_CHANNEL_ID, ADMIN_ONLY_CHANNEL_ID]:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    stock_sheet = spreadsheet.worksheet("stock_list")
    stock_sheet.append_row([สาขา, treatment, จำนวน])
    await interaction.response.send_message(f"✅ เพิ่ม {treatment} {จำนวน} ชิ้น ให้กับ {สาขา}")

@tree.command(name="stock_คงเหลือ", description="เช็คสต๊อกคงเหลือตามสาขา")
@app_commands.autocomplete(สาขา=lambda i, c: [app_commands.Choice(name=b, value=b) for b in BRANCHES if c.lower() in b.lower()])
async def stock_check(interaction: discord.Interaction, สาขา: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    stock_sheet = spreadsheet.worksheet("stock_list")
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
    updated = sum(1 for i, row in enumerate(records) if row[7] == group_uuid and row[8] == "pending" and usage_sheet.update_cell(i + 1, 9, "completed"))
    await interaction.response.send_message(f"✅ ยืนยันกลุ่ม {group_uuid} ทั้งหมด {updated} รายการ" if updated else "❌ ไม่พบหรือยืนยันไปแล้ว", ephemeral=True)

@tree.command(name="รายงานทรีตเมนต์วันนี้", description="ดูรายการทรีตเมนต์ทั้งหมดที่ถูกส่งวันนี้")
async def treatment_report_today(interaction: discord.Interaction):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    today_date = datetime.now().date().isoformat()
    msg = "📊 รายการทรีตเมนต์วันนี้\n"
    records = usage_sheet.get_all_values()
    msg += "\n".join(f"• ลูกค้า: {row[5]}, Therapist: {row[6]}, Treatment: {row[3]}, สาขา: {row[2]}" for row in records[1:] if row[1][:10] == today_date) or "ไม่มีรายการวันนี้"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="รายงานทรีตเมนต์ลายพนักงาน", description="ดูสรุปการใช้ทรีตเมนต์แยกตามพนักงานวันนี้")
async def treatment_summary_by_therapist(interaction: discord.Interaction):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    today_date = datetime.now().date().isoformat()
    records = usage_sheet.get_all_values()
    summary = defaultdict(int)
    for row in records[1:]:
        if row[1][:10] == today_date and row[8] == "completed":
            summary[row[6]] += 1
    msg = "📊 สรุปทรีตเมนต์วันนี้แยกตามพนักงาน\n" + "\n".join(f"- {k}: {v} รายการ" for k, v in summary.items()) if summary else "ไม่มีรายการวันนี้"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="stock_ยกเลิกบางรายการ", description="ยกเลิก Treatment หลายรายการ")
@app_commands.describe(uuid_codes="เลือก UUID หลายรายการ พร้อมแสดงชื่อลูกค้าและ Treatment")
async def stock_cancel(interaction: discord.Interaction, uuid_codes: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    uuid_list = [u.split("|")[0].strip() for u in uuid_codes.split(",") if u.strip()]
    cancelled = sum(1 for i, row in enumerate(records) if row[0] in uuid_list and row[8] == "pending" and usage_sheet.update_cell(i + 1, 9, "cancelled"))
    await interaction.response.send_message(f"✅ ยกเลิกทั้งหมด {cancelled} รายการเรียบร้อย" if cancelled else "❌ ไม่พบ UUID ที่ระบุหรือไม่สามารถยกเลิกได้", ephemeral=True)

@stock_cancel.autocomplete("uuid_codes")
async def autocomplete_cancel_uuid(interaction: discord.Interaction, current: str):
    usage_sheet = spreadsheet.worksheet("treatment_usage")
    today_date = datetime.now().date().isoformat()
    options = []
    records = usage_sheet.get_all_values()
    for row in records[1:]:
        if row[1][:10] == today_date and row[8] == "pending" and current.lower() in row[0].lower():
            options.append(app_commands.Choice(name=f"{row[0]} | {row[5]} | {row[3]}", value=f"{row[0]} | {row[5]} | {row[3]}"))
        if len(options) >= 20:
            break
    return options

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
