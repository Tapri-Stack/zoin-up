import asyncio
import os
import discord
from discord.ext import commands
import random
import yaml
from helper import Config, Session

# initialise bot
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# global init
config = Config()
curr_session = Session()


async def sync():
    if not curr_session.msg_id:
        return

    txt_ch = bot.get_channel(config.TARGET_TXT_CH_ID)
    if not txt_ch:
        return

    try:
        msg = await txt_ch.fetch_message(curr_session.msg_id)
        await msg.edit(embed=curr_session.embed)
    except Exception as e:
        print(f"Failed to sync: {e}")


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    global curr_session

    guild = member.guild
    txt_ch = bot.get_channel(config.TARGET_TXT_CH_ID)
    if not txt_ch:
        return
    manager = guild.get_member(config.USER_DUMLUCK_ID)
    if not manager:
        return

    # "new" activity on the vc
    if after.channel and after.channel.id == config.TARGET_VC_CH_ID:

        # activity: new session
        if len(after.channel.members) == 1 and not curr_session.is_active:
            curr_session.is_active = True
            curr_session.attendees.add(member)

            others_online = any(not m.bot and m.status == discord.Status.online and m.id != member.id for m in guild.members)

            if not others_online:
                curr_session.set_embed(title=f"🚨 *EMERGENCY WAR ROOM*", color=discord.Color.red())

            # start logs
            if member.id == manager.id:
                curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: (passive aggressive) Team, please join the call.")
            else:
                curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: I'm running late, please continue.")
            curr_session.add_log(f"🦮 {member.display_name} has started the session.")

            # Send initial message
            role = guild.get_role(config.ROLE_GAMER_ID)
            mention = role.mention if role else "@everyone"

            try:
                msg = await txt_ch.send(content=f"{mention} {curr_session._MESSAGE}", embed=curr_session.embed)
                # Use custom emoji if available, fallback to checkmark
                try:
                    emoji = await guild.fetch_emoji(config.EMOJI_ACK_ID)
                    await msg.add_reaction(emoji)
                except:
                    await msg.add_reaction("✅")

                curr_session.msg_id = msg.id
            except Exception as e:
                print(f"Failed to send initial session message: {e}")

        # activity: joining existing session
        elif curr_session.is_active and member not in curr_session.attendees:
            curr_session.attendees.add(member)
            curr_session.add_log(f"🦮 {member.display_name} has joined the call.")
            await sync()

    # "leave" activity on the vc
    elif before.channel and before.channel.id == config.TARGET_VC_CH_ID:

        # activity: leaving existing session
        if curr_session.is_active:
            curr_session.add_log(f"🐕 {member.display_name} has left the call.")

            # everyone left
            if len(before.channel.members) == 0:
                curr_session.set_embed(color=discord.Color.light_gray())
                curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: 📋 MOM to be prepared by {random.choice(list(curr_session.attendees)).display_name}.")
                await sync()

                curr_session = Session()  # reset session
            else:
                await sync()

    # mute & deafen
    if after.channel and after.channel.id == config.TARGET_VC_CH_ID:
        if (not before.self_mute and after.self_mute) or (not before.self_deaf and after.self_deaf):
            # get excuses from file
            root = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(root, "excuses.yml"), "r") as f:
                excuses = yaml.safe_load(f)

            curr_session.add_log(f"🤓☝️ {member.display_name} had to step out due to {random.choice(excuses)}.")
            await sync()


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    global curr_session

    if not curr_session.is_active or curr_session.msg_id != payload.message_id or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    txt_ch = bot.get_channel(config.TARGET_TXT_CH_ID)
    if not txt_ch:
        return
    vc_ch = bot.get_channel(config.TARGET_VC_CH_ID)
    if not vc_ch:
        return

    if payload.emoji.id == config.EMOJI_ACK_ID:
        invite = await vc_ch.create_invite(max_age=60, max_uses=1)
        portal_msg = await txt_ch.send(f"⏳ {member.mention}, here is your session invite: {invite.url}")
        await asyncio.sleep(10)
        await portal_msg.delete()


bot.run(config.DISCORD_TOKEN)
