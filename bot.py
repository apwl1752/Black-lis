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

def v(val):
    return val if val and val != "—" else "—"

def build_embed(title, acc, name, color):
    embed = discord.Embed(title=title, color=color)

    # ── الحساب + PSN
    embed.add_field(name="👤  الحساب", value=f"```{name}```", inline=True)
    embed.add_field(name="🎮  PSN",    value=f"```{v(acc.get('psn', '—'))}```", inline=True)
    embed.add_field(name="\u200b",     value="\u200b", inline=True)

    # ── Mail + Pass
    embed.add_field(name="📧  Mail", value=f"```{v(acc.get('mail', '—'))}```", inline=True)
    embed.add_field(name="🔑  Pass", value=f"||`{v(acc.get('password', '—'))}`||", inline=True)
    embed.add_field(name="\u200b",   value="\u200b", inline=True)

    # ── OGE + DOB
    embed.add_field(name="🔰  OGE", value=f"```{v(acc.get('oge', '—'))}```", inline=True)
    embed.add_field(name="📅  DOB", value=f"```{v(acc.get('dob', '—'))}```", inline=True)
    embed.add_field(name="\u200b",  value="\u200b", inline=True)

    # ── CC + TID
    embed.add_field(name="💳  CC",  value=f"```{v(acc.get('cc', '—'))}```", inline=True)
    embed.add_field(name="🔖  TID", value=f"```{v(acc.get('tid', '—'))}```", inline=True)
    embed.add_field(name="\u200b",  value="\u200b", inline=True)

    # ── CARD + Region
    embed.add_field(name="🌍  Region", value=f"```{v(acc.get('region', '—'))}```", inline=True)
    embed.add_field(name="\u200b",     value="\u200b", inline=True)

    embed.set_footer(text=f"🕒  أُضيف: {acc.get('added_at', '—')}  •  🖤 Black")
    return embed

# ─── Events ───────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} شغّال!")

