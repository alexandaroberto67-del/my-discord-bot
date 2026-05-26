import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime

TOKEN = "MTUwODYzMDkyNDY1MTM5NzIyMQ.GM9l8J.-xEow2Wpsqbz1nxtXwb8yfEDA_9wiqwJtMTXYg"
GUILD_ID = 1508606322470420480

VERIFY_CHANNEL_ID     = 1508606322470420486
DISCORD_RULES_CHANNEL = 1508606323246501968
INGAME_RULES_CHANNEL  = 1508606323426852925
ABOUT_US_CHANNEL      = 1508606323426852927
SERVER_AD_CHANNEL     = 1508606323426852928
TICKETS_CHANNEL       = 1508606323607081116
APPS_CHANNEL          = 1508606323426852931
APP_RESULTS_CHANNEL   = 1508606323607081112
INFRACTIONS_CHANNEL   = 1508606325150711838
PROMOTIONS_CHANNEL    = 1508614619504185479
LOA_CHANNEL           = 1508606325150711841

UNVERIFIED_ROLE_ID = 1508606322470420488
VERIFIED_ROLE_ID   = 1508606322470420486
LOA_ROLE_ID        = 1508606322550112373

STAFF_ROLE_IDS = [
    1508606322558505187, 1508606322558505185, 1508606322558505184,
    1508606322558505183, 1508606322558505182, 1508606322550112375,
    1508606322550112374, 1508606322512494670, 1508606322512494669,
    1508606322512494668, 1508606322512494667, 1508606322512494665,
    1508606322512494664, 1508606322499915876,
]

SENIOR_STAFF_IDS = [
    1508606322558505187, 1508606322558505185, 1508606322558505184,
    1508606322558505183, 1508606322558505182, 1508606322550112375,
    1508606322550112374,
]

DATA_DIR = "grey_data"
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(name):
    path = f"{DATA_DIR}/{name}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_json(name, data):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(data, f, indent=2)

def is_staff(member):
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)

def is_senior(member):
    return any(r.id in SENIOR_STAFF_IDS for r in member.roles)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

applications = {}
loas = {}
infractions = {}
tickets = {}

GUILD_OBJ = discord.Object(id=GUILD_ID)

