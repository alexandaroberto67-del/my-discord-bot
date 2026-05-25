import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

TOKEN = "MTUwNzE2NTI5ODUxODY1NDk4Nw.GNmccg.-1rb_KY5FeXUJwzsU0LHrobRS51pF188M9QEXc"
GUILD_ID = 1488378242846036070
GUILD_ID_2 = 1508606322470420480
ALL_GUILDS = [discord.Object(id=1488378242846036070), discord.Object(id=1508606322470420480)]
UNCLAIMED_CATEGORY_ID = 1507173928705986692
CLAIMED_CATEGORY_ID = 1507173970531586109
GUIDELINES_CHANNEL_ID = 1488378243697606713
BANNER_PATH = "banner.png"
GUIDELINES_BANNER_PATH = "guidelines_banner.png"
DESIGN_TICKETS_FILE = "tickets.json"
SUPPORT_TICKETS_FILE = "support_tickets.json"

MANAGEMENT_ROLE_IDS = [1497417569215189103, 1497066480372547625, 1497416896600080445, 1497415634915561603]
DESIGN_STAFF_ROLE_IDS = MANAGEMENT_ROLE_IDS + [1497420088456777859, 1497420575583502397, 1497420527789412462, 1497420622840725616, 1497420719015989439, 1497420767959187538, 1497420827165982751, 1497420666729922620, 1507166479622340848]
SUPPORT_PING_ROLE_IDS = [1497066388760822000, 1497415353175773244, 1488389422641709310, 1497417569215189103, 1507161747885133964]
SUPPORT_STAFF_ROLE_IDS = SUPPORT_PING_ROLE_IDS

SERVICES = [
    {"label": "Alt Servicing",    "emoji": "🔄", "prefix": "alt",     "role_id": 1507166479622340848},
    {"label": "ELS Designer",     "emoji": "🚨", "prefix": "els",     "role_id": 1497420666729922620},
    {"label": "Banner Designer",  "emoji": "🖼️", "prefix": "banner",  "role_id": 1497420827165982751},
    {"label": "Logo Designer",    "emoji": "✏️", "prefix": "logo",    "role_id": 1497420767959187538},
    {"label": "Graphic Designer", "emoji": "🎨", "prefix": "graphic", "role_id": 1497420719015989439},
    {"label": "Uniform Designer", "emoji": "👕", "prefix": "uniform", "role_id": 1497420622840725616},
    {"label": "Livery Designer",  "emoji": "🚗", "prefix": "livery",  "role_id": 1497420527789412462},
    {"label": "Discord Designer", "emoji": "💬", "prefix": "discord", "role_id": 1497420575583502397},
]

TOPICS = [
    {"label": "General", "emoji": "❓", "description": "Questions & Concerns", "prefix": "general"},
    {"label": "Support", "emoji": "🎫", "description": "Reporting Members & Designers", "prefix": "support"},
]

GUIDELINES = [
    ("1. Orders", "Please do not ping a designer as they do have many other orders and more."),
    ("2. Misuse", "Use all channels appropriately and do not misuse any. Use tickets for its intended purposes."),
    ("3. Advertising", "Advertising is not allowed. This can include DMs. We only advertise if you are an affiliate."),
    ("4. English", "Our servers main language is English. Please do not speak any other languages within the server to improve collaboration."),
    ("5. ALTS", "ALT accounts are strictly not allowed. Do not try to bypass a punishment by using a ALT."),
    ("6. Drama", "Do not create or bring up any type of drama into the server. Let's have a chill environment."),
    ("7. Profanity", "Do not bypass our profanity filter and refrain from using profanity in any of our channels."),
    ("8. Knowledge", "Treat others how you are wanting to be treated. Do not troll & allow for a clean/chill environment."),
    ("9. Account", "Your username on Discord has to be your RBLX username. Alts are not allowed."),
    ("10. NSFW", "Nudity, graphic, or hateful types of messages & images is highly prohibited."),
    ("11. VC Usage", "Use VCs how they are suppose to be used. Use PTS in RP VCs & use RTO for RTO purposes."),
    ("12. Pinging", "Pinging a high rank or member without a valid reason is not allowed. You may only ping the HR team if important."),
]

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_roles(guild, ids):
    return [r for r in [guild.get_role(i) for i in ids] if r]

