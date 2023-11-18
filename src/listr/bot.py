from __future__ import annotations

from discord import (
    Embed,
    Intents,
    Interaction,
    Message,
    MessageType,
    RawReactionActionEvent,
)
from discord.abc import Messageable
from discord.app_commands import command
from discord.ext.commands import Bot, Cog

from .utils.logging import get_logger
from .utils.message import count_emoji, get_content, has_embed_content, set_strike

logger = get_logger(__name__)


class NotMessageable(Exception):
    pass


class Commands(Cog):
    def __init__(self, bot: Listr):
        self.bot = bot

    @command(name="list", description="Itemize all messages in this channel")
    async def list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(interaction.channel, Messageable):
            raise NotMessageable(interaction.channel_id)

        async for message in interaction.channel.history(limit=None, oldest_first=True):
            if message.type != MessageType.reply:
                await self.bot.embed_message(message, delete_original=True)

        await interaction.delete_original_response()


class Listr(Bot):
    def __init__(
        self,
        command_prefix: str,
        strike_emoji: str,
        delete_emoji: str,
    ):
        intents = Intents.default()
        intents.message_content = True
        super().__init__(command_prefix, intents=intents)

        self.strike_emoji = strike_emoji
        self.delete_emoji = delete_emoji

    async def fetch_message(self, channel_id: int, message_id: int) -> Message:
        channel = self.get_channel(channel_id)

        if not isinstance(channel, Messageable):
            raise NotMessageable(channel_id)

        return await channel.fetch_message(message_id)

    async def embed_message(
        self, message: Message, delete_original: bool = False
    ) -> None:

        await message.channel.send(embed=Embed(description=get_content(message)))

        if delete_original:
            await message.delete()

    async def on_ready(self) -> None:
        await self.add_cog(Commands(self))
        await self.tree.sync()

        logger.info(f"Logged in as {self.user}")

    async def on_message(self, message: Message):
        if message.author == self.user:
            if has_embed_content(message):
                await message.add_reaction(self.strike_emoji)
                await message.add_reaction(self.delete_emoji)
        elif message.type != MessageType.reply:
            await self.embed_message(message, delete_original=True)

    async def on_raw_reaction_add(self, event: RawReactionActionEvent):
        if event.emoji.name == self.strike_emoji:
            message = await self.fetch_message(event.channel_id, event.message_id)
            if not has_embed_content(message):
                return

            count = count_emoji(message, self.strike_emoji)
            await set_strike(message, count % 2 == 0)

        elif event.emoji.name == self.delete_emoji:
            message = await self.fetch_message(event.channel_id, event.message_id)
            if not has_embed_content(message):
                return

            if count_emoji(message, self.delete_emoji) > 1:
                await message.delete()

    async def on_raw_reaction_remove(self, event: RawReactionActionEvent):
        if event.emoji.name == self.strike_emoji:
            message = await self.fetch_message(event.channel_id, event.message_id)
            count = count_emoji(message, self.strike_emoji)
            await set_strike(message, count % 2 == 0)