# ── Verify ────────────────────────────────────────────────────────────────────

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅", custom_id="gc_verify")
    async def verify(self, interaction, button):
        guild = interaction.guild
        verified = guild.get_role(VERIFIED_ROLE_ID)
        unverified = guild.get_role(UNVERIFIED_ROLE_ID)
        if verified in interaction.user.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
            return
        try:
            if unverified:
                await interaction.user.remove_roles(unverified)
            if verified:
                await interaction.user.add_roles(verified)
            await interaction.response.send_message("✅ You have been verified! Welcome to Grey County RP!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


# ── Applications ──────────────────────────────────────────────────────────────

class AppPart2Modal(discord.ui.Modal, title="Staff Application — Part 2 of 2"):
    def __init__(self, part1):
        super().__init__()
        self.part1 = part1

    professionalism = discord.ui.TextInput(label="What does 'Professional Staff Member' mean?", style=discord.TextStyle.paragraph, max_length=500)
    conflict = discord.ui.TextInput(label="Scenario: Two players arguing in Global Chat", style=discord.TextStyle.paragraph, max_length=500)
    rule_enforcement = discord.ui.TextInput(label="Scenario: Friend/high rank breaks a rule", style=discord.TextStyle.paragraph, max_length=500)
    maturity = discord.ui.TextInput(label="How do you handle a player trolling you?", style=discord.TextStyle.paragraph, max_length=500)
    agreements = discord.ui.TextInput(label="Type AGREE to confirm all policies", placeholder="Type AGREE", max_length=10)

    async def on_submit(self, interaction):
        if self.agreements.value.upper() != "AGREE":
            await interaction.response.send_message("❌ You must type AGREE to confirm the policies.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        app_id = f"{interaction.user.id}_{int(datetime.utcnow().timestamp())}"
        app_data = {**self.part1, "app_id": app_id, "author_id": interaction.user.id, "author_name": str(interaction.user),
                    "submitted_at": datetime.utcnow().isoformat(), "status": "pending",
                    "professionalism": self.professionalism.value, "conflict": self.conflict.value,
                    "rule_enforcement": self.rule_enforcement.value, "maturity": self.maturity.value}
        applications[app_id] = app_data
        save_json("applications", applications)
        try:
            results_ch = guild.get_channel(APP_RESULTS_CHANNEL) or await bot.fetch_channel(APP_RESULTS_CHANNEL)
        except:
            await interaction.followup.send("❌ Could not find results channel.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Grey County RP — Staff Application", color=0x5865F2, timestamp=datetime.utcnow())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Discord Username", value=self.part1["discord_username"], inline=True)
        embed.add_field(name="Age", value=self.part1["age"], inline=True)
        embed.add_field(name="Timezone", value=self.part1["timezone"], inline=True)
        embed.add_field(name="Previous Experience", value=self.part1["experience"], inline=False)
        embed.add_field(name="Motivation", value=self.part1["motivation"], inline=False)
        embed.add_field(name="Professionalism Definition", value=self.professionalism.value, inline=False)
        embed.add_field(name="Conflict Resolution", value=self.conflict.value, inline=False)
        embed.add_field(name="Rule Enforcement", value=self.rule_enforcement.value, inline=False)
        embed.add_field(name="Maturity Check", value=self.maturity.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id} | App ID: {app_id}")
        await results_ch.send(embed=embed, view=AppReviewView(app_id))
        await interaction.followup.send("✅ Application submitted! Do NOT ping staff about it.", ephemeral=True)


class AppPart1Modal(discord.ui.Modal, title="Staff Application — Part 1 of 2"):
    discord_username = discord.ui.TextInput(label="Discord Username", max_length=100)
    age = discord.ui.TextInput(label="Current Age", max_length=3)
    timezone = discord.ui.TextInput(label="Time Zone", placeholder="e.g. EST, PST, GMT", max_length=50)
    experience = discord.ui.TextInput(label="Previous Staffing Experience", style=discord.TextStyle.paragraph, max_length=500)
    motivation = discord.ui.TextInput(label="Why do you want to join Grey County RP staff?", style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction):
        await interaction.response.send_modal(AppPart2Modal(part1={
            "discord_username": self.discord_username.value, "age": self.age.value,
            "timezone": self.timezone.value, "experience": self.experience.value,
            "motivation": self.motivation.value,
        }))


class AppDenyModal(discord.ui.Modal, title="Deny Reason"):
    reason = discord.ui.TextInput(label="Reason for denial", style=discord.TextStyle.paragraph, max_length=500)
    def __init__(self, message):
        super().__init__()
        self.message = message

    async def on_submit(self, interaction):
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
            save_json("applications", applications)
            try:
                user = await bot.fetch_user(app["author_id"])
                await user.send(embed=discord.Embed(title="❌ Application Denied", description=f"Your Grey County RP staff application was denied.\n\n**Reason:** {self.reason.value}", color=0xED4245))
            except: pass
        embed = self.message.embeds[0]
        embed.color = 0xED4245
        embed.add_field(name="Decision", value=f"❌ Denied by {interaction.user.mention}\n**Reason:** {self.reason.value}", inline=False)
        await self.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ Application denied.", ephemeral=True)


class AppReviewView(discord.ui.View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅", custom_id="gc_app_accept")
    async def accept(self, interaction, button):
        if not is_senior(interaction.user):
            await interaction.response.send_message("❌ Only senior staff can review applications.", ephemeral=True)
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
            save_json("applications", applications)
            try:
                user = await bot.fetch_user(app["author_id"])
                await user.send(embed=discord.Embed(title="✅ Application Accepted!", description="Congratulations! Your Grey County RP staff application has been accepted!\n\nWelcome to the team!", color=0x57F287))
            except: pass
        embed = interaction.message.embeds[0]
        embed.color = 0x57F287
        embed.add_field(name="Decision", value=f"✅ Accepted by {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Application accepted!", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌", custom_id="gc_app_deny")
    async def deny(self, interaction, button):
        if not is_senior(interaction.user):
            await interaction.response.send_message("❌ Only senior staff can review applications.", ephemeral=True)
            return
        await interaction.response.send_modal(AppDenyModal(interaction.message))


class AppPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.primary, emoji="📋", custom_id="gc_apply")
    async def apply(self, interaction, button):
        await interaction.response.send_modal(AppPart1Modal())


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="❓", description="Questions & general help", value="general"),
            discord.SelectOption(label="Report a Player", emoji="🚨", description="Report rule violations", value="report"),
            discord.SelectOption(label="Staff Complaint", emoji="⚖️", description="Complaint against staff", value="complaint"),
            discord.SelectOption(label="Other", emoji="💬", description="Anything else", value="other"),
        ]
        super().__init__(placeholder="Select a ticket type...", min_values=1, max_values=1, options=options, custom_id="gc_ticket_select")

    async def callback(self, interaction):
        await open_ticket(interaction, self.values[0])


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Assign to me", style=discord.ButtonStyle.primary, emoji="🙋", custom_id="gc_ticket_assign")
    async def assign(self, interaction, button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can assign tickets.", ephemeral=True)
            return
        ticket = tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return
        ticket["assigned_to"] = interaction.user.id
        save_json("tickets", tickets)
        await interaction.response.send_message(embed=discord.Embed(description=f"🙋 {interaction.user.mention} assigned to this ticket.", color=0x57F287))

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="gc_ticket_close")
    async def close(self, interaction, button):
        ticket = tickets.get(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)
            return
        if not (is_staff(interaction.user) or ticket["author_id"] == interaction.user.id):
            await interaction.response.send_message("❌ You can't close this ticket.", ephemeral=True)
            return
        ticket["status"] = "closed"
        save_json("tickets", tickets)
        await interaction.response.send_message(embed=discord.Embed(title="Ticket Closed", description=f"🔒 Closed by {interaction.user.mention}. Deleting in 5 seconds.", color=0xED4245))
        await asyncio.sleep(5)
        await interaction.channel.delete()


async def open_ticket(interaction, ticket_type):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    for t in tickets.values():
        if t["author_id"] == interaction.user.id and t["type"] == ticket_type and t["status"] == "open":
            ch = guild.get_channel(t["channel_id"])
            if ch:
                await interaction.followup.send(f"❌ You already have an open {ticket_type} ticket: {ch.mention}", ephemeral=True)
                return
    staff_roles = [guild.get_role(rid) for rid in STAFF_ROLE_IDS if guild.get_role(rid)]
    overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
    for role in staff_roles:
        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    number = len(tickets) + 1
    channel = await guild.create_text_channel(f"{ticket_type}-{number:04d}", overwrites=overwrites, topic=f"Ticket #{number} | {ticket_type} | {interaction.user}")
    tickets[str(channel.id)] = {"number": number, "type": ticket_type, "author_id": interaction.user.id, "author_name": str(interaction.user), "channel_id": channel.id, "assigned_to": None, "opened_at": datetime.utcnow().isoformat(), "status": "open"}
    save_json("tickets", tickets)
    pings = " ".join(r.mention for r in staff_roles[:3])
    embed = discord.Embed(title=f"🎫 {ticket_type.title()} Ticket #{number}", description=f"Hey {interaction.user.mention}! A staff member will be with you shortly.\n\nPlease describe your issue in detail.", color=0x5865F2, timestamp=datetime.utcnow())
    embed.set_footer(text=f"Opened by {interaction.user}")
    await channel.send(content=pings, embed=embed, view=TicketControlView())
    await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)