def is_design_staff(member):
    return any(r.id in DESIGN_STAFF_ROLE_IDS for r in member.roles)

def is_support_staff(member):
    return any(r.id in SUPPORT_STAFF_ROLE_IDS for r in member.roles)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
design_tickets = {}
support_tickets = {}


# ── Guidelines ────────────────────────────────────────────────────────────────

async def post_guidelines(guild):
    try:
        channel = await bot.fetch_channel(GUIDELINES_CHANNEL_ID)
    except Exception as e:
        print(f"❌ Could not fetch guidelines channel: {e}")
        return
    if not channel:
        print(f"❌ Guidelines channel not found!")
        return

    # Clear channel
    await channel.purge(limit=100)

    # Build rules text
    rules_text = "\n\n".join(f"`{title}`\n{desc}" for title, desc in GUIDELINES)

    embed = discord.Embed(
        title="Discord Regulations",
        description=rules_text,
        color=0x5865F2,
    )

    if os.path.exists(GUIDELINES_BANNER_PATH):
        file = discord.File(GUIDELINES_BANNER_PATH, filename="guidelines_banner.png")
        embed.set_image(url="attachment://guidelines_banner.png")
        await channel.send(file=file, embed=embed)
    else:
        await channel.send(embed=embed)

    print(f"✅ Guidelines posted in #{channel.name}")


# ── Design ticket logic ───────────────────────────────────────────────────────

async def open_design_ticket(interaction, service):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    for t in design_tickets.values():
        if t["author_id"] == interaction.user.id and t["prefix"] == service["prefix"] and t["status"] == "open":
            ch = guild.get_channel(t["channel_id"])
            if ch:
                await interaction.followup.send(f"You already have an open {service['label']} ticket: {ch.mention}", ephemeral=True)
                return
    staff_roles = get_roles(guild, DESIGN_STAFF_ROLE_IDS)
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    for role in staff_roles:
        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    unclaimed = guild.get_channel(UNCLAIMED_CATEGORY_ID)
    number = len(design_tickets) + 1
    channel = await guild.create_text_channel(f"{service['prefix']}-{number:04d}", overwrites=overwrites, category=unclaimed, topic=f"Ticket #{number} | {service['label']} | {interaction.user}")
    design_tickets[str(channel.id)] = {"number": number, "label": service["label"], "prefix": service["prefix"], "author_id": interaction.user.id, "author_name": str(interaction.user), "channel_id": channel.id, "assigned_to": None, "opened_at": datetime.utcnow().isoformat(), "status": "open"}
    save_json(DESIGN_TICKETS_FILE, design_tickets)
    pings = " ".join(r.mention for r in get_roles(guild, MANAGEMENT_ROLE_IDS + [service["role_id"]]))
    embed = discord.Embed(title=f"{service['emoji']} {service['label']} — Ticket #{number}", description=f"Hey {interaction.user.mention}! Thanks for your interest in our **{service['label']}** service.\n\nPlease describe what you're looking for and a staff member will be with you shortly!", color=0x5865F2, timestamp=datetime.utcnow())
    embed.set_footer(text=f"Opened by {interaction.user}")
    await channel.send(content=pings, embed=embed, view=DesignControlView())
    await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

