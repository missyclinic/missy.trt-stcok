import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
from typing import Optional

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

TREATMENTS_SPLIT_1 = ["TRT-TURBO 5G", "TRT-Super Shape", "TRT-Super Block", "TRT-Super Firm", "TRT-RELAX", "TRT-Reset Body Skin", "TRT-Gold 24K Body", "TRT-Revive (BODY)", "TRT-Revive- Reduce Booster", "TRT-Revive - Immune System Booster", "TRT-Body Scrub", "TRT-Body Mask", "TRT-Back Acne Treatment (สิวหลัง)", "TRT-Breast Massage 15min", "TRT-Breast Massage & Machine(M9)", "TRT-Slim XS", "TRT-Slim FITS", "TRT-Slim Burm", "TRT-Migraine Relief", "TRT-Super Slim - 30min", "TRT-Super Slim - 15min", "TRT-Super Scrub (เฉพาะจุด)", "TRT-Reset (เช็ดเฉพาะรักแร้)", "TRT-Balance (A,B)", "เจลกายภาพ (3P)"]

TREATMENTS_SPLIT_2 = ["เจลกายภาพ (5P)", "TRT-กกน", "TRT Boxer", "TRT-หมวก", "TRT-ยาชา", "TRT - Shining skin -Botox", "TRT - Shining skin -Collagen", "TRT - Shining skin -Acne", "TRT - Shining skin -Glow", "TRT - Shining skin Pro - 2P", "TRT-Perfect mask -Charcoal", "TRT-Perfact mask -Bulgarian Rose", "TRT-Perfect mask -Anti-Aging", "TRT-Perfect mask -Vit-C", "TRT-Eye action", "TRT-Missy SkinCell", "TRT-Face Lift  5D", "TRT-Revive Face", "TRT-Golden Aura", "TRT-24K Facial Scrub", "TRT-OXY SKIN CELL", "TRT-ชุดทำความสะอาด+บำรุง", "TRT-Milky ทำความสะอาด", "TRT-Water Micellar ทำความสะอาดก่อนกดสิว", "Magnet SkinPro - Peel exfoliator"]

TREATMENTS_SPLIT_3 = ["TRT-Revive (HAIR)", "Magnet SkinPro - Wish Care", "Magnet SkinPro - BTX", "Magnet SkinPro - Brightening", "Magnet SkinPro - Neo Energy", "Magnet SkinPro -Collagen", "Magnet SkinPro -Hyaluronic", "Magnet SkinPro - Repairing", "TRT-whitamin C", "TRT-GEL กำจัดขน 3P", "TRT-GEL กำจัดขน 1P", "TRT-GEL 9D", "TRT-Missy Vaginal Repair Cream", "TRT-MISSY MADE+", "TCL - IV AURA-WINK-WHITE ตัวยา", "TCL - IV AURA 100ml. ตัวยา", "TCL-IV AURA 20ml PRO ตัวยา", "TCL-IV FAT BUNRNER ตัวยา", "TRT-MESO AURA 1ML", "แล็ปยาชาหน้ากาก", "มีดโกน 1อัน", "บังทรง"]

THERAPISTS = ["วิ PRY", "รัก PRY", "ปาร์ตี้ SM", "คนที่ 4", "คนที่ 5", "คนที่ 6", "คนที่ 7"]
BRANCHES = ["เซ็นทรัลระยอง", "แพชชั่นระยอง", "พระราม2"]

ADMIN_CHANNEL_ID = 1394115416049061918
ADMIN_ONLY_CHANNEL_ID = 1394133334317203476
TREATMENT_CHANNEL_ID = 1394115507883606026

