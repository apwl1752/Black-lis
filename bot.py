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

    embed.add_field(name="👤  الحساب", value=f"```{name}```", inline=True)
    embed.add_field(name="🎮  PSN",    value=f"```{v(acc.get('psn', '—'))}```", inline=True)
    embed.add_field(name="\u200b",     value="\u200b", inline=True)

    embed.add_field(name="📧  Mail", value=f"```{v(acc.get('mail', '—'))}```", inline=True)
    embed.add_field(name="🔑  Pass", value=f"||`{v(acc.get('password', '—'))}`||", inline=True)
    embed.add_field(name="\u200b",   value="\u200b", inline=True)

    embed.add_field(name="🔰  OGE", value=f"```{v(acc.get('oge', '—'))}```", inline=True)
    embed.add_field(name="📅  DOB", value=f"```{v(acc.get('dob', '—'))}```", inline=True)
    embed.add_field(name="\u200b",  value="\u200b", inline=True)

    embed.add_field(name="💳  CC",  value=f"```{v(acc.get('cc', '—'))}```", inline=True)
    embed.add_field(name="🔖  TID", value=f"```{v(acc.get('tid', '—'))}```", inline=True)
    embed.add_field(name="\u200b",  value="\u200b", inline=True)

    embed.add_field(name="🃏  CARD",   value=f"```{v(acc.get('card', '—'))}```", inline=True)
    embed.add_field(name="🌍  Region", value=f"```{v(acc.get('region', '—'))}```", inline=True)
    embed.add_field(name="\u200b",     value="\u200b", inline=True)

    embed.set_footer(text=f"🕒  أُضيف: {acc.get('added_at', '—')}  •  🖤 Black")
    return embed

# ─── Events ───────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} شغّال!")


# ══════════════════════════════════════════════════════════
#  ADD FLOW  (Modal1 → رسالة + Button → Modal2)
# ══════════════════════════════════════════════════════════