# ── LOA ───────────────────────────────────────────────────────────────────────

class LOAModal(discord.ui.Modal, title="Leave of Absence Request"):
    reason = discord.ui.TextInput(label="Reason for LOA", style=discord.TextStyle.paragraph, max_length=500)
    duration = discord.ui.TextInput(label="Duration", placeholder="e.g. 1 week, 2 weeks", max_length=100)
    return_date = discord.ui.TextInput(label="Expected Return Date", placeholder="e.g. June 1st", max_length=100)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        loa_id = f"{interaction.user.id}_{int(datetime.utcnow().timestamp())}"
        loas[loa_id] = {"loa_id": loa_id, "author_id": interaction.user.id, "author_name": str(interaction.user), "reason": self.reason.value, "duration": self.duration.value, "return_date": self.return_date.value, "submitted_at": datetime.utcnow().isoformat(), "status": "pending"}
        save_json("loas", loas)
        try:
            loa_ch = guild.get_channel(LOA_CHANNEL) or await bot.fetch_channel(LOA_CHANNEL)
        except:
            await interaction.followup.send("❌ Could not find LOA channel.", ephemeral=True)
            return
        embed = discord.Embed(title="🏖️ Leave of Absence Request", color=0xFFA500, timestamp=datetime.utcnow())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.add_field(name="Duration", value=self.duration.value, inline=True)
        embed.add_field(name="Expected Return", value=self.return_date.value, inline=True)
        embed.set_footer(text=f"User ID: {interaction.user.id} | LOA ID: {loa_id}")
        await loa_ch.send(embed=embed, view=LOAReviewView(loa_id))
        loa_role = guild.get_role(LOA_ROLE_ID)
        if loa_role:
            await interaction.user.add_roles(loa_role)
        await interaction.followup.send("✅ LOA request submitted!", ephemeral=True)


