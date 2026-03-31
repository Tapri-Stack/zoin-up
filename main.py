import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import yaml

# env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_VC_ID = int(os.getenv("TARGET_VC_ID"))
TEXT_CH_ID = int(os.getenv("TEXT_CH_ID"))
GAMER_ROLE_ID = int(os.getenv("GAMER_ROLE_ID"))
DUMLUCK_USER_ID = int(os.getenv("DUMLUCK_USER_ID"))
ACK_EMOJI_ID = int(os.getenv("ACK_EMOJI_ID"))

# bot init
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# emojis
ACK_EMOJI_NAME = "ack"
ACK_EMOJI = f"<:{ACK_EMOJI_NAME}:{ACK_EMOJI_ID}>"


# create msg
embed_msg = f"""```
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░▀▀▀▀▀▀▀▀░░░░
░░░░░░░▀▀░░░░░░░░░░░
░░░░░░▀▀░░▀▀▀▀░░░░░░
░░░░░▀▀░░░░▀▀░░░░░░░
░░░░▀▀▀▀▀▀▀▀░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░
░░░░░░▀▀░░▀▀░░▀▀░░░░
░░░░░░░▀▀▀▀▀▀░░░░░░░
░░░░▀▀░░▀▀░░▀▀░░░░░░
░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░
░░░░░░▀▀░░▀▀░░▀▀░░░░
░░░░░░░▀▀▀▀▀▀░░░░░░░
░░░░▀▀░░▀▀░░▀▀░░░░░░
░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░
░░░░░░▀▀░░▀▀░░▀▀░░░░
░░░░░░░▀▀▀▀▀▀░░░░░░░
░░░░▀▀░░▀▀░░▀▀░░░░░░
░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░▀▀▀▀▀▀▀▀░░░░
░░░░░░░▀▀░░░░▀▀░░░░░
░░░░░░▀▀▀▀▀▀▀▀░░░░░░
░░░░░▀▀░░░░▀▀░░░░░░░
░░░░▀▀░░░░░░▀▀░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░
░░░░░░░░░░▀▀░░░░░░░░
░░░░░░░░░▀▀░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░
```"""
mention = f"<@&{GAMER_ROLE_ID}> zoin up ..., or else ... 🥀"


last_msg_id = None
session_log = ""
title = ""
color = None
attendees = set()


# get excuses
root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(root, "excuses.yml"), "r") as f:
    excuses = yaml.safe_load(f)


@bot.event
async def on_voice_state_update(member, before, after):
    global last_msg_id, session_log, title, color, attendees

    manager_display_name = member.guild.get_member(DUMLUCK_USER_ID).display_name

    text_channel = bot.get_channel(TEXT_CH_ID)
    if text_channel:

        if after.channel:
            # if activity to the same channel -> ignore mute, unmute, etc.
            if before.channel == after.channel:
                return

            # if someone joins the voice channel -> send message
            if after.channel.id == TARGET_VC_ID:

                # new session
                if len(after.channel.members) == 1:
                    other_online_members = [m.name for m in member.guild.members if m.status != discord.Status.offline and m.name != member.name]

                    if len(other_online_members) == 0:
                        title = f"EMERGENCY WAR ROOM\n(Organiser: {member.display_name})"
                        color = discord.Color.red()
                    else:
                        title = f"Standup in progress\n(Manager: {manager_display_name})"
                        color = discord.Color.green()

                    # if manager not starting the meeting
                    if member.display_name != manager_display_name:
                        session_log += f"{manager_display_name}: I'm running late, please continue."
                    else:
                        session_log += f"{manager_display_name}: (passive aggressive) Team, please join the huddle."

                    session_log += f"\n{member.display_name} joined the call."

                    embed = discord.Embed(title=title, description=embed_msg, color=color)
                    embed.set_footer(text=session_log)

                    try:
                        msg = await text_channel.send(content=mention, embed=embed)
                        await msg.add_reaction(ACK_EMOJI)
                        last_msg_id = msg.id
                    except Exception as e:
                        print(f"Error adding reaction: {e}")

                # existing session
                elif last_msg_id:
                    # if new member joining
                    if member not in attendees:
                        session_log += f"\n{member.display_name} joined the call."
                        await update_log_embed(text_channel, title, embed_msg, color, session_log)

                attendees.add(member)

        # someone leaves
        elif before.channel and before.channel.id == TARGET_VC_ID:
            if last_msg_id:
                excuse = random.choice(excuses)
                session_log += f"\n{member.display_name} had to step out due to {excuse}."
                await update_log_embed(text_channel, title, embed_msg, color, session_log)

                # if the channel is empty
                if len(before.channel.members) == 0:
                    session_log += f"\n{manager_display_name}: MOM to be prepared by {random.choice(attendees)}."
                    await update_log_embed(text_channel, title, embed_msg, discord.Color.light_grey(), session_log)

                    # Reset globals for the next session
                    last_msg_id = None
                    session_log = ""
                    title = ""
                    color = None
                    attendees = set()


async def update_log_embed(channel, title, description, color, footer):
    global last_msg_id, session_log
    try:
        msg = await channel.fetch_message(last_msg_id)

        new_embed = discord.Embed(title=title, description=description, color=color)
        new_embed.set_footer(text=footer)
        await msg.edit(embed=new_embed)
    except Exception as e:
        print(f"Failed to update log: {e}")


@bot.event
async def on_raw_reaction_add(payload):
    if not last_msg_id or last_msg_id != payload.message_id or payload.user_id == bot.user.id:
        return

    # if react with emoji, send invite
    if payload.emoji.name == ACK_EMOJI_NAME:
        channel = bot.get_channel(payload.channel_id)
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        vc_channel = bot.get_channel(TARGET_VC_ID)

        if vc_channel and member:
            invite = await vc_channel.create_invite(max_age=60, max_uses=1)
            portal_msg = await channel.send(f"{member.mention}, here is your invite link: {invite.url}")
            await asyncio.sleep(10)
            try:
                await portal_msg.delete()
            except:
                pass


bot.run(TOKEN)
