import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
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

# เปิดชีท
treatment_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_list")
therapist_sheet = client.open("Stock Treatment Log CRY").worksheet("therapist_list")

TREATMENTS = treatment_sheet.col_values(1)[1:]
THERAPISTS = therapist_sheet.col_values(1)[1:]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

stock_data = defaultdict(lambda: defaultdict(int))
usage_log = []

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 139411551234567890
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="stock_เพิ่ม", description="เพิ่มสต๊อกสินค้า (Admin)")
async def stock_add(interaction: discord.Interaction, สาขา: str, treatment: str, จำนวน: int):
    if interaction.channel_id not in [ADMIN_CHANNEL_ID, ADMIN_ONLY_CHANNEL_ID]:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    stock_data[สาขา][treatment] += จำนวน
    await interaction.response.send_message(f"✅ เพิ่ม {treatment} {จำนวน} ชิ้น ให้กับ {สาขา}")

@tree.command(name="stock_คงเหลือ", description="เช็คสต๊อกคงเหลือตามสาขา")
async def stock_check(interaction: discord.Interaction, สาขา: str):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Stock Management", ephemeral=True)
        return
    msg = f"📦 สต๊อกคงเหลือ {สาขา}:\n"
    for t in TREATMENTS:
        qty = stock_data[สาขา][t]
        msg += f"- {t}: {qty} ชิ้น\n"
    await interaction.response.send_message(msg)

from discord.ui import Select

class MultiTreatmentModal(Modal):
    treatments_autocomplete = [t.lower() for t in TREATMENTS]
    therapists_autocomplete = [t.lower() for t in THERAPISTS]
    def __init__(self):
        equipment_options = [
            discord.SelectOption(label="TRT-หมวก", description="หมวก"),
            discord.SelectOption(label="TRT-Milky ทำความสะอาด", description="มิลกี้"),
            discord.SelectOption(label="TRT-ยาชา", description="ยาชา"),
            discord.SelectOption(label="TRT-กกน", description="กางเกงใน"),
            discord.SelectOption(label="TRT-ชุดทำความสะอาด+บำรุง", description="ชุดทำความสะอาด"),
            discord.SelectOption(label="แล็ปยาชาหน้ากาก", description="แลบหน้ากาก")
        ]
        super().__init__(title="ลง Treatment ลูกค้าหนึ่งคน")
        self.customer_input = TextInput(label="ชื่อลูกค้า", required=True)
        self.branch_input = TextInput(label="สาขา (เช่น เซ็นทรัลระยอง)", required=True)
        self.add_item(self.customer_input)
        self.add_item(self.branch_input)
        self.equipment_select = Select(placeholder="เลือกอุปกรณ์ที่ใช้ประจำ", options=equipment_options, min_values=0, max_values=len(equipment_options))
        self.add_item(self.equipment_select)
        self.treatment_inputs = []
        self.therapist_inputs = []
        for i in range(5):
            treatment_input = TextInput(label=f"Treatment {i+1}", required=False, placeholder="พิมพ์ชื่อ Treatment เช่น Qskin")
            therapist_input = TextInput(label=f"Therapist {i+1}", required=False, placeholder="พิมพ์ชื่อพนักงาน เช่น ปาร์ตี้SM")
            self.add_item(treatment_input)
            self.add_item(therapist_input)
            self.treatment_inputs.append(treatment_input)
            self.therapist_inputs.append(therapist_input)
    async def on_submit(self, interaction: discord.Interaction):
        error_messages = []
        usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
        today = datetime.now().isoformat()
        branch = self.branch_input.value.strip()
        customer = self.customer_input.value.strip()
        today_str = datetime.now().strftime("%Y-%m-%d")
        records = usage_sheet.get_all_values()
        existing_group_id = None
        for row in records[1:]:
            if row[1][:10] == today_str and row[5] == customer and row[2] == branch:
                existing_group_id = row[7]
                break
        group_id = existing_group_id if existing_group_id else str(uuid.uuid4())
        for treatment_input, therapist_input in zip(self.treatment_inputs, self.therapist_inputs):
            if treatment_input.value and therapist_input.value:
                if treatment_input.value.lower() not in self.treatments_autocomplete:
                    error_messages.append(f"❌ ไม่พบ Treatment: {treatment_input.value}")
                    continue
                if therapist_input.value.lower() not in self.therapists_autocomplete:
                    error_messages.append(f"❌ ไม่พบ Therapist: {therapist_input.value}")
                    continue
                usage_sheet.append_row([
                    str(uuid.uuid4()), today, branch, treatment_input.value, 1, customer, therapist_input.value, group_id, "pending"
                ])
        for equipment in self.equipment_select.values:
            usage_sheet.append_row([
                str(uuid.uuid4()), today, branch, equipment, 1, customer, "อุปกรณ์", group_id, "pending"
            ])

        for treatment_input, therapist_input in zip(self.treatment_inputs, self.therapist_inputs):
            if treatment_input.value and therapist_input.value:
                if treatment_input.value.lower() not in self.treatments_autocomplete:
                    error_messages.append(f"❌ ไม่พบ Treatment: {treatment_input.value}")
                    continue
                if therapist_input.value.lower() not in self.therapists_autocomplete:
                    error_messages.append(f"❌ ไม่พบ Therapist: {therapist_input.value}")
                    continue
                usage_sheet.append_row([
                    str(uuid.uuid4()), today, branch, treatment_input.value, 1, customer, therapist_input.value, group_id, "pending"
                ])
                if therapist_input.value.lower() not in self.therapists_autocomplete:
                    error_messages.append(f"❌ ไม่พบ Therapist: {therapist_input.value}")
                    continue
                usage_sheet.append_row([
                    str(uuid.uuid4()), today, branch, treatment_input.value, 1, customer, therapist_input.value, group_id, "pending"
                ])
        if error_messages:
            await interaction.response.send_message("\n".join(error_messages), ephemeral=True)

            return
        summary_msg = (
            f"✅ บันทึก Treatment เรียบร้อย\n"
            f"ลูกค้า: {customer}\n"
            f"สาขา: {branch}\n"
            f"Group UUID: {group_id}\n\n"
            f"📋 รายการที่ส่ง:\n"
            )
        for treatment_input, therapist_input in zip(self.treatment_inputs, self.therapist_inputs):
            if treatment_input.value and therapist_input.value:
                summary_msg += f"- {treatment_input.value} | {therapist_input.value}"
        channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
        await channel.send(summary_msg)
        await interaction.response.send_message("✅ ส่งสรุปไปที่ห้อง Treatment Log เรียบร้อยแล้ว", ephemeral=True)

