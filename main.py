import os
import random
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.utils import get
from supabase_db import DB

# -------------------- init --------------------

load_dotenv()
DISCORD_TOKEN = int(os.getenv("DISCORD_TOKEN"))
TEXT_CH = int(os.getenv("TEXT_CH"))
VOICE_CH = int(os.getenv("VOICE_CH"))


intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("z", "Z"), intents=intents, help_command=None)

db = DB()

# -------------------- helpers: voice channel activity --------------------


def on_voice_channel(voice_state: discord.VoiceState):
    return voice_state.channel and voice_state.channel.id == VOICE_CH


def is_new_session(after: discord.VoiceState):
    return on_voice_channel(after) and len(after.channel.members) == 1 and not db.get_curr_session()


def is_joining(member: discord.Member, after: discord.VoiceState):
    return on_voice_channel(after) and member.id not in db.get_joined_members()


def is_leaving(before: discord.VoiceState, after: discord.VoiceState):
    return on_voice_channel(before) and not on_voice_channel(after)


def is_rejoining(member: discord.Member, after: discord.VoiceState):
    return is_joining(member, after) and member.id in db.get_left_members()


def is_step_out(before: discord.VoiceState, after: discord.VoiceState):
    return on_voice_channel(after) and ((not before.self_mute and after.self_mute) or (not before.self_deaf and after.self_deaf))


def is_end_session(before: discord.VoiceState, after: discord.VoiceState):
    return is_leaving(before, after) and len(before.channel.members) == 0


# -------------------- helpers: misc --------------------


def dice_roll(choice: int):
    return random.randint(1, 6) == choice


def dice_roll_time():
    choice = time.time_ns() % 6 + 1
    return dice_roll(choice)


def oblique(string: str):
    return "".join(["𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"[ord(char) - ord("A")] if char.isalpha() else char for char in string.upper()])


# -------------------- helpers: embed updates --------------------


def get_msg_embed(ctx):
    session_id = db.get_curr_session()
    if session_id:
        msg = ctx.fetch_message(session_id)
        if msg.embeds:
            return msg, msg.embeds[0]


async def embed_add_log(ctx, log: str):
    msg, embed = get_msg_embed(ctx)
    logs = embed.footer.text + f"\n{log}"
    embed.set_footer(logs)
    await msg.edit(embed=embed)


async def embed_update_title(ctx, title: str):
    msg, embed = get_msg_embed(ctx)
    embed = msg.embeds[0]
    embed.title = title
    await msg.edit(embed=embed)


async def embed_update_img(ctx, img_url: str):
    msg, embed = get_msg_embed(ctx)
    embed = msg.embeds[0]
    embed.set_image(url=img_url)
    embed.set_thumbnail(url=img_url)
    await msg.edit(embed=embed)


# -------------------- bot functions --------------------


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    text_ch = guild.get_channel(TEXT_CH)
    is_manager = get(guild.roles, name="manager") in member.roles
    is_pm = get(guild.roles, name="PM") in member.roles
    avatar = "🐍" if is_manager or is_pm else "🦮"

    if is_new_session(after):
        embed = discord.Embed(
            title=oblique("zoin up"),
            color=discord.Color.random(),
        )
        embed.set_image(url=f'https://media.discordapp.net/stickers/{get(guild.stickers, name="almostnice")}.webp')
        embed.set_thumbnail(url=f'https://media.discordapp.net/stickers/{get(guild.stickers, name="almostnice")}.webp')
        embed.set_footer(text="")
        msg = await text_ch.send(content=get(guild.roles, name="g***r").mention, embed=embed)

        db.create_session(id=msg.id)
        db.join_call(member.id)

        embed_update_title(text_ch, db.get_latest_agenda())

    if is_joining(member, after):
        db.join_call(member.id)

    if is_leaving(member, after):
        excuse = db.get_random_excuse()
        db.leave_call(excuse, member.id)
        embed_add_log(text_ch, oblique(f"{avatar} {member.display_name}: I'll have to drop off due to {excuse}.{" You can sit now." if is_manager else ""}"))

    if is_step_out(before, after):
        excuse = db.get_random_excuse()
        db.pause_call(excuse, member.id)
        embed_add_log(text_ch, oblique(f"{avatar} {member.display_name}: I have to step out due to {excuse}.{" Keep standing." if is_manager else ""}"))

    if is_end_session(before):
        db.end_curr_session()