async def open_support_ticket(interaction, topic):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    for t in support_tickets.values():
        if t["author_id"] == interaction.user.id and t["prefix"] == topic["prefix"] and t["status"] == "open":
            ch = guild.get_channel(t["channel_id"])
            if ch:
                await interaction.followup.send(f"You already have an open {topic['label']} ticket: {ch.mention}", ephemeral=True)
                return
    ping_roles = get_roles(guild, SUPPORT_PING_ROLE_IDS)
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    for role in ping_roles:
        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    unclaimed = guild.get_channel(UNCLAIMED_CATEGORY_ID)
    number = len(support_tickets) + 1
    channel = await guild.create_text_channel(f"{topic['prefix']}-{number:04d}", overwrites=overwrites, category=unclaimed, topic=f"Ticket #{number} | {topic['label']} | {interaction.user}")
    support_tickets[str(channel.id)] = {"number": number, "label": topic["label"], "prefix": topic["prefix"], "author_id": interaction.user.id, "author_name": str(interaction.user), "channel_id": channel.id, "assigned_to": None, "opened_at": datetime.utcnow().isoformat(), "status": "open"}
    save_json(SUPPORT_TICKETS_FILE, support_tickets)
    pings = " ".join(r.mention for r in ping_roles)
    embed = discord.Embed(title=f"{topic['emoji']} {topic['label']} — Ticket #{number}", description=f"Hey {interaction.user.mention}! Thanks for reaching out.\n\nPlease describe your issue and a staff member will be with you shortly!", color=0x5865F2, timestamp=datetime.utcnow())
    embed.set_footer(text=f"Opened by {interaction.user}")
    await channel.send(content=pings, embed=embed, view=SupportControlView())
    await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)


# ── Views ─────────────────────────────────────────────────────────────────────

class ServiceButton(discord.ui.Button):
    def __init__(self, service, row):
        super().__init__(label=service["label"], emoji=service["emoji"], style=discord.ButtonStyle.primary, custom_id=f"design_{service['prefix']}", row=row)
        self.service = service
    async def callback(self, interaction):
        await open_design_ticket(interaction, self.service)

class DesignPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for i, s in enumerate(SERVICES):
            self.add_item(ServiceButton(s, row=i // 4))

class DesignControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assign to me", style=discord.ButtonStyle.primary, emoji="🙋", custom_id="design_assign")
    async def assign(self, interaction, button):
        if not is_design_staff(interaction.user):
            await interaction.response.send_message("Only staff can assign tickets.", ephemeral=True)
            return
        ticket = design_tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return
        ticket["assigned_to"] = interaction.user.id
        save_json(DESIGN_TICKETS_FILE, design_tickets)
        claimed = interaction.guild.get_channel(CLAIMED_CATEGORY_ID)
        if claimed:
            await interaction.channel.edit(category=claimed)
        await interaction.response.send_message(embed=discord.Embed(description=f"🙋 {interaction.user.mention} assigned. Moved to Claimed.", color=0x57F287))

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="design_close")
    async def close(self, interaction, button):
        ticket = design_tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return
        if not (is_design_staff(interaction.user) or ticket["author_id"] == interaction.user.id):
            await interaction.response.send_message("You can't close this ticket.", ephemeral=True)
            return
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.utcnow().isoformat()
        ticket["closed_by"] = str(interaction.user)
        save_json(DESIGN_TICKETS_FILE, design_tickets)
        await interaction.response.send_message(embed=discord.Embed(title="Ticket Closed", description=f"🔒 Closed by {interaction.user.mention}. Deleting in 5 seconds.", color=0xED4245))
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TopicSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=t["label"], emoji=t["emoji"], description=t["description"], value=t["prefix"]) for t in TOPICS]
        super().__init__(placeholder="Select a topic...", min_values=1, max_values=1, options=options, custom_id="support_topic_select")
    async def callback(self, interaction):
        selected = next(t for t in TOPICS if t["prefix"] == self.values[0])
        await open_support_ticket(interaction, selected)

class SupportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TopicSelect())

class SupportControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assign to me", style=discord.ButtonStyle.primary, emoji="🙋", custom_id="support_assign")
    async def assign(self, interaction, button):
        if not is_support_staff(interaction.user):
            await interaction.response.send_message("Only staff can assign tickets.", ephemeral=True)
            return
        ticket = support_tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return
        ticket["assigned_to"] = interaction.user.id
        save_json(SUPPORT_TICKETS_FILE, support_tickets)
        claimed = interaction.guild.get_channel(CLAIMED_CATEGORY_ID)
        if claimed:
            await interaction.channel.edit(category=claimed)
        await interaction.response.send_message(embed=discord.Embed(description=f"🙋 {interaction.user.mention} assigned. Moved to Claimed.", color=0x57F287))

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="support_close")
    async def close(self, interaction, button):
        ticket = support_tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return
        if not (is_support_staff(interaction.user) or ticket["author_id"] == interaction.user.id):
            await interaction.response.send_message("You can't close this ticket.", ephemeral=True)
            return
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.utcnow().isoformat()
        ticket["closed_by"] = str(interaction.user)
        save_json(SUPPORT_TICKETS_FILE, support_tickets)
        await interaction.response.send_message(embed=discord.Embed(title="Ticket Closed", description=f"🔒 Closed by {interaction.user.mention}. Deleting in 5 seconds.", color=0xED4245))
        await asyncio.sleep(5)
        await interaction.channel.delete()