class LOAReviewView(discord.ui.View):
    def __init__(self, loa_id):
        super().__init__(timeout=None)
        self.loa_id = loa_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="gc_loa_approve")
    async def approve(self, interaction, button):
        if not is_senior(interaction.user):
            await interaction.response.send_message("❌ Only senior staff can approve LOAs.", ephemeral=True)
            return
        loa_id = None
        if interaction.message.embeds:
            footer = interaction.message.embeds[0].footer.text
            if footer and "LOA ID:" in footer:
                loa_id = footer.split("LOA ID:")[-1].strip()
        loa = loas.get(loa_id)
        if loa:
            loa["status"] = "approved"
            loa["reviewed_by"] = str(interaction.user)
            save_json("loas", loas)
            try:
                user = await bot.fetch_user(loa["author_id"])
                await user.send(embed=discord.Embed(title="✅ LOA Approved", description=f"Your LOA has been approved!\n\n**Duration:** {loa['duration']}\n**Return Date:** {loa['return_date']}", color=0x57F287))
            except: pass
        embed = interaction.message.embeds[0]
        embed.color = 0x57F287
        embed.add_field(name="Decision", value=f"✅ Approved by {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ LOA approved!", ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌", custom_id="gc_loa_deny")
    async def deny(self, interaction, button):
        if not is_senior(interaction.user):
            await interaction.response.send_message("❌ Only senior staff can deny LOAs.", ephemeral=True)
            return
        loa_id = None
        if interaction.message.embeds:
            footer = interaction.message.embeds[0].footer.text
            if footer and "LOA ID:" in footer:
                loa_id = footer.split("LOA ID:")[-1].strip()
        loa = loas.get(loa_id)
        if loa:
            loa["status"] = "denied"
            loa["reviewed_by"] = str(interaction.user)
            save_json("loas", loas)
            try:
                guild = interaction.guild
                user = await bot.fetch_user(loa["author_id"])
                member = guild.get_member(loa["author_id"])
                loa_role = guild.get_role(LOA_ROLE_ID)
                if member and loa_role:
                    await member.remove_roles(loa_role)
                await user.send(embed=discord.Embed(title="❌ LOA Denied", description="Your LOA request has been denied. Please contact senior staff.", color=0xED4245))
            except: pass
        embed = interaction.message.embeds[0]
        embed.color = 0xED4245
        embed.add_field(name="Decision", value=f"❌ Denied by {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ LOA denied.", ephemeral=True)


class LOAPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit LOA Request", style=discord.ButtonStyle.primary, emoji="🏖️", custom_id="gc_loa_submit")
    async def submit(self, interaction, button):
        await interaction.response.send_modal(LOAModal())


# ── Infractions & Promotions ──────────────────────────────────────────────────

class InfractionModal(discord.ui.Modal, title="Issue Infraction"):
    target = discord.ui.TextInput(label="Member (username or ID)", max_length=100)
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, max_length=500)
    punishment = discord.ui.TextInput(label="Punishment", placeholder="e.g. Warning, Strike 1, Demotion", max_length=100)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        inf_id = f"INF-{len(infractions)+1:04d}"
        infractions[inf_id] = {"inf_id": inf_id, "target": self.target.value, "reason": self.reason.value, "punishment": self.punishment.value, "issued_by": str(interaction.user), "issued_at": datetime.utcnow().isoformat()}
        save_json("infractions", infractions)
        try:
            inf_ch = guild.get_channel(INFRACTIONS_CHANNEL) or await bot.fetch_channel(INFRACTIONS_CHANNEL)
        except:
            await interaction.followup.send("❌ Could not find infractions channel.", ephemeral=True)
            return
        embed = discord.Embed(title=f"⚖️ Infraction — {inf_id}", color=0xED4245, timestamp=datetime.utcnow())
        embed.add_field(name="Member", value=self.target.value, inline=True)
        embed.add_field(name="Punishment", value=self.punishment.value, inline=True)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user}")
        await inf_ch.send(embed=embed)
        await interaction.followup.send(f"✅ Infraction {inf_id} logged!", ephemeral=True)


