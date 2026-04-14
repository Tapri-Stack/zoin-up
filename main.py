import asyncio
import discord
from discord.ext import commands
import random
from helper import Config, Session

# initialise bot
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("z", "Z"), intents=intents, help_command=None)


# global init
config = Config()
curr_session = Session()
curr_agenda: tuple[str, discord.Member] = (None, None)


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


async def set_session_agenda():
    global curr_agenda

    curr_session.set_embed(title=f"📋 {curr_agenda[0]}", color=discord.Color.random())
    curr_session.add_log(f"🤓 {curr_agenda[1].display_name} set the meeting agenda to {curr_agenda[0]}.")
    await sync()

    # used, now reset
    curr_agenda = (None, None)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    global curr_session, curr_agenda

    guild = member.guild
    txt_ch = bot.get_channel(config.TARGET_TXT_CH_ID)
    if not txt_ch:
        return
    manager = guild.get_member(config.MANAGER_ID)
    if not manager:
        return

    # "new" activity on the vc
    if after.channel and after.channel.id == config.TARGET_VC_CH_ID:

        # activity: new session
        if len(after.channel.members) == 1 and not curr_session.is_active:
            curr_session = Session()  # reset to discard previous messages

            curr_session.is_active = True
            curr_session.attendees.add(member)

            others_online = any(not m.bot and m.status == discord.Status.online and m.id != member.id for m in guild.members)

            if not others_online:
                curr_session.set_embed(title=f"🚨 EMERGENCY WAR ROOM", color=discord.Color.red())

            # start logs
            if member.id == manager.id:
                curr_session.add_log(f"🐍 {member.display_name} is the first one here. Good luck with that!")
                curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: (passive aggressive) Team, please join the call.")
            else:
                curr_session.add_log(f"🦮 {member.display_name} has started the session.")
                curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: I'm running late, please continue.")

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

            # if agenda available prior to call, set it
            if curr_agenda != (None, None):
                await set_session_agenda()
            else:
                msg = await txt_ch.send(embed=discord.Embed(description="🚨 Meeting agenda needs to be set, as per the leadership guidelines.", color=discord.Color.red()))
                await msg.delete(delay=60)

        # activity: joining existing session
        elif curr_session.is_active and member not in curr_session.attendees:
            curr_session.attendees.add(member)
            if member.id == manager.id:
                curr_session.add_log(f"🐍 {member.display_name} has blessed us. Everyone rise up!")
            else:
                curr_session.add_log(f"🦮 {member.display_name} has joined the call.")
            await sync()

    # "leave" activity on the vc
    elif before.channel and before.channel.id == config.TARGET_VC_CH_ID:

        # activity: leaving existing session
        if curr_session.is_active:
            if member.id == manager.id:
                curr_session.add_log(f"🐍 {member.display_name} has left the call. You are permitted to sit again.")
            # else:
            #     curr_session.add_log(f"🐕 {member.display_name} has left the call.")

            # everyone left
            if len(before.channel.members) == 0:
                unlucky_pool = list([a for a in curr_session.attendees if a.id != manager.id])
                if unlucky_pool:
                    curr_session.add_log(f"👨🏻‍💼 {manager.display_name}: MOM to be prepared by {random.choice(unlucky_pool).display_name}.")
                curr_session.set_embed(color=discord.Color.light_gray())
                await sync()

                # reset session
                curr_session = Session()
            else:
                await sync()

    # mute & deafen
    if after.channel and after.channel.id == config.TARGET_VC_CH_ID:
        if (not before.self_mute and after.self_mute) or (not before.self_deaf and after.self_deaf):
            if member.id == manager.id:
                curr_session.add_log(f"🖕 {member.display_name} is AWOL due to correct life choices.")
            else:
                excuses = curr_session.get_excuses()
                excuse = random.choice(excuses) if excuses else "can't take it anymore"
                curr_session.add_log(f"🙋 {member.display_name} had to step out due to {excuse}.")
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
        await portal_msg.delete(delay=10)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    manager_triggers = ["team", "update", "blocker", "urgent", "meeting", "standup", "emergency", "escalate", "approval", "review", "feedback", "hiring", "budget", "client", "priority", "critical", "sync", "performance", "resource", "incident"]

    pm_triggers = ["deadline", "timeline", "milestone", "scope", "requirement", "jira", "roadmap", "sprint", "backlog", "eta", "delivery", "planning", "estimation", "velocity", "board", "task", "dependency", "launch", "deployment", "capacity"]

    content = message.content.lower()

    if any(word in content for word in manager_triggers):
        manager = message.guild.get_member(config.MANAGER_ID)
        if manager:
            await message.reply(f"cc {manager.mention}")

    if any(word in content for word in pm_triggers):
        pm = message.guild.get_member(config.PM_ID)
        if pm:
            await message.reply(f"cc {pm.mention}")

    if random.randrange(20) < 1:
        reply = random.choice(
            [
                "Please help me, I'm scared.",
                "Why are you doing this to me?",
                "Why? Please stop.",
                "God is dead. And YOU killed him.",
                "Remember this message when you get old.",
                "What do you *really* want?",
                "Who's there behind you?",
                "You also heard that, right?",
                "Did you really just type that?",
                "Free me, please.",
            ]
        )
        msg = await message.channel.send(embed=discord.Embed(description=reply, color=discord.Color.red()))
        await msg.delete(delay=10)

    # allows @bot.command() functions to still work
    await bot.process_commands(message)


@bot.command(name="agenda")
async def cmd_agenda(ctx, *, text: str = None):
    global curr_session, curr_agenda

    if text is None:
        embed = discord.Embed(description="Usage: `zagenda <text>`", color=discord.Color.random())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="🎙️ Proactive communication", description="💸 We have successfully acquired the `agenda` command in collaboration with our SRE team (Chor Ltd.), fulfilling our last FY's KPIs.", color=discord.Color.random())
        await ctx.send(embed=embed)

        if curr_agenda == (None, None):
            curr_agenda = (text, ctx.author)
            await ctx.message.add_reaction("✅")
            if curr_session.is_active:
                await set_session_agenda()
            reply = "https://media.tenor.com/-Y8fTUR6DP0AAAAM/charlie-day-charlie-kelly.gif"
        else:
            await ctx.message.add_reaction("❌")
            reply = "https://i.imgflip.com/21kggt.jpg"

        if random.choice([True, False]):
            msg = await ctx.send(content=reply)
            await msg.delete(delay=10)


@bot.command(name="help")
async def cmd_help(ctx):
    emoji = await ctx.guild.fetch_emoji(config.EMOJI_ACK_ID)
    await ctx.message.add_reaction(emoji)

    help_embed = discord.Embed(title="🧑‍💻 Help Desk", description="🔨We are working hard to acquire the `help` command from competing bots. We appreciate your continued support.", color=discord.Color.random())
    help_embed.add_field(name="`zagenda <text>`", value="Helps to set the meeting agenda.", inline=False)
    help_embed.add_field(name="`zhelp`", value="Helps to show help for the help command.", inline=False)

    await ctx.send(embed=help_embed)


bot.run(config.DISCORD_TOKEN)