# -------------------- bot commands --------------------


def _use_str(cmd: str, args: str):
    if len(args) > 0:
        return f"`{cmd} [dice_roll_1..6] {args}`"
    return f"`{cmd} [dice_roll_1..6]`"


async def how_to_use(ctx, cmd: str, args: str):
    await ctx.message.add_reaction("❗️")
    embed = discord.Embed(description=f"Use: {_use_str(cmd, args)}", color=discord.Color.blue())
    await ctx.reply(embed=embed)


async def _cmd_helper(ctx, incorrect_use: bool, choice: int, cmd: str, args: str):
    if incorrect_use:
        await how_to_use(ctx, cmd, args)
        return False
    if dice_roll(choice):
        await ctx.message.add_reaction("✅")
        return True
    await ctx.message.add_reaction("↪🎲")
    return False


@bot.command(name="agenda", aliases=["AGENDA", "a", "A"])
async def cmd_agenda(ctx, choice: int = None, agenda: str = None):
    if await _cmd_helper(ctx, choice is None, choice, "zagenda", "[agenda]"):
        db.add_agenda(agenda, ctx.author.id)
        embed_update_title(ctx, agenda)


@bot.command(name="broadcast", aliases=["BROADCAST"])
async def cmd_broadcast(ctx, choice: int = None, message: str = None):
    if await _cmd_helper(ctx, choice is None or message is None, choice, "broadcast", "[message]"):
        db.add_broadcast(message, ctx.author.id)


@bot.command(name="callout", aliases=["CALLOUT"])
async def cmd_callout(ctx, choice: int = None, role: str = None, callout: str = None):
    if await _cmd_helper(
        ctx,
        choice is None or role is None or callout is None or role.lower() not in ["manager", "pm"],
        choice,
        "zcallout",
        "[manager/pm] [callout]",
    ):
        if role.lower() == "manager":
            db.add_manager_callout(callout, ctx.author.id)
        if role.lower() == "pm":
            db.add_pm_callout(callout, ctx.author.id)


@bot.command(name="excuse", aliases=["EXCUSE", "e", "E"])
async def cmd_excuse(ctx, choice: int = None, excuse: str = None):
    if await _cmd_helper(ctx, choice is None or excuse is None, choice, "zexcuse", "[excuse]"):
        db.add_excuse(excuse, ctx.author.id)


@bot.command(name="hallucinate", aliases=["HALLUCINATE", "hallucination", "HALLUCINATION"])
async def cmd_hallucinate(ctx, choice: int = None, hallucination: str = None):
    if await _cmd_helper(ctx, choice is None or hallucination is None, choice, "zhallucinate", "[hallucination]"):
        db.add_hallucination(hallucination, ctx.author.id)


@bot.command(name="roll", aliases=["ROLL"])
async def cmd_roll(ctx, choice: int = None):
    await _cmd_helper(ctx, choice is None, choice, "zroll", "")


@bot.command(name="help", aliases=["HELP", "h", "H", "man", "MAN"])
async def cmd_help(ctx, choice: int = None):
    if await _cmd_helper(ctx, choice is None, choice, "zhelp", ""):
        embed = discord.Embed(title="🧑‍💻 Help Desk", description="All commands need a successful dice roll to function.", color=discord.Color.blue())
        embed.add_field(name=_use_str("zagenda", "[agenda]"), value="Set the meeting agenda to gain corporate aura.", inline=False)
        embed.add_field(name=_use_str("zbroadcast", "[message]"), value="Add messages to the daily broadcast pool.", inline=False)
        embed.add_field(name=_use_str("zcallout", "[manager/pm] [callout]"), value="Add callouts to annoy the people who haunt your dreams.", inline=False)
        embed.add_field(name=_use_str("zexcuse", "[excuse]"), value="Excuse me?", inline=False)
        embed.add_field(name=_use_str("zhallucinate", "[hallucination]"), value="Meow.", inline=False)
        embed.add_field(name=_use_str("zroll", ""), value="Roll a dice to resolve arguments, decide hangouts, or make life changing decisions.", inline=False)
        embed.add_field(name=_use_str("zhelp/zman/zh", ""), value="Helps if you want help about the help command.", inline=False)
        await ctx.reply(embed=embed)
