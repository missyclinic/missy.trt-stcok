import discord
from discord.ext import commands
from discord.ui import Modal, View, Select, TextInput, Button
from flask import Flask
from threading import Thread
import os

TOKEN = os.getenv("TOKEN")
OWNER_ID = 1391657596037103718

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

branches = ["ระยอง", "บางนา", "เชียงใหม่"]
employees = ["A", "B", "C", "D", "E"]

class SalesModal(Modal):
    def __init__(self, branches, employees):
        super().__init__(title="บันทึกยอดขาย")
        self.branches = branches
        self.employees = employees

        self.add_item(TextInput(label="ยอดรวมก่อนหัก (บาท)", custom_id="total_amount", placeholder="เช่น 20000", required=True))
        self.add_item(Select(placeholder="เลือกสาขา", options=[discord.SelectOption(label=b) for b in branches]))
        self.add_item(Select(placeholder="เลือกประเภท", options=[discord.SelectOption(label=t) for t in ["NP", "RP", "BL", "WI", "FB"]]))
        self.add_item(TextInput(label="ชื่อลูกค้า", custom_id="customer_name", placeholder="ระบุชื่อ", required=True))
        self.add_item(TextInput(label="รายละเอียดการขาย", custom_id="details", placeholder="เช่น Super Slim...", required=True))
        self.add_item(Select(placeholder="เลือกรายการหัก", min_values=0, max_values=3, options=[
            discord.SelectOption(label="หักหัตถการ 10%", value="htk"),
            discord.SelectOption(label="หักรูดบัตร 7%", value="rd"),
            discord.SelectOption(label="หักผ่อน 10%", value="pn")
        ]))

    async def on_submit(self, interaction: discord.Interaction):
        total_amount = float(self.children[0].value)
        deduct_select: Select = self.children[5]
        deducts = deduct_select.values

        total_deduct = 0
        if "htk" in deducts:
            total_deduct += total_amount * 0.10
        if "rd" in deducts:
            total_deduct += total_amount * 0.07
        if "pn" in deducts:
            total_deduct += total_amount * 0.10

        remaining = total_amount - total_deduct
        await interaction.response.send_message(
            f"ยอดขายรวม: {total_amount:.2f} บาท\nยอดหักรวม: {total_deduct:.2f} บาท\nยอดคงเหลือ: {remaining:.2f} บาท\n**กรุณากรอกยอดของพนักงานให้ครบ {remaining:.2f} บาท ผ่านคำสั่งถัดไป**",
            ephemeral=True
        )

@bot.tree.command(name="ยอดขาย", description="บันทึกยอดขายของพนักงาน")
async def sales(interaction: discord.Interaction):
    await interaction.response.send_modal(SalesModal(branches, employees))

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is ready.")

# Flask Keep Alive
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(TOKEN)
