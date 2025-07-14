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

class EquipmentSelectView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.equipment_select = Select(
            placeholder="เลือกอุปกรณ์ที่ใช้ประจำ",
            options=[
                discord.SelectOption(label="TRT-หมวก"),
                discord.SelectOption(label="TRT-Milky ทำความสะอาด"),
                discord.SelectOption(label="TRT-ยาชา"),
                discord.SelectOption(label="TRT-กกน"),
                discord.SelectOption(label="TRT-ชุดทำความสะอาด+บำรุง"),
                discord.SelectOption(label="แล็ปยาชาหน้ากาก"),
            ],
            min_values=0,
            max_values=5
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
        self.branch_input = TextInput(label="สาขา (เช่น เซ็นทรัลระยอง)", required=True)
        self.add_item(self.customer_input)
        self.add_item(self.branch_input)
        self.treatment_inputs = []
        self.therapist_inputs = []
        for i in range(5):
            treatment_input = TextInput(label=f"Treatment {i+1}", required=False)
            therapist_input = TextInput(label=f"Therapist {i+1}", required=False)
            self.add_item(treatment_input)
            self.add_item(therapist_input)
            self.treatment_inputs.append(treatment_input)
            self.therapist_inputs.append(therapist_input)

    async def on_submit(self, interaction: discord.Interaction):
        usage_sheet = spreadsheet.worksheet("treatment_usage")
        today = datetime.now().isoformat()
        branch = self.branch_input.value.strip()
        customer = self.customer_input.value.strip()
        group_id = str(uuid.uuid4())

        treatment_pairs = []
        for treatment_input, therapist_input in zip(self.treatment_inputs, self.therapist_inputs):
            treatment = treatment_input.value.strip()
            therapist = therapist_input.value.strip()
            if treatment and therapist:
                usage_sheet.append_row([
                    str(uuid.uuid4()), today, branch, treatment, 1, customer, therapist, group_id, "pending"
                ])
                treatment_pairs.append(f"- {treatment} | {therapist}")

        for equipment in self.equipments:
            usage_sheet.append_row([
                str(uuid.uuid4()), today, branch, equipment, 1, customer, "อุปกรณ์", group_id, "pending"
            ])
        channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
        summary_msg = f"✅ บันทึก Treatment สำหรับ {customer} สาขา {branch}\nGroup UUID: {group_id}\n" + "\n".join(treatment_pairs)
        if self.equipments:
            summary_msg += f"\n- อุปกรณ์: {', '.join(self.equipments)}"
        await channel.send(summary_msg)
        await interaction.response.send_message(f"✅ บันทึกเรียบร้อย Group UUID: {group_id}", ephemeral=True)

@tree.command(name="stock_ส่งทรีตเมนต์", description="ส่งทรีตเมนต์หลายรายการสำหรับลูกค้าคนเดียว")
async def stock_cut_multi(interaction: discord.Interaction):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.send_message("เลือกอุปกรณ์ที่ใช้ก่อน แล้วกด ยืนยันและลงข้อมูล", view=EquipmentSelectView(), ephemeral=True)

@tree.command(name="stock_เพิ่ม", description="เพิ่มสต๊อกสินค้า (Admin)")
async def stock_add(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int):
    if interaction.channel_id not in [ADMIN_CHANNEL_ID, ADMIN_ONLY_CHANNEL_ID]:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    stock_sheet.append_row([สาขา, treatment, จำนวน])
    await interaction.response.send_message(f"✅ เพิ่ม {treatment} {จำนวน} ชิ้น ให้กับ {สาขา}")

@tree.command(name="stock_คงเหลือ", description="เช็คสต๊อกคงเหลือตามสาขา")
async def stock_check(interaction: discord.Interaction, สาขา: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    records = stock_sheet.get_all_values()
    msg = f"📦 สต๊อกคงเหลือ {สาขา}:
"
    for row in records[1:]:
        if row[0] == สาขา:
            msg += f"- {row[1]}: {row[2]} ชิ้น
"
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
    msg = "📊 รายการทรีตเมนต์วันนี้
"
    count = 0
    for row in records[1:]:
        if row[1][:10] == today_date:
            msg += f"• ลูกค้า: {row[5]}, Therapist: {row[6]}, Treatment: {row[3]}, สาขา: {row[2]}
"
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
    msg = "📊 สรุปทรีตเมนต์วันนี้แยกตามพนักงาน
"
    if summary:
        for therapist, total in summary.items():
            msg += f"- {therapist}: {total} รายการ
"
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
