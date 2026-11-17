import os
import random
import datetime
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord.utils import get
from redis import Redis, RedisStream
from discord_helpers import SessionMsg, VC


# -------------------- init & helpers --------------------

# env
load_dotenv()
DISCORD_TOKEN = int(os.getenv("DISCORD_TOKEN"))
TEXT_CHANNEL = int(os.getenv("TEXT_CHANNEL"))
VOICE_CHANNEL = int(os.getenv("VOICE_CHANNEL"))

# bot
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("z", "Z"), intents=intents, help_command=None)

# redis
r = Redis()
rs = RedisStream()

# discord helpers
vc = VC(VOICE_CHANNEL)
session = None

# role ids
manager_id = None
pm_id = None

# tags
tags = {"manager": set(), "pm": set()}

# bot cmds
cmds = {
    "agenda": {"cmd": "zagenda/za <agenda>", "description": "Set the meeting agenda to gain corporate aura."},
    "broadcast": {"cmd": "zbroadcast/zb <message>", "description": "Add messages to the daily broadcast pool."},
    "change": {"cmd": "zchange/zc {manager/pm} <@user> {dice 1..6}", "description": "Oust the higher-ups."},
    "excuse": {"cmd": "zexcuse/ze <excuse>", "description": "Excuse me?"},
    "hallucinate": {"cmd": "zhallucinate/zh <hallucination>", "description": "Meow?"},
    "roll": {"cmd": "zroll/zr {dice 1..6}", "description": "Roll a dice to make life changing decisions."},
    "tag": {"cmd": "ztag/zt {manager/pm} <tag>", "description": "Auto-tag those who haunt your dreams."},
    "help": {"cmd": "zhelp", "description": "Helps if you want help about the help command."},
}


def init():
    if session is None and not vc.is_new_call(before, after):
        msg_id = rs.get_latest_data("call")["msg_id"]
        session = Session(msg_id, text_channel)

    if manager_id is None:
        manager_id = rs.get_latest_data("manager")["value"]

    if pm_id is None:
        pm_id = rs.get_latest_data("pm")["value"]

    if len(tags["manager"]) == 0:
        tags["manager"] = r.redis.smembers("manager_tags")

    if len(tags["pm"]) == 0:
        tags["pm"] = r.redis.smembers("pm_tags")


def refresh_cache_roles():
    manager_id = rs.get_latest_data("manager")["value"]
    pm_id = rs.get_latest_data("pm")["value"]


def refresh_cache_tags():
    tags["manager"] = r.redis.smembers("tags_manager")
    tags["pm"] = r.redis.smembers("tags_pm")


def roll(choice: int):
    return random.randint(1, 6) == choice


def roll_time():
    choice = time.time_ns() % 6 + 1
    return roll(choice)


# -------------------- activity --------------------


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    guild = member.guild
    text_channel = guild.get_channel(TEXT_CHANNEL)
    is_manager = member.id == manager_id
    is_pm = member.id == pm_id
    avatar = "🐍" if is_manager or is_pm else "🦮"
    name = member.display_name
    init()

    if vc.is_joining(before, after):
        if vc.is_new_call(before, after):
            embed = discord.Embed(title="🗣️ Standup in session", color=discord.Color.random())
            msg = await text_channel.send(content=get(guild.roles, name="g***r").mention, embed=embed)
            session = SessionMsg(msg.id, text_channel)
            session.update_log(f"{avatar} {name}: Zoin up!{" Why is everyone late?" if is_manager else ""}")
            session.update_img(f'https://media.discordapp.net/stickers/{get(guild.stickers, name="almostnice")}.webp')
            rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "new_call"})
        else:
            session.update_log(f"{avatar} {name}: Zoined.{" Who's missing?" if is_manager else ""}")
        rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "join_call"})

    if vc.is_leaving(before, after):
        excuse = r.get_random_entry_from_stream("excuse")
        embed_add_log(f"{avatar} {name}: Dropping off, {excuse}.{" You can sit down now." if is_manager else ""}")
        if vc.is_end_call(before, after):
            session = None
            rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "end_call"})
        rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "leave_call", "excuse": excuse})

    if vc.is_mute(before, after) or vc.is_deafen(before, after):
        excuse = r.get_random_entry_from_stream("excuse")
        embed_add_log(f"{avatar} {name}: Excuse me, {excuse}.{" Only work discussions allowed." if is_manager else ""}")
        rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "pause_call", "excuse": excuse})

    if vc.is_unmute(before, after) or vc.is_undeafen(before, after):
        embed_add_log(f"{avatar} {name}: Back.{" Silence! Update me on what I missed." if is_manager else ""}")
        rs.add("call", {"msg_id": msg.id, "member_id": member.id, "kind": "resume_call"})


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    init()

    if roll_time():
        manager = message.guild.get_member(manager_id)
        pm = message.guild.get_member(pm_id)
        content = message.content.lower().split()
        if any(word in content for word in tags["manager"]):
            await message.reply(f"cc {manager.mention}")
        if any(word in content for word in tags["pm"]):
            await message.reply(f"cc {pm.mention}")

    if roll_time():
        hallucination = rs.get_random_data("hallucination")
        embed = discord.Embed(title="🤖", description=hallucination, color=discord.Color.red())
        msg = await message.channel.send()
        await msg.delete(delay=10)

    # allows @bot.command() functions to still work
    await bot.process_commands(message)