# ── Slash Commands ────────────────────────────────────────────────────────────


# ── Prices ────────────────────────────────────────────────────────────────────

SERVICE_PRICES = {
    "alt": {
        "label": "🔄 Alt Servicing",
        "prices": [
            ("Basic Alt Setup", "50 R$"),
            ("Full Alt Package", "120 R$"),
            ("Premium Management", "250 R$"),
        ]
    },
    "els": {
        "label": "🚨 ELS Designer",
        "prices": [
            ("Basic ELS", "150 R$"),
            ("Advanced ELS", "350 R$"),
            ("Custom Premium ELS", "600 R$"),
        ]
    },
    "banner": {
        "label": "🖼️ Banner Designer",
        "prices": [
            ("Small Banner", "75 R$"),
            ("Animated Banner", "200 R$"),
            ("Premium Server Banner", "350 R$"),
        ]
    },
    "logo": {
        "label": "✏️ Logo Designer",
        "prices": [
            ("Simple Logo", "100 R$"),
            ("Detailed Logo", "250 R$"),
            ("Professional Logo Pack", "500 R$"),
        ]
    },
    "graphic": {
        "label": "🎨 Graphic Designer",
        "prices": [
            ("Basic Graphic", "80 R$"),
            ("Custom Graphic", "180 R$"),
            ("Full Graphic Package", "400 R$"),
        ]
    },
    "uniform": {
        "label": "👕 Uniform Designer",
        "prices": [
            ("Simple Uniform", "120 R$"),
            ("Department Uniform Set", "300 R$"),
            ("Premium Custom Uniform", "550 R$"),
        ]
    },
    "livery": {
        "label": "🚗 Livery Designer",
        "prices": [
            ("Basic Livery", "200 R$"),
            ("Detailed Livery", "450 R$"),
            ("Full Fleet Package", "900 R$"),
        ]
    },
    "discord": {
        "label": "💬 Discord Designer",
        "prices": [
            ("Basic Server Design", "150 R$"),
            ("Full Server Setup", "400 R$"),
            ("Premium Custom Server", "750 R$"),
        ]
    },
}


class PricesSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=s["label"], emoji=s["emoji"], value=s["prefix"])
            for s in SERVICES
        ]
        super().__init__(placeholder="💰 View prices for a service...", min_values=1, max_values=1, options=options, custom_id="prices_select")

    async def callback(self, interaction: discord.Interaction):
        prefix = self.values[0]
        data = SERVICE_PRICES.get(prefix)
        if not data:
            await interaction.response.send_message("Prices not found.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{data['label']} — Pricing", color=0x5865F2)
        for name, price in data["prices"]:
            embed.add_field(name=name, value=price, inline=True)
        embed.set_footer(text="Prices are in Robux (R$)")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PricesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PricesSelect())


@bot.tree.command(name="panel", description="Post the design services panel (staff only)")
@app_commands.guilds(*ALL_GUILDS)
async def panel(interaction):
    if not is_design_staff(interaction.user):
        await interaction.response.send_message("Only staff can post the panel.", ephemeral=True)
        return
    embed = discord.Embed(title="🎨 Vine Customs — Design Services", description="Welcome! Select the service you'd like to purchase below.\nA private ticket will be created for you.\n\n" + "\n".join(f"{s['emoji']} **{s['label']}**" for s in SERVICES), color=0x5865F2)
    await interaction.channel.send(embed=embed, view=DesignPanelView())
    prices_embed = discord.Embed(title="💰 Vine Customs — Pricing", description="Select a service below to view its pricing.", color=0x5865F2)
    await interaction.channel.send(embed=prices_embed, view=PricesView())
    await interaction.response.send_message("Panel posted.", ephemeral=True)