@tree.command(name="ส่งtrt", description="บันทึกทรีตเมนต์พร้อมอุปกรณ์")
@app_commands.describe(
    สาขา="เลือกสาขา",
    ลูกค้า="ชื่อลูกค้า",
    ใช้_หมวก="ใช้ TRT-หมวก หรือไม่",
    ใช้_กกน="ใช้ TRT-กกน หรือไม่",
    ใช้_ชุดทำความสะอาด="ใช้ TRT-ชุดทำความสะอาด+บำรุง หรือไม่",
    ใช้_milky="ใช้ TRT-Milky ทำความสะอาด หรือไม่",
    ใช้_ยาชา="ใช้ TRT-ยาชา หรือไม่",
    ใช้_แล็ปยาชา="ใช้ แล็ปยาชาหน้ากาก หรือไม่",
    treatment1_1="ทรีตเมนต์ 1 กลุ่ม 1",
    treatment1_2="ทรีตเมนต์ 1 กลุ่ม 2",
    treatment1_3="ทรีตเมนต์ 1 กลุ่ม 3",
    therapist1="พนักงาน 1",
    treatment2_1="ทรีตเมนต์ 2 กลุ่ม 1",
    treatment2_2="ทรีตเมนต์ 2 กลุ่ม 2",
    treatment2_3="ทรีตเมนต์ 2 กลุ่ม 3",
    therapist2="พนักงาน 2",
    treatment3_1="ทรีตเมนต์ 3 กลุ่ม 1",
    treatment3_2="ทรีตเมนต์ 3 กลุ่ม 2",
    treatment3_3="ทรีตเมนต์ 3 กลุ่ม 3",
    therapist3="พนักงาน 3"
)
@app_commands.choices(
    สาขา=[app_commands.Choice(name=b, value=b) for b in BRANCHES],
    treatment1_1=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_1],
    treatment1_2=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_2],
    treatment1_3=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_3],
    therapist1=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    treatment2_1=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_1],
    treatment2_2=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_2],
    treatment2_3=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_3],
    therapist2=[app_commands.Choice(name=t, value=t) for t in THERAPISTS],
    treatment3_1=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_1],
    treatment3_2=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_2],
    treatment3_3=[app_commands.Choice(name=t, value=t) for t in TREATMENTS_SPLIT_3],
    therapist3=[app_commands.Choice(name=t, value=t) for t in THERAPISTS]
)
async def ส่งtrt(interaction: discord.Interaction, สาขา: str, ลูกค้า: str,
                 ใช้_หมวก: Optional[bool] = False,
                 ใช้_กกน: Optional[bool] = False,
                 ใช้_ชุดทำความสะอาด: Optional[bool] = False,
                 ใช้_milky: Optional[bool] = False,
                 ใช้_ยาชา: Optional[bool] = False,
                 ใช้_แล็ปยาชา: Optional[bool] = False,
                 treatment1_1: Optional[str] = None, treatment1_2: Optional[str] = None, treatment1_3: Optional[str] = None, therapist1: Optional[str] = None,
                 treatment2_1: Optional[str] = None, treatment2_2: Optional[str] = None, treatment2_3: Optional[str] = None, therapist2: Optional[str] = None,
                 treatment3_1: Optional[str] = None, treatment3_2: Optional[str] = None, treatment3_3: Optional[str] = None, therapist3: Optional[str] = None):

    await interaction.response.defer(thinking=True)
    today_date = datetime.now().strftime("%Y-%m-%d")
    group_id = f"{today_date.replace('-', '')}-{str(uuid.uuid4())[:6]}"
    msg = f"✅ บันทึกทรีตเมนต์สำหรับ\nชื่อลูกค้า {ลูกค้า}\nทำที่ : {สาขา}\nGroup ID: {group_id}\nรายการ TRT\n"
    treatments = [
        (treatment1_1 or treatment1_2 or treatment1_3, therapist1),
        (treatment2_1 or treatment2_2 or treatment2_3, therapist2),
        (treatment3_1 or treatment3_2 or treatment3_3, therapist3)
    ]
    for t, p in treatments:
        if t and p:
            msg += f"- {t} | {p}\n"
    equipment_list = []
    if ใช้_หมวก:
        equipment_list.append("TRT-หมวก")
    if ใช้_กกน:
        equipment_list.append("TRT-กกน")
    if ใช้_ชุดทำความสะอาด:
        equipment_list.append("TRT-ชุดทำความสะอาด+บำรุง")
    if ใช้_milky:
        equipment_list.append("TRT-Milky ทำความสะอาด")
    if ใช้_ยาชา:
        equipment_list.append("TRT-ยาชา")
    if ใช้_แล็ปยาชา:
        equipment_list.append("แล็ปยาชาหน้ากาก")
    msg += f"อุปกรณ์: {', '.join(equipment_list)}" if equipment_list else "ไม่มีอุปกรณ์"
    channel = interaction.guild.get_channel(TREATMENT_CHANNEL_ID)
    await channel.send(msg)
    await interaction.followup.send(f"✅ บันทึกเรียบร้อย Group ID: {group_id}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot {bot.user} พร้อมใช้งาน")

bot.run(TOKEN)