@tasks.loop(time=datetime.time(hour=3, minute=30))
async def daily_broadcast():
    if roll_time():
        channel = bot.get_channel(TEXT_CHANNEL)
        broadcast = rs.get_random_data("broadcast")
        embed = discord.Embed(title="📢", description=broadcast, color=discord.Color.orange())
        await channel.send(embed)


# -------------------- commands --------------------


async def dice_roll(ctx, choice: int):
    r = roll(choice)
    await valid_use(ctx) if r else ctx.message.add_reaction("↪🎲")
    return r


async def invalid_use(ctx, cmd: str):
    await ctx.message.add_reaction("❗️")
    embed = discord.Embed(description=f"Usage: {cmds[cmd]["cmd"]}", color=discord.Color.blue())
    if roll_time():
        embed.set_image(url="https://i.imgflip.com/21kggt.jpg")
    await ctx.reply(embed=embed)


async def valid_use(ctx):
    await ctx.message.add_reaction("✅")


@bot.command(name="agenda", aliases=["AGENDA", "a", "A"])
async def cmd_agenda(ctx, agenda: str):
    if agenda is None:
        return await invalid_use(ctx, "agenda")

    await valid_use(ctx)
    embed = discord.Embed(title="✍️ Meeting Agenda", description=agenda, color=discord.Color.green())
    embed.set_footer(f"Set by {ctx.author.name}")
    await ctx.reply(embed=embed)
    rs.add("agenda", {"member_id": ctx.author.id, "value": agenda})


@bot.command(name="broadcast", aliases=["BROADCAST", "b", "B"])
async def cmd_broadcast(ctx, message: str):
    if message is None:
        return await invalid_use(ctx, "broadcast")

    await valid_use(ctx)
    rs.add("broadcast", {"member_id": ctx.author.id, "value": message})


@bot.command(name="change", aliases=["CHANGE", "c", "C"])
async def cmd_change(ctx, change: str, change_to: discord.Member, choice: int = None):
    if change not in ("manager", "pm") or type(change_to) is not discord.Member or choice not in range(1, 7):
        return await invalid_use(ctx, "change")

    if await dice_roll(ctx, choice):
        await valid_use(ctx)
        rs.add(change, {"member_id": ctx.author.id, "value": change_to.id})
        refresh_cache_roles()


@bot.command(name="excuse", aliases=["EXCUSE", "e", "E"])
async def cmd_excuse(ctx, excuse: str):
    if excuse is None:
        return await invalid_use(ctx, "excuse")

    await valid_use(ctx)
    rs.add("excuse", {"member_id": ctx.author.id, "value": excuse})


@bot.command(name="hallucinate", aliases=["HALLUCINATE", "h", "H"])
async def cmd_hallucinate(ctx, hallucination: str):
    if hallucination is None:
        return await invalid_use(ctx, "hallucinate")

    await valid_use(ctx)
    rs.add("hallucination", {"member_id": ctx.author.id, "value": hallucination})


@bot.command(name="roll", aliases=["ROLL", "r", "R"])
async def cmd_roll(ctx, choice: int):
    if choice not in range(1, 7):
        return await invalid_use(ctx, "roll")

    await valid_use(ctx)
    await dice_roll(ctx, choice)


@bot.command(name="tag", aliases=["tag", "t", "T"])
async def cmd_tag(ctx, role: str, tag: str):
    if role not in ("manager", "pm") or tag is None:
        return await invalid_use(ctx, "tag")

    await valid_use(ctx)
    r.redis.sadd(f"tags_{role}", tag)
    refresh_cache_tags()


@bot.command(name="help", aliases=["HELP"])
async def cmd_help(ctx):
    await valid_use(ctx)
    embed = discord.Embed(title="🧑‍💻 Help Desk", color=discord.Color.blue())
    for v in cmds.values():
        for cmd, description in v.items():
            embed.add_field(name=cmd, value=description, inline=False)
    await ctx.reply(embed=embed)


# -------------------- end --------------------

bot.run(DISCORD_TOKEN)