@tree.command(name="stock_ส่งทรีตเมนต์", description="ส่งทรีตเมนต์หลายรายการสำหรับลูกค้าคนเดียว")
async def stock_cut_multi(interaction: discord.Interaction):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.send_modal(MultiTreatmentModal())

@tree.command(name="พนักงานรับทรีตเมนต์ยืนยัน", description="พนักงานยืนยันว่าได้รับทรีตเมนต์ในกลุ่มนั้นแล้ว")
async def stock_confirm_group(interaction: discord.Interaction, group_uuid: str):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
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
    usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    today_date = datetime.now().date().isoformat()
    msg = "📊 รายการทรีตเมนต์วันนี้"
    treatment_count = defaultdict(lambda: defaultdict(int))
    count = 0
    for row in records[1:]:
        if row[1][:10] == today_date:
            treatment_count[row[2]][row[3]] += 1
            treatment_count[row[3]] += 1
            msg += f"• ลูกค้า: {row[5]}, Therapist: {row[6]}, Treatment: {row[3]}, สาขา: {row[2]}"
            count += 1
    if count == 0:
        msg += "ไม่มีรายการวันนี้"
    else:
        msg += "📋 สรุปจำนวนตาม Treatment แยกตามสาขา"
        for branch, treatments in treatment_count.items():
            msg += f"📍 {branch}"
            for treatment, total in treatments.items():
                msg += f"- {treatment}: {total} รายการ"

            msg += f"- {treatment}: {total} รายการ"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="รายงานทรีตเมนต์ลายพนักงาน", description="ดูสรุปการใช้ทรีตเมนต์แยกตามพนักงานวันนี้")
async def treatment_summary_by_therapist(interaction: discord.Interaction):
    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
    records = usage_sheet.get_all_values()
    today_date = datetime.now().date().isoformat()
    summary = defaultdict(int)
    for row in records[1:]:
        if row[1][:10] == today_date and row[8] == "completed":
            summary[row[6]] += 1
    msg = "📊 สรุปทรีตเมนต์วันนี้แยกตามพนักงาน"
    if summary:
        for therapist, total in summary.items():
            msg += f"- {therapist}: {total} รายการ"
    else:
        msg += "ไม่มีรายการวันนี้"
    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="stock_ยกเลิกบางรายการ", description="ยกเลิก Treatment หลายรายการ")
@app_commands.describe(uuid_codes="เลือก UUID หลายรายการ พร้อมแสดงชื่อลูกค้า")
async def stock_cancel(interaction: discord.Interaction, uuid_codes: str):
    ...

@stock_cancel.autocomplete("uuid_codes")
async def autocomplete_cancel_uuid(interaction: discord.Interaction, current: str):
    ...

    if interaction.channel_id != ADMIN_ONLY_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Admin Only", ephemeral=True)
        return
    usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
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

async def autocomplete_cancel_uuid(interaction: discord.Interaction, current: str):
    usage_sheet = client.open("Stock Treatment Log CRY").worksheet("treatment_usage")
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
