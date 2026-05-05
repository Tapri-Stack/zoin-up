import os
import random
import time
from dotenv import load_dotenv
import discord
from discord.ext import commands
from supabase_db import DB

# -------------------- init --------------------

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


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
    return voice_state.channel and voice_state.channel.id == db.get_server_id("voice_tapri", "channel")


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


def dice_roll(choice):
    return random.randint(1, 6) == choice


def dice_roll_time():
    choice = time.time_ns() % 6 + 1
    return dice_roll(choice)


def oblique(string: str):
    return "".join(["𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"[ord(char) - ord("A")] if char.isalpha() else char for char in string.upper()])


# -------------------- helpers: embed updates --------------------


async def embed_add_log(msg: discord.Message, log: str):
    if msg.embeds:
        embed = msg.embeds[0]
        logs = embed.footer.text + f"\n{log}"
        embed.set_footer(logs)
        await msg.edit(embed=embed)


async def embed_update_title(msg: discord.Message, title: str):
    if msg.embeds:
        embed = msg.embeds[0]
        embed.title = title
        await msg.edit(embed=embed)


async def embed_update_img(msg: discord.Message, img_url: str):
    if msg.embeds:
        embed = msg.embeds[0]
        embed.set_image(url=img_url)
        embed.set_thumbnail(url=img_url)
        await msg.edit(embed=embed)


# -------------------- bot functions --------------------


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    text_ch = member.guild.get_channel(db.get_server_id("text_tapri", "channel"))
    team_manager = member.guild.get_member(db.get_server_id("team_manager", "member"))
    product_manager = member.guild.get_member(db.get_server_id("product_manager", "member"))
    msg = await text_ch.fetch_message(db.get_curr_session())

    if is_new_session(after):
        embed = discord.Embed(
            title=oblique("zoin up"),
            color=discord.Color.random(),
        )
        embed.set_image(url=f'https://media.discordapp.net/stickers/{db.get_server_id("almostnice", "sticker")}.webp')
        embed.set_thumbnail(url=f'https://media.discordapp.net/stickers/{db.get_server_id("almostnice", "sticker")}.webp')
        embed.set_footer(text="")
        msg = await text_ch.send(embed=embed)

        db.create_session(id=msg.id)
        db.join_call(member.id)

        embed_add_log(msg, oblique(f"{member.display_name} requested for a zoin up."))
        embed_update_title(msg, db.get_latest_agenda())

    if is_joining(member, after):
        db.join_call(member.id)
        embed_add_log(msg, oblique(f"{member.display_name} zoined."))

    if is_leaving(member, after):
        db.leave_call(member.id)
        embed_add_log(msg, oblique(f"{member.display_name} left due to {db.get_random_excuse()}."))

    if is_step_out(before, after):
        db.pause_call(member.id)
        embed_add_log(msg, oblique(f"{member.display_name} had to step out due to {db.get_random_excuse()}."))

    if is_end_session(before):
        db.end_curr_session()


# -------------------- bot commands --------------------


async def how_to_use(ctx, cmd_use: str):
    await ctx.message.add_reaction("❗️")
    embed = discord.Embed(description=f"Use: `{cmd_use}`", color=discord.Color.blue())
    if dice_roll_time():
        embed.set_image("https://i.imgflip.com/21kggt.jpg")
    await ctx.reply(embed=embed)


@bot.command(name="roll")
async def cmd_roll(ctx, *, choice: int = None):
    if choice is None:
        await how_to_use(ctx, "zroll [1..6]")
    else:
        if dice_roll(choice):
            await ctx.message.add_reaction("✅")
            embed = discord.Embed(color=discord.Color.green())
            embed.set_image("https://tenor.com/bn49Q.gif")
            await ctx.reply(embed=embed)
        else:
            await ctx.message.add_reaction("❌")


@bot.command(name="agenda")
async def cmd_agenda(ctx, *, text: str = None):
    if text is None:
        await how_to_use(ctx, "zagenda [text]")
    else:
        db.add_agenda(text, ctx.author.id)
        embed_update_title(ctx, text)
        await ctx.message.add_reaction("✅")
