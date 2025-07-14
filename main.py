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

class MultiTreatmentModal(Modal):
    treatments_autocomplete = [t.lower() for t in TREATMENTS]
    therapists_autocomplete = [t.lower() for t in THERAPISTS]
    def __init__(self):
        super().__init__(title="ลง Treatment ลูกค้าหนึ่งคน")
        self.customer_input = TextInput(label="ชื่อลูกค้า", required=True)
        self.branch_input = TextInput(label="สาขา (เช่น เซ็นทรัลระยอง)", required=True)
        self.add_item(self.customer_input)
        self.add_item(self.branch_input)
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
        for treatment_input, therapist_input in zip(self.treatment_inputs, self.therapist_inputs):
            if treatment_input.value and therapist_input.value:
            if treatment_input.value.lower() not in self.treatments_autocomplete:
                error_messages.append(f"❌ ไม่พบ Treatment: {treatment_input.value}")
                continue
            if therapist_input.value.lower() not in self.therapists_autocomplete:
                error_messages.append(f"❌ ไม่พบ Therapist: {therapist_input.value}")
                continue
                usage_sheet.append_row([
                    str(uuid.uuid4()), today, branch, treatment_input.value, 1, customer, therapist_input.value
                ])
        if error_messages:
            await interaction.response.send_message("\n".join(error_messages), ephemeral=True)
            return
        await interaction.response.send_message("✅ บันทึก Treatment เรียบร้อย")

@tree.command(name="stock_ตัดหลาย", description="ตัดสต๊อกหลาย Treatment สำหรับลูกค้าคนเดียว")
async def stock_cut_multi(interaction: discord.Interaction):
    if interaction.channel_id != TREATMENT_CHANNEL_ID:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในห้อง Treatment Log", ephemeral=True)
        return
    await interaction.response.send_modal(MultiTreatmentModal())

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