@bot.tree.command(name="supportpanel", description="Post the support panel (staff only)")
@app_commands.guilds(*ALL_GUILDS)
async def support_panel(interaction):
    if not is_support_staff(interaction.user):
        await interaction.response.send_message("Only staff can post the panel.", ephemeral=True)
        return
    embed = discord.Embed(description="Looking for assistance? You have came to the right place! Please choose the correct ticket below and someone will be with you shortly!\n\n❓ **• General**\n• Questions\n• Concerns\n\n🎫 **• Support**\n• Reporting Members\n• Reporting Designers\n\nIf you have anything other than that open a general ticket!", color=0x5865F2)
    if os.path.exists(BANNER_PATH):
        file = discord.File(BANNER_PATH, filename="banner.png")
        embed.set_image(url="attachment://banner.png")
        await interaction.channel.send(file=file, embed=embed, view=SupportPanelView())
    else:
        await interaction.channel.send(embed=embed, view=SupportPanelView())
    await interaction.response.send_message("Support panel posted.", ephemeral=True)

@bot.tree.command(name="postguidelines", description="Re-post the guidelines (staff only)")
@app_commands.guilds(*ALL_GUILDS)
async def postguidelines(interaction):
    if not is_design_staff(interaction.user) and not is_support_staff(interaction.user):
        await interaction.response.send_message("Only staff can post guidelines.", ephemeral=True)
        return
    await interaction.response.send_message("Posting guidelines...", ephemeral=True)
    await post_guidelines(interaction.guild)

@bot.tree.command(name="tickets", description="List open design tickets (staff only)")
@app_commands.guilds(*ALL_GUILDS)
async def list_design(interaction):
    if not is_design_staff(interaction.user):
        await interaction.response.send_message("Only staff can view tickets.", ephemeral=True)
        return
    open_t = [t for t in design_tickets.values() if t["status"] == "open"]
    if not open_t:
        await interaction.response.send_message("No open design tickets!", ephemeral=True)
        return
    lines = [f"**#{t['number']}** | {t['label']} | <@{t['author_id']}> | " + (f"<@{t['assigned_to']}>" if t['assigned_to'] else "Unassigned") for t in open_t]
    await interaction.response.send_message(embed=discord.Embed(title=f"Open Design Tickets ({len(open_t)})", description="\n".join(lines), color=0x5865F2), ephemeral=True)

@bot.tree.command(name="supporttickets", description="List open support tickets (staff only)")
@app_commands.guilds(*ALL_GUILDS)
async def list_support(interaction):
    if not is_support_staff(interaction.user):
        await interaction.response.send_message("Only staff can view tickets.", ephemeral=True)
        return
    open_t = [t for t in support_tickets.values() if t["status"] == "open"]
    if not open_t:
        await interaction.response.send_message("No open support tickets!", ephemeral=True)
        return
    lines = [f"**#{t['number']}** | {t['label']} | <@{t['author_id']}> | " + (f"<@{t['assigned_to']}>" if t['assigned_to'] else "Unassigned") for t in open_t]
    await interaction.response.send_message(embed=discord.Embed(title=f"Open Support Tickets ({len(open_t)})", description="\n".join(lines), color=0x5865F2), ephemeral=True)


# ── Events ────────────────────────────────────────────────────────────────────

@bot.tree.command(name="apppanel", description="Post the applications panel (admin only)")
@app_commands.guilds(*ALL_GUILDS)
async def app_panel(interaction: discord.Interaction):
    if not can_review(interaction.user):
        await interaction.response.send_message("❌ Only admins can post this panel.", ephemeral=True)
        return
    embed = discord.Embed(
        title="📋 Vine Customs — Designer Applications",
        description="Want to join our design team? Click the button for the role you're applying for below!\n\n" + "\n".join(f"{s['emoji']} **{s['label']}**" for s in SERVICES),
        color=0x5865F2,
    )
    await interaction.channel.send(embed=embed, view=AppPanelView())
    await interaction.response.send_message("✅ Application panel posted.", ephemeral=True)

