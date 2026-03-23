import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_VC_ID = int(os.getenv("TARGET_VC_ID"))
TEXT_CH_ID = int(os.getenv("TEXT_CH_ID"))
GAMER_ROLE_ID = int(os.getenv("GAMER_ROLE_ID"))

# bot init
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# emojis
NICE_YUDI_EMOJI = "<:niceyudi:1468916522033352746>"
NICE_YUDI_EMOJI_NAME = "niceyudi"


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
mention = f"<@&{GAMER_ROLE_ID}>"


last_msg_id = None  # store msg id


@bot.event
async def on_voice_state_update(member, before, after):
    global last_msg_id
    if after.channel and after.channel.id == TARGET_VC_ID:
        if len(after.channel.members) == 1:
            text_channel = bot.get_channel(TEXT_CH_ID)
            if text_channel:
                embed = discord.Embed(description=embed_msg, color=discord.Color.green())
                embed.set_footer(text=f"{member.display_name} has started the session.")

                msg = await text_channel.send(content=mention, embed=embed)
                try:
                    await msg.add_reaction(NICE_YUDI_EMOJI)
                except Exception as e:
                    print(f"Error adding reaction: {e}")

                last_msg_id = msg.id


@bot.event
async def on_raw_reaction_add(payload):
    if not last_msg_id or last_msg_id != payload.message_id or payload.user_id == bot.user.id:
        return

    # if react with emoji, send invite
    if payload.emoji.name == NICE_YUDI_EMOJI_NAME:
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