class AddModal2(discord.ui.Modal, title="🖤 معلومات إضافية (اختياري)"):
    cc     = discord.ui.TextInput(label="CC",     placeholder="رقم البطاقة",   required=False)
    tid    = discord.ui.TextInput(label="TID",    placeholder="Transaction ID", required=False)
    card   = discord.ui.TextInput(label="CARD",   placeholder="نوع الكارد",     required=False)
    region = discord.ui.TextInput(label="Region", placeholder="مثال: SA / US",  required=False)

    def __init__(self, name: str, partial_acc: dict):
        super().__init__()
        self.account_name = name
        self.partial_acc  = partial_acc

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()

        acc = self.partial_acc
        acc["cc"]       = str(self.cc)     or "—"
        acc["tid"]      = str(self.tid)    or "—"
        acc["card"]     = str(self.card)   or "—"
        acc["region"]   = str(self.region) or "—"
        acc["added_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        data[self.account_name] = acc
        save_data(data)

        embed = build_embed("✅ تم إضافة الحساب", acc, self.account_name, 0x2ecc71)
        # ✅ هذه الـ interaction جاية من Button → يشتغل send_message عادي
        await interaction.response.send_message(embed=embed)


# ─── View يحمل زر "أكمل البيانات" يفتح Modal2 ────────────
class AddStep2View(discord.ui.View):
    def __init__(self, name: str, partial_acc: dict):
        super().__init__(timeout=120)
        self.account_name = name
        self.partial_acc  = partial_acc

    @discord.ui.button(label="➕ أكمل البيانات (CC / TID / CARD / Region)", style=discord.ButtonStyle.primary)
    async def open_modal2(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ✅ Button → Modal يشتغل بدون مشكلة
        await interaction.response.send_modal(
            AddModal2(name=self.account_name, partial_acc=self.partial_acc)
        )
        self.stop()

    @discord.ui.button(label="⏭️ تخطى", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        acc = self.partial_acc
        acc["cc"] = acc["tid"] = acc["card"] = acc["region"] = "—"
        acc["added_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        data[self.account_name] = acc
        save_data(data)

        embed = build_embed("✅ تم إضافة الحساب", acc, self.account_name, 0x2ecc71)
        await interaction.response.send_message(embed=embed)
        self.stop()


class AddModal1(discord.ui.Modal, title="🖤 إضافة حساب جديد  (1/2)"):
    psn      = discord.ui.TextInput(label="PSN",  placeholder="أدخل PSN ID",      required=True)
    mail     = discord.ui.TextInput(label="Mail", placeholder="أدخل الإيميل",     required=False)
    password = discord.ui.TextInput(label="Pass", placeholder="أدخل الباسورد",    required=False)
    oge      = discord.ui.TextInput(label="OGE",  placeholder="أدخل OGE",         required=False)
    dob      = discord.ui.TextInput(label="DOB",  placeholder="مثال: 2000-11-11",  required=False)

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

        # ✅ بدل send_modal ثاني → نرسل رسالة فيها View مع Button
        view = AddStep2View(name=self.account_name, partial_acc=partial)
        await interaction.response.send_message(
            "✅ **الخطوة 1 تمت!** الآن أضف بيانات البطاقة أو تخطى:",
            view=view,
            ephemeral=True
        )


# ══════════════════════════════════════════════════════════
#  EDIT FLOW  (Modal1 → رسالة + Button → Modal2)
# ══════════════════════════════════════════════════════════

class EditModal2(discord.ui.Modal, title="✏️ تعديل الحساب  (2/2)"):
    cc     = discord.ui.TextInput(label="CC",     required=False)
    tid    = discord.ui.TextInput(label="TID",    required=False)
    card   = discord.ui.TextInput(label="CARD",   required=False)
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
        acc["card"]   = str(self.card)   or "—"
        acc["region"] = str(self.region) or "—"
        data[match] = acc
        save_data(data)

        embed = build_embed("✅ تم تعديل الحساب", acc, match, 0xf39c12)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─── View يحمل زر "أكمل التعديل" يفتح EditModal2 ─────────
class EditStep2View(discord.ui.View):
    def __init__(self, name: str, updated_acc: dict):
        super().__init__(timeout=120)
        self.account_name = name
        self.updated_acc  = updated_acc

    @discord.ui.button(label="✏️ تعديل البيانات (CC / TID / CARD / Region)", style=discord.ButtonStyle.primary)
    async def open_modal2(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ✅ Button → Modal يشتغل
        await interaction.response.send_modal(
            EditModal2(name=self.account_name, updated_acc=self.updated_acc)
        )
        self.stop()

    @discord.ui.button(label="💾 حفظ بدون تعديل (2/2)", style=discord.ButtonStyle.secondary)
    async def save_as_is(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        match = find_account(data, self.account_name)
        if match:
            data[match] = self.updated_acc
            save_data(data)
        embed = build_embed("✅ تم تعديل الحساب", self.updated_acc, self.account_name, 0xf39c12)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()


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
        self.mail.default     = acc.get("mail", "")     if acc.get("mail")     != "—" else ""
        self.password.default = acc.get("password", "") if acc.get("password") != "—" else ""
        self.oge.default      = acc.get("oge", "")      if acc.get("oge")      != "—" else ""
        self.dob.default      = acc.get("dob", "")      if acc.get("dob")      != "—" else ""

    async def on_submit(self, interaction: discord.Interaction):
        updated = dict(self.old_acc)
        updated["psn"]      = str(self.psn)      or updated["psn"]
        updated["mail"]     = str(self.mail)     or "—"
        updated["password"] = str(self.password) or "—"
        updated["oge"]      = str(self.oge)      or "—"
        updated["dob"]      = str(self.dob)      or "—"

        # ✅ بدل send_modal ثاني → رسالة فيها View مع Button
        view = EditStep2View(name=self.account_name, updated_acc=updated)
        await interaction.response.send_message(
            "✅ **الجزء الأول تم!** الآن عدّل بيانات البطاقة أو احفظ مباشرة:",
            view=view,
            ephemeral=True
        )


# ══════════════════════════════════════════════════════════
#  SLASH COMMANDS
# ══════════════════════════════════════════════════════════

@bot.tree.command(name="add", description="➕ إضافة حساب جديد")
@app_commands.describe(name="اسم الحساب")
async def add_account(interaction: discord.Interaction, name: str):
    if not channel_check(interaction):
        await interaction.response.send_message("❌ هذا الأمر يشتغل في الروم المحددة فقط.", ephemeral=True)
        return
    await interaction.response.send_modal(AddModal1(name=name))


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
        f"  🃏 CARD   : {v(acc.get('card','—'))}",
        f"  🌍 Region : {v(acc.get('region','—'))}",
        "─" * 34,
        f"  🕒 أُضيف  : {acc.get('added_at','—')}",
        "```"
    ]
    await interaction.response.send_message("\n".join(lines), ephemeral=True)



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
