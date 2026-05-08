import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ─── Config ───────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
ALLOWED_CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0)) or None
DATA_FILE = "accounts.json"

# ─── Setup ────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Data Helpers ─────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def channel_check(interaction: discord.Interaction):
    if ALLOWED_CHANNEL_ID and interaction.channel_id != ALLOWED_CHANNEL_ID:
        return False
    return True

def find_account(data, name):
    return next((k for k in data if k.lower() == name.lower()), None)

def build_embed(title, acc, name, color):
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="🏷️ الاسم", value=f"`{name}`", inline=True)
    embed.add_field(name="🎮 PSN", value=f"`{acc['psn']}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="📧 Mail", value=f"`{acc['mail']}`", inline=True)
    embed.add_field(name="🔑 Pass", value=f"||`{acc['password']}`||", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="🔰 OGE", value=f"`{acc['oge']}`", inline=True)
    embed.add_field(name="📅 DOB", value=f"`{acc['dob']}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.set_footer(text=f"🕒 {acc.get('added_at', '—')}")
    return embed

# ─── Events ───────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} شغّال!")

# ─── Add Modal ────────────────────────────────────────────
class AddModal(discord.ui.Modal, title="🖤 إضافة حساب جديد"):
    psn = discord.ui.TextInput(label="PSN", placeholder="أدخل PSN ID", required=True)
    mail = discord.ui.TextInput(label="Mail", placeholder="أدخل الإيميل", required=False)
    password = discord.ui.TextInput(label="Pass", placeholder="أدخل الباسورد", required=False)
    oge = discord.ui.TextInput(label="OGE", placeholder="أدخل OGE", required=False)
    dob = discord.ui.TextInput(label="DOB", placeholder="مثال: 2000-11-11", required=False)

    def __init__(self, name: str):
        super().__init__()
        self.account_name = name

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()

        if find_account(data, self.account_name):
            await interaction.response.send_message(
                f"⚠️ الحساب **{self.account_name}** موجود مسبقاً. استخدم `/edit`.", ephemeral=True
            )
            return

        acc = {
            "psn": str(self.psn),
            "mail": str(self.mail) or "—",
            "password": str(self.password) or "—",
            "oge": str(self.oge) or "—",
            "dob": str(self.dob) or "—",
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data[self.account_name] = acc
        save_data(data)

        embed = build_embed("✅ تم إضافة الحساب", acc, self.account_name, 0x2ecc71)
        await interaction.response.send_message(embed=embed)

# ─── Edit Modal ───────────────────────────────────────────
class EditModal(discord.ui.Modal, title="✏️ تعديل الحساب"):
    psn = discord.ui.TextInput(label="PSN", required=False)
    mail = discord.ui.TextInput(label="Mail", required=False)
    password = discord.ui.TextInput(label="Pass", required=False)
    oge = discord.ui.TextInput(label="OGE", required=False)
    dob = discord.ui.TextInput(label="DOB", required=False)

    def __init__(self, name: str, acc: dict):
        super().__init__()
        self.account_name = name
        self.psn.default = acc["psn"]
        self.mail.default = acc["mail"] if acc["mail"] != "—" else ""
        self.password.default = acc["password"] if acc["password"] != "—" else ""
        self.oge.default = acc["oge"] if acc["oge"] != "—" else ""
        self.dob.default = acc["dob"] if acc["dob"] != "—" else ""

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        match = find_account(data, self.account_name)
        if not match:
            await interaction.response.send_message("❌ الحساب ما موجود.", ephemeral=True)
            return

        data[match]["psn"] = str(self.psn) or data[match]["psn"]
        data[match]["mail"] = str(self.mail) or "—"
        data[match]["password"] = str(self.password) or "—"
        data[match]["oge"] = str(self.oge) or "—"
        data[match]["dob"] = str(self.dob) or "—"
        save_data(data)

        embed = build_embed("✅ تم تعديل الحساب", data[match], match, 0xf39c12)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── /add ─────────────────────────────────────────────────
@bot.tree.command(name="add", description="➕ إضافة حساب جديد")
@app_commands.describe(name="اسم الحساب")
async def add_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return
    await interaction.response.send_modal(AddModal(name=name))

# ─── /edit ────────────────────────────────────────────────
@bot.tree.command(name="edit", description="✏️ تعديل بيانات حساب")
@app_commands.describe(name="اسم الحساب")
async def edit_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return

    data = load_data()
    match = find_account(data, name)
    if not match:
        await interaction.response.send_message(f"❌ ما لقيت حساب باسم **{name}**.", ephemeral=True)
        return

    await interaction.response.send_modal(EditModal(name=match, acc=data[match]))

# ─── /view ────────────────────────────────────────────────
@bot.tree.command(name="view", description="👁️ عرض بيانات حساب")
@app_commands.describe(name="اسم الحساب")
async def view_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return

    data = load_data()
    match = find_account(data, name)
    if not match:
        await interaction.response.send_message(f"❌ ما لقيت حساب باسم **{name}**.", ephemeral=True)
        return

    embed = build_embed(f"📋 {match}", data[match], match, 0x3498db)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── /info ────────────────────────────────────────────────
@bot.tree.command(name="info", description="📌 عرض قائمة منظمة لحساب")
@app_commands.describe(name="اسم الحساب")
async def info_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return

    data = load_data()
    match = find_account(data, name)
    if not match:
        await interaction.response.send_message(f"❌ ما لقيت حساب باسم **{name}**.", ephemeral=True)
        return

    acc = data[match]
    lines = [
        "```",
        f"  🖤  {match.upper()}",
        "─" * 32,
        f"  🎮 PSN  : {acc['psn']}",
        f"  📧 Mail : {acc['mail']}",
        f"  🔑 Pass : {acc['password']}",
        f"  🔰 OGE  : {acc['oge']}",
        f"  📅 DOB  : {acc['dob']}",
        "─" * 32,
        f"  🕒 أُضيف : {acc.get('added_at', '—')}",
        "```"
    ]
    await interaction.response.send_message("\n".join(lines), ephemeral=True)

# ─── /list ────────────────────────────────────────────────
@bot.tree.command(name="list", description="📃 عرض جميع الحسابات")
async def list_accounts(interaction: discord.Interaction):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return

    data = load_data()
    if not data:
        await interaction.response.send_message("📭 ما فيه حسابات مضافة بعد.", ephemeral=True)
        return

    embed = discord.Embed(title="📂 قائمة الحسابات", color=0x9b59b6)
    for i, (name, acc) in enumerate(data.items(), 1):
        embed.add_field(
            name=f"{i}. {name}",
            value=f"🎮 `{acc['psn']}` | 📧 `{acc['mail']}` | 📅 `{acc['dob']}`",
            inline=False
        )
    embed.set_footer(text=f"المجموع: {len(data)} حساب")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── /delete ──────────────────────────────────────────────
@bot.tree.command(name="delete", description="🗑️ حذف حساب")
@app_commands.describe(name="اسم الحساب")
async def delete_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return

    data = load_data()
    match = find_account(data, name)
    if not match:
        await interaction.response.send_message(f"❌ ما لقيت حساب باسم **{name}**.", ephemeral=True)
        return

    del data[match]
    save_data(data)
    await interaction.response.send_message(f"🗑️ تم حذف حساب **{match}** بنجاح.")

# ─── Run ──────────────────────────────────────────────────
bot.run(TOKEN)