# ─── Modal 2: CC / TID / CARD / Region ────────────────────
class AddModal2(discord.ui.Modal, title="🖤 معلومات إضافية (اختياري)"):
    cc     = discord.ui.TextInput(label="CC",     placeholder="رقم البطاقة",   required=False)
    tid    = discord.ui.TextInput(label="TID",    placeholder="Transaction ID", required=False)
    region = discord.ui.TextInput(label="Region", placeholder="مثال: SA / US",  required=False)

    def __init__(self, name: str, partial_acc: dict):
        super().__init__()
        self.account_name = name
        self.partial_acc  = partial_acc

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()

        acc = self.partial_acc
        acc["cc"]     = str(self.cc)     or "—"
        acc["tid"]    = str(self.tid)    or "—"
        acc["region"] = str(self.region) or "—"
        acc["added_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        data[self.account_name] = acc
        save_data(data)

        embed = build_embed("✅ تم إضافة الحساب", acc, self.account_name, 0x2ecc71)
        await interaction.response.send_message(embed=embed)

# ─── Modal 1: PSN / Mail / Pass / OGE / DOB ───────────────
class AddModal1(discord.ui.Modal, title="🖤 إضافة حساب جديد  (1/2)"):
    psn      = discord.ui.TextInput(label="PSN",  placeholder="أدخل PSN ID",   required=True)
    mail     = discord.ui.TextInput(label="Mail", placeholder="أدخل الإيميل",  required=False)
    password = discord.ui.TextInput(label="Pass", placeholder="أدخل الباسورد", required=False)
    oge      = discord.ui.TextInput(label="OGE",  placeholder="أدخل OGE",      required=False)
    dob      = discord.ui.TextInput(label="DOB",  placeholder="مثال: 2000-11-11", required=False)

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

        partial = {
            "psn":      str(self.psn),
            "mail":     str(self.mail)     or "—",
            "password": str(self.password) or "—",
            "oge":      str(self.oge)      or "—",
            "dob":      str(self.dob)      or "—",
        }
        await interaction.response.send_modal(AddModal2(name=self.account_name, partial_acc=partial))

# ─── Edit Modal 1 ─────────────────────────────────────────
class EditModal1(discord.ui.Modal, title="✏️ تعديل الحساب  (1/2)"):
    psn      = discord.ui.TextInput(label="PSN",  required=False)
    mail     = discord.ui.TextInput(label="Mail", required=False)
    password = discord.ui.TextInput(label="Pass", required=False)
    oge      = discord.ui.TextInput(label="OGE",  required=False)
    dob      = discord.ui.TextInput(label="DOB",  required=False)

    def __init__(self, name: str, acc: dict):
        super().__init__()
        self.account_name = name
        self.old_acc      = acc
        self.psn.default      = acc.get("psn", "")
        self.mail.default     = acc.get("mail", "") if acc.get("mail") != "—" else ""
        self.password.default = acc.get("password", "") if acc.get("password") != "—" else ""
        self.oge.default      = acc.get("oge", "") if acc.get("oge") != "—" else ""
        self.dob.default      = acc.get("dob", "") if acc.get("dob") != "—" else ""

    async def on_submit(self, interaction: discord.Interaction):
        updated = dict(self.old_acc)
        updated["psn"]      = str(self.psn)      or updated["psn"]
        updated["mail"]     = str(self.mail)     or "—"
        updated["password"] = str(self.password) or "—"
        updated["oge"]      = str(self.oge)      or "—"
        updated["dob"]      = str(self.dob)      or "—"
        await interaction.response.send_modal(EditModal2(name=self.account_name, updated_acc=updated))

# ─── Edit Modal 2 ─────────────────────────────────────────
class EditModal2(discord.ui.Modal, title="✏️ تعديل الحساب  (2/2)"):
    cc     = discord.ui.TextInput(label="CC",     required=False)
    tid    = discord.ui.TextInput(label="TID",    required=False)
    region = discord.ui.TextInput(label="Region", required=False)

    def __init__(self, name: str, updated_acc: dict):
        super().__init__()
        self.account_name = name
        self.updated_acc  = updated_acc
        self.cc.default     = updated_acc.get("cc", "")     if updated_acc.get("cc")     != "—" else ""
        self.tid.default    = updated_acc.get("tid", "")    if updated_acc.get("tid")    != "—" else ""
        self.card.default   = updated_acc.get("card", "")   if updated_acc.get("card")   != "—" else ""
        self.region.default = updated_acc.get("region", "") if updated_acc.get("region") != "—" else ""

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        match = find_account(data, self.account_name)
        if not match:
            await interaction.response.send_message("❌ الحساب ما موجود.", ephemeral=True)
            return

        acc = self.updated_acc
        acc["cc"]     = str(self.cc)     or "—"
        acc["tid"]    = str(self.tid)    or "—"
        acc["region"] = str(self.region) or "—"
        data[match] = acc
        save_data(data)

        embed = build_embed("✅ تم تعديل الحساب", acc, match, 0xf39c12)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── /add ─────────────────────────────────────────────────
@bot.tree.command(name="add", description="➕ إضافة حساب جديد")
@app_commands.describe(name="اسم الحساب")
async def add_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return
    await interaction.response.send_modal(AddModal1(name=name))

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
    await interaction.response.send_modal(EditModal1(name=match, acc=data[match]))

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
        "─" * 34,
        f"  🎮 PSN    : {v(acc.get('psn','—'))}",
        f"  📧 Mail   : {v(acc.get('mail','—'))}",
        f"  🔑 Pass   : {v(acc.get('password','—'))}",
        f"  🔰 OGE    : {v(acc.get('oge','—'))}",
        f"  📅 DOB    : {v(acc.get('dob','—'))}",
        "─" * 34,
        f"  💳 CC     : {v(acc.get('cc','—'))}",
        f"  🔖 TID    : {v(acc.get('tid','—'))}",
        f"  🌍 Region : {v(acc.get('region','—'))}",
        "─" * 34,
        f"  🕒 أُضيف  : {acc.get('added_at','—')}",
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
            value=f"🎮 `{acc.get('psn','—')}` | 🌍 `{acc.get('region','—')}` | 📅 `{acc.get('dob','—')}`",
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