async def sync_and_run():
    for g in ALL_GUILDS:
        bot.tree.copy_global_to(guild=g)
        await bot.tree.sync(guild=g)


@bot.event
async def on_ready():
    global design_tickets, support_tickets
    design_tickets = load_json(DESIGN_TICKETS_FILE)
    support_tickets = load_json(SUPPORT_TICKETS_FILE)
    bot.add_view(DesignPanelView())
    bot.add_view(DesignControlView())
    bot.add_view(SupportPanelView())
    bot.add_view(SupportControlView())
    bot.add_view(PricesView())
    load_apps()
    bot.add_view(AppPanelView())
    bot.add_view(ReviewView("placeholder"))
    for g in ALL_GUILDS:
        bot.tree.copy_global_to(guild=g)
        await bot.tree.sync(guild=g)
    print(f"✅ Logged in as {bot.user}")
    print(f"   {len(design_tickets)} design tickets, {len(support_tickets)} support tickets loaded.")
    guild = bot.get_guild(GUILD_ID)
    if guild:
        await post_guidelines(guild)


# ── Applications ──────────────────────────────────────────────────────────────

OWNER_ID = 1399078141401759754
ADMIN_ROLE_ID_APP = 1507161747885133964
APP_PANEL_CHANNEL_ID = 1507171064755650642
APP_RESULTS_CHANNEL_ID = 1507246734890242118
APPS_FILE = "applications.json"

APP_QUESTIONS = [
    "What design experience do you have, and what programs/apps do you use?",
    "Please share examples of your previous work or a portfolio link.",
    "How active can you be in the server each week?",
    "Why do you want to join our design team, and what makes your work stand out?",
]

applications = {}

def load_apps():
    global applications
    if os.path.exists(APPS_FILE):
        with open(APPS_FILE, "r") as f:
            applications = json.load(f)

def save_apps():
    with open(APPS_FILE, "w") as f:
        json.dump(applications, f, indent=2)

def can_review(member):
    return member.id == OWNER_ID or any(r.id == ADMIN_ROLE_ID_APP for r in member.roles)


class ApplicationModal(discord.ui.Modal):
    def __init__(self, service):
        super().__init__(title=f"{service['label']} Application")
        self.service = service
        self.q1 = discord.ui.TextInput(label="Experience & Programs", style=discord.TextStyle.paragraph, placeholder="What design experience do you have, and what programs/apps do you use?", max_length=500)
        self.q2 = discord.ui.TextInput(label="Portfolio / Previous Work", style=discord.TextStyle.paragraph, placeholder="Share examples of your work or a portfolio link.", max_length=500)
        self.q3 = discord.ui.TextInput(label="Availability", style=discord.TextStyle.short, placeholder="How active can you be in the server each week?", max_length=200)
        self.q4 = discord.ui.TextInput(label="Why Join & What Makes You Stand Out", style=discord.TextStyle.paragraph, placeholder="Why do you want to join and what makes your work stand out?", max_length=500)
        self.add_item(self.q1)
        self.add_item(self.q2)
        self.add_item(self.q3)
        self.add_item(self.q4)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        app_id = f"{interaction.user.id}_{self.service['prefix']}_{int(datetime.utcnow().timestamp())}"
        applications[app_id] = {
            "app_id": app_id, "service": self.service["label"], "prefix": self.service["prefix"],
            "author_id": interaction.user.id, "author_name": str(interaction.user),
            "submitted_at": datetime.utcnow().isoformat(), "status": "pending",
            "answers": {"experience": self.q1.value, "portfolio": self.q2.value, "availability": self.q3.value, "why_join": self.q4.value}
        }
        save_apps()
        try:
            results_channel = guild.get_channel(APP_RESULTS_CHANNEL_ID) or await bot.fetch_channel(APP_RESULTS_CHANNEL_ID)
        except:
            await interaction.followup.send("❌ Could not find the applications channel.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{self.service['emoji']} {self.service['label']} Application", color=0x5865F2, timestamp=datetime.utcnow())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Experience & Programs", value=self.q1.value, inline=False)
        embed.add_field(name="Portfolio / Previous Work", value=self.q2.value, inline=False)
        embed.add_field(name="Availability", value=self.q3.value, inline=False)
        embed.add_field(name="Why Join & What Makes You Stand Out", value=self.q4.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id} | App ID: {app_id}")
        await results_channel.send(embed=embed, view=ReviewView(app_id))
        await interaction.followup.send("✅ Your application has been submitted! We'll get back to you soon.", ephemeral=True)