class PromotionModal(discord.ui.Modal, title="Issue Promotion"):
    target = discord.ui.TextInput(label="Member (username or ID)", max_length=100)
    old_rank = discord.ui.TextInput(label="Previous Rank", max_length=100)
    new_rank = discord.ui.TextInput(label="New Rank", max_length=100)
    reason = discord.ui.TextInput(label="Reason for Promotion", style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        try:
            prom_ch = guild.get_channel(PROMOTIONS_CHANNEL) or await bot.fetch_channel(PROMOTIONS_CHANNEL)
        except:
            await interaction.followup.send("❌ Could not find promotions channel.", ephemeral=True)
            return
        embed = discord.Embed(title="🎉 Promotion", color=0x57F287, timestamp=datetime.utcnow())
        embed.add_field(name="Member", value=self.target.value, inline=True)
        embed.add_field(name="Previous Rank", value=self.old_rank.value, inline=True)
        embed.add_field(name="New Rank", value=self.new_rank.value, inline=True)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user}")
        await prom_ch.send(embed=embed)
        await interaction.followup.send("✅ Promotion logged!", ephemeral=True)


# ── Panel Setup ───────────────────────────────────────────────────────────────

async def post_all_panels(guild):
    async def clear_post(channel_id, items):
        try:
            ch = guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            await ch.purge(limit=50)
            for embed, view in items:
                await ch.send(embed=embed, view=view) if view else await ch.send(embed=embed)
            print(f"✅ Posted in #{ch.name}")
        except Exception as e:
            print(f"❌ Error in {channel_id}: {e}")

    await clear_post(VERIFY_CHANNEL_ID, [(discord.Embed(title="✅ Verify — Grey County RP", description="Click the button below to verify yourself and gain access to the server!", color=0x57F287), VerifyView())])
    await clear_post(DISCORD_RULES_CHANNEL, [(discord.Embed(title="📜 Discord Rules — Grey County RP", description="**1. Respect** — Treat all members with respect at all times.\n\n**2. No Harassment** — Bullying, threats, or targeted harassment will not be tolerated.\n\n**3. No NSFW** — Keep all content appropriate for all ages.\n\n**4. No Spam** — Do not spam messages, pings, or emojis.\n\n**5. English Only** — Please communicate in English in all public channels.\n\n**6. No Advertising** — Do not advertise other servers without permission.\n\n**7. Follow Discord ToS** — All Discord Terms of Service apply.\n\n**8. Staff Decisions are Final** — Respect the decisions made by staff.", color=0x5865F2), None)])
    await clear_post(INGAME_RULES_CHANNEL, [(discord.Embed(title="🚓 In-Game Rules — Grey County RP", description="**1. No VDM** — Vehicle Deathmatch is strictly prohibited.\n\n**2. No RDM** — Random Deathmatch is strictly prohibited.\n\n**3. Realistic Roleplay** — All roleplay must be realistic and professional.\n\n**4. FRP** — Fail Roleplay will result in punishment.\n\n**5. Respect Officers** — Follow all LEO commands during active RP.\n\n**6. No Exploits** — Using game exploits or glitches is banned.\n\n**7. Civilians** — Must follow all traffic laws and RP scenarios.\n\n**8. Mic Required** — A working microphone is required for active RP.", color=0x5865F2), None)])
    await clear_post(ABOUT_US_CHANNEL, [(discord.Embed(title="⚖️ About Grey County RP", description="# ⚖️ GREY COUNTY ROLEPLAY | VINE STATE ⚖️\n**Professionalism. Realism. Integrity.**\n\nGrey County RP is a strictly professional ERLC community based in Vine State. We are looking for mature, dedicated members who want to experience roleplay at its highest level.\n\n**🏛️ WHY JOIN GREY COUNTY?**\n• Mature Environment: High standards for behavior and RP quality\n• Specialized Departments: Realistic structures for LEO, Fire, and Civ\n• Advanced CAD/MDT: Stay organized during patrols\n• Dedicated Staff: Active management that actually listens\n\n**🚓 DIVISIONS**\n👮 Vine State Police Department (VSPD)\n🚔 Grey County Sheriff's Office (GCSO)\n🚒 Vine State Fire & Rescue (VSFR)\n👨‍👩‍👧‍👦 Certified Civilian Operations", color=0x5865F2), None)])
    await clear_post(SERVER_AD_CHANNEL, [(discord.Embed(title="🔗 Join Grey County RP", description="# ⚖️ GREY COUNTY ROLEPLAY | VINE STATE ⚖️\n**Professionalism. Realism. Integrity.**\n\n*Are you tired of green-run servers and chaotic roleplay? Grey County RP is a strictly professional ERLC community based in Vine State.*\n\n**🚓 RECRUITING FOR ALL DIVISIONS**\n👮 Vine State Police Department (VSPD)\n🚔 Grey County Sheriff's Office (GCSO)\n🚒 Vine State Fire & Rescue (VSFR)\n👨‍👩‍👧‍👦 Certified Civilian Operations\n\n**🔗 SECURE YOUR SPOT**\nJoin the Discord: https://discord.gg/EVKCSgb522", color=0x5865F2), None)])
    await clear_post(TICKETS_CHANNEL, [(discord.Embed(title="🎫 Grey County RP — Support Tickets", description="Need help? Select a ticket type below and a staff member will assist you shortly.", color=0x5865F2), TicketPanelView())])
    await clear_post(APPS_CHANNEL, [(discord.Embed(title="📋 Grey County RP — Staff Applications", description="**Want to join the Grey County RP Staff Team?**\n\nClick the button below to begin your application.\n\n⚠️ **Anti-AI Policy** — AI-generated responses will result in an instant denial and blacklist.\n⚠️ **No Solicitation** — DMing or pinging staff about your application will result in denial.\n⚠️ **Be Honest** — All information must be your own truthful responses.\n\nApplications are reviewed by senior staff. You will be notified via DM.", color=0x5865F2), AppPanelView())])
    await clear_post(LOA_CHANNEL, [(discord.Embed(title="🏖️ Leave of Absence", description="Need to take a break? Submit your LOA request below.\n\nYou will receive the LOA role while on leave. LOA requests must be approved by senior staff.", color=0xFFA500), LOAPanelView())])


