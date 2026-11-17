import discord


class VC:
    def __init__(self, vc_id: int):
        self.vc_id = vc_id

    def is_valid_channel(self, voice_state: discord.VoiceState):
        return voice_state.channel is not None and voice_state.channel.id == self.vc_id

    def is_member_count_changed(self, state: discord.VoiceState, before: discord.VoiceState, after: discord.VoiceState):
        if self.is_valid_channel(state) and before.channel != after.channel:
            return len(state.channel.members)

    def is_member_count_same(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_valid_channel(before) and before.channel == after.channel

    def is_new_call(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_changed(after, before, after) == 1

    def is_joining(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_changed(after, before, after) > 1

    def is_leaving(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_changed(before, before, after) > 0

    def is_end_call(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_changed(after, before, after) == 0

    def is_mute(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_same(before, after) and (not before.self_mute and after.self_mute)

    def is_deafen(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_same(before, after) and (not before.self_deaf and after.self_deaf)

    def is_unmute(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_same(before, after) and (before.self_mute and not after.self_mute)

    def is_undeafen(self, before: discord.VoiceState, after: discord.VoiceState):
        return self.is_member_count_same(before, after) and (before.self_deaf and not after.self_deaf)


class SessionMsg:
    def __init__(self, msg_id: int, channel: discord.VoiceState):
        self.msg_id = msg_id
        self.channel = channel

    def get_msg(self):
        return self.channel.fetch_message(self.msg_id)

    def get_embed(self):
        msg = self.get_msg()
        if msg.embeds:
            return msg.embeds[0]

    async def update_log(self, log: str):
        embed = self.get_embed()
        embed.set_footer(embed.footer.text + f"\n{log}")
        await msg.edit(embed=embed)

    async def update_title(self, title: str):
        embed = self.get_embed()
        embed.title = title
        await msg.edit(embed=embed)

    async def update_img(self, img_url: str):
        embed = self.get_embed()
        embed.set_image(url=img_url)
        embed.set_thumbnail(url=img_url)
        await msg.edit(embed=embed)