class DenyReasonModal(discord.ui.Modal, title="Deny Reason"):
    reason = discord.ui.TextInput(label="Reason for denial", style=discord.TextStyle.paragraph, placeholder="Provide a reason for denying this application...", max_length=500)
    def __init__(self, message):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction: discord.Interaction):
        app_id = None
        if self.message.embeds:
            footer = self.message.embeds[0].footer.text
            if footer and "App ID:" in footer:
                app_id = footer.split("App ID:")[-1].strip()
        app = applications.get(app_id)
        if app:
            app["status"] = "denied"
            app["reviewed_by"] = str(interaction.user)
            app["deny_reason"] = self.reason.value
            save_apps()
            try:
                user = await bot.fetch_user(app["author_id"])
                await user.send(embed=discord.Embed(title="❌ Application Denied", description=f"Unfortunately your **{app['service']}** application at **Vine Customs** has been denied.\n\n**Reason:** {self.reason.value}", color=0xED4245))
            except:
                pass
        embed = self.message.embeds[0]
        embed.color = 0xED4245
        embed.add_field(name="Decision", value=f"❌ Denied by {interaction.user.mention}\n**Reason:** {self.reason.value}", inline=False)
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ Application denied.", ephemeral=True)


class ReviewView(discord.ui.View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅", custom_id="app_accept")
    async def accept(self, interaction, button):
        if not can_review(interaction.user):
            await interaction.response.send_message("❌ Only admins can review applications.", ephemeral=True)
            return
        app_id = None
        if interaction.message.embeds:
            footer = interaction.message.embeds[0].footer.text
            if footer and "App ID:" in footer:
                app_id = footer.split("App ID:")[-1].strip()
        app = applications.get(app_id)
        if app:
            app["status"] = "accepted"
            app["reviewed_by"] = str(interaction.user)
            save_apps()
            try:
                user = await bot.fetch_user(app["author_id"])
                await user.send(embed=discord.Embed(title="✅ Application Accepted!", description=f"Congratulations! Your **{app['service']}** application has been accepted at **Vine Customs**!\n\nWelcome to the team!", color=0x57F287))
            except:
                pass
        embed = interaction.message.embeds[0]
        embed.color = 0x57F287
        embed.add_field(name="Decision", value=f"✅ Accepted by {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Application accepted!", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌", custom_id="app_deny")
    async def deny(self, interaction, button):
        if not can_review(interaction.user):
            await interaction.response.send_message("❌ Only admins can review applications.", ephemeral=True)
            return
        await interaction.response.send_modal(DenyReasonModal(interaction.message))


class AppButton(discord.ui.Button):
    def __init__(self, service, row):
        super().__init__(label=service["label"], emoji=service["emoji"], style=discord.ButtonStyle.primary, custom_id=f"app_{service['prefix']}", row=row)
        self.service = service
    async def callback(self, interaction):
        await interaction.response.send_modal(ApplicationModal(self.service))

class AppPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for i, s in enumerate(SERVICES):
            self.add_item(AppButton(s, row=i // 4))


# 1. Imports should usually be at the VERY top of the file, 
# but if you put it here, it must be before you use 'os'
import os

# 2. Get the token first
TOKEN = os.getenv('TOKEN', '').strip()

# 3. Debug print (optional, but helpful for Railway)
if TOKEN:
    print(f"Token detected! Starts with: {TOKEN[:5]}...")
else:
    print("TOKEN NOT FOUND! Check your Railway Variables.")

# 4. Run the bot LAST
bot.run(TOKEN)