# ── Commands ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="setup", description="Post all panels (senior staff only)")
@app_commands.guilds(GUILD_OBJ)
async def setup(interaction):
    if not is_senior(interaction.user):
        await interaction.response.send_message("❌ Only senior staff can run setup.", ephemeral=True)
        return
    await interaction.response.send_message("⏳ Setting up all channels...", ephemeral=True)
    await post_all_panels(interaction.guild)
    await interaction.edit_original_response(content="✅ All panels posted!")


@bot.tree.command(name="infraction", description="Issue an infraction (senior staff only)")
@app_commands.guilds(GUILD_OBJ)
async def infraction(interaction):
    if not is_senior(interaction.user):
        await interaction.response.send_message("❌ Only senior staff can issue infractions.", ephemeral=True)
        return
    await interaction.response.send_modal(InfractionModal())


@bot.tree.command(name="promote", description="Issue a promotion (senior staff only)")
@app_commands.guilds(GUILD_OBJ)
async def promote(interaction):
    if not is_senior(interaction.user):
        await interaction.response.send_message("❌ Only senior staff can issue promotions.", ephemeral=True)
        return
    await interaction.response.send_modal(PromotionModal())


@bot.tree.command(name="loa", description="Submit a Leave of Absence request")
@app_commands.guilds(GUILD_OBJ)
async def loa_cmd(interaction):
    await interaction.response.send_modal(LOAModal())


# ── Events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    global applications, loas, infractions, tickets
    applications = load_json("applications")
    loas = load_json("loas")
    infractions = load_json("infractions")
    tickets = load_json("tickets")

    bot.add_view(VerifyView())
    bot.add_view(AppPanelView())
    bot.add_view(AppReviewView("placeholder"))
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControlView())
    bot.add_view(LOAPanelView())
    bot.add_view(LOAReviewView("placeholder"))

    bot.tree.copy_global_to(guild=GUILD_OBJ)
    await bot.tree.sync(guild=GUILD_OBJ)

    print(f"✅ Grey County Bot logged in as {bot.user}")
    print(f"   {len(applications)} apps | {len(tickets)} tickets | {len(loas)} LOAs loaded.")

bot.run(os.getenv('TOKEN_SECOND_BOT'))
