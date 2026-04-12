import os
import discord
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import List, Set, Optional
import requests
import yaml

load_dotenv()


@dataclass(frozen=True)
class Config:
    DISCORD_TOKEN: str = field(default_factory=lambda: os.getenv("DISCORD_TOKEN"))
    TARGET_VC_CH_ID: int = field(default_factory=lambda: int(os.getenv("TARGET_VC_CH_ID")))
    TARGET_TXT_CH_ID: int = field(default_factory=lambda: int(os.getenv("TARGET_TXT_CH_ID")))
    ROLE_GAMER_ID: int = field(default_factory=lambda: int(os.getenv("ROLE_GAMER_ID")))
    MANAGER_ID: int = field(default_factory=lambda: int(os.getenv("MANAGER_ID")))
    PM_ID: int = field(default_factory=lambda: int(os.getenv("PM_ID")))
    EMOJI_ACK_ID: int = field(default_factory=lambda: int(os.getenv("EMOJI_ACK_ID")))
    URL_EXCUSES_YML: str = field(default_factory=lambda: os.getenv("URL_EXCUSES_YML"))

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
        if not self.PM_ID:
            raise EnvironmentError("Environment variable not set:", self.PM_ID)
        if not self.EMOJI_ACK_ID:
            raise EnvironmentError("Environment variable not set:", self.EMOJI_ACK_ID)
        if not self.URL_EXCUSES_YML:
            raise EnvironmentError("Environment variable not set:", self.URL_EXCUSES_YML)


@dataclass
class Session:
    _MESSAGE: str = "zoin up ..., or else ... 🥀"
    _EMBED_TITLE: str = "🗣️ Standup in session"
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
    _EMBED_COLOR: discord.Color = field(default_factory=lambda: discord.Color.random())

    msg_id: Optional[int] = None
    log: str = ""
    attendees: Set[discord.Member] = field(default_factory=set)
    is_active: bool = False
    embed: Optional[discord.Embed] = None
    _excuses: List[str] = field(default_factory=list)

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

    def get_excuses(self) -> List[str]:
        config = Config()

        try:
            response = requests.get(config.URL_EXCUSES_YML, allow_redirects=True)
            response.raise_for_status()
            data = yaml.safe_load(response.content)
            self._excuses = data
            return data
        except Exception as e:
            print("Failed to fetch excuses:", e)
            if self._excuses:
                print("Returning cached excuses.")
                return self._excuses

        return []
