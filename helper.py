import os
import discord
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import Set, Optional

load_dotenv()


@dataclass(frozen=True)
class Config:
    DISCORD_TOKEN: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN"))
    TARGET_VC_CH_ID: int = field(default_factory=lambda: int(os.getenv("TARGET_VC_CH_ID")))
    TARGET_TXT_CH_ID: int = field(default_factory=lambda: int(os.getenv("TARGET_TXT_CH_ID")))
    ROLE_GAMER_ID: int = field(default_factory=lambda: int(os.getenv("ROLE_GAMER_ID")))
    MANAGER_ID: int = field(default_factory=lambda: int(os.getenv("MANAGER_ID")))
    EMOJI_ACK_ID: int = field(default_factory=lambda: int(os.getenv("EMOJI_ACK_ID")))

    def __post_init__(self):
        if not self.DISCORD_TOKEN:
            raise EnvironmentError("Environment variable not set:", self.DISCORD_TOKEN)
        if not self.TARGET_VC_CH_ID:
            raise EnvironmentError("Environment variable not set:", self.TARGET_VC_CH_ID)
        if not self.TARGET_TXT_CH_ID:
            raise EnvironmentError("Environment variable not set:", self.TARGET_TXT_CH_ID)
        if not self.ROLE_GAMER_ID:
            raise EnvironmentError("Environment variable not set:", self.ROLE_GAMER_ID)
        if not self.MANAGER_ID:
            raise EnvironmentError("Environment variable not set:", self.MANAGER_ID)
        if not self.EMOJI_ACK_ID:
            raise EnvironmentError("Environment variable not set:", self.EMOJI_ACK_ID)


@dataclass
class Session:
    _MESSAGE: str = "*zoin up ..., or else ...* 🥀"
    _EMBED_TITLE: str = "🗣️ *Standup in session*"
    _EMBED_DESCRIPTION: str = """```
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░▀▀▀▀▀▀▀▀░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░░░░░░░░░
░░░░░░░░░░▀▀░░▀▀▀▀░░░░░░░░░░
░░░░░░░░░▀▀░░░░▀▀░░░░░░░░░░░
░░░░░░░░▀▀▀▀▀▀▀▀░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░
░░░░░░░░░░░▀▀▀▀▀▀░░░░░░░░░░░
░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░
░░░░░░░░░░░▀▀▀▀▀▀░░░░░░░░░░░
░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░
░░░░░░░░░░░▀▀▀▀▀▀░░░░░░░░░░░
░░░░░░░░▀▀░░▀▀░░▀▀░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░▀▀▀▀▀▀▀▀░░░░░░░░
░░░░░░░░░░░▀▀░░░░▀▀░░░░░░░░░
░░░░░░░░░░▀▀▀▀▀▀▀▀░░░░░░░░░░
░░░░░░░░░▀▀░░░░▀▀░░░░░░░░░░░
░░░░░░░░▀▀░░░░░░▀▀░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░▀▀░░░░░░░░░░░
░░░░░░░░░░░░░░▀▀░░░░░░░░░░░░
░░░░░░░░░░░░░▀▀░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░▀▀░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```"""
    _EMBED_COLOR: discord.Color = field(default_factory=lambda: discord.Color.green())

    msg_id: Optional[int] = None
    log: str = ""
    attendees: Set[discord.Member] = field(default_factory=set)
    is_active: bool = False
    embed: Optional[discord.Embed] = None

    def __post_init__(self):
        if self.embed is None:
            self.set_embed()

    def set_embed(self, title=None, description=None, color=None):
        self.embed = discord.Embed(title=title or self._EMBED_TITLE, description=description or self._EMBED_DESCRIPTION, color=color or self._EMBED_COLOR)
        if self.log:
            self.embed.set_footer(text=self.log)

    def add_log(self, msg: str):
        self.log += f"\n{msg}"
        if self.embed:
            self.embed.set_footer(text=self.log)
