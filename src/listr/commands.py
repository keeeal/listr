from __future__ import annotations

from asyncio import gather
from enum import Enum, auto
from typing import TYPE_CHECKING

from discord import Interaction
from discord.abc import Messageable
from discord.app_commands import command, describe
from discord.ext.commands import Cog

from listr.errors import NotMessageable
from listr.item import Item

if TYPE_CHECKING:
    from listr.bot import Listr


class SortBy(Enum):
    alphabetically = auto()
    newest_first = auto()


class Commands(Cog):
    def __init__(self, bot: Listr):
        self.bot = bot

    @command(name="list", description="Itemize all messages in this channel")
    async def list(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(interaction.channel, Messageable):
            raise NotMessageable(interaction.channel_id)

        async for message in interaction.channel.history(limit=None, oldest_first=True):
            if message.author == self.bot.user:
                continue
            if Item.is_item(message):
                continue

            await Item.from_message(
                message=message,
                colour=self.bot.colour,
                done_label=self.bot.done_label,
                delete_label=self.bot.delete_label,
                delete_message=True,
            )

        await interaction.delete_original_response()

    @command(name="sort", description="Sort all items in this channel")
    @describe(by="The way to sort the messages")
    async def sort(self, interaction: Interaction, by: SortBy):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(interaction.channel, Messageable):
            raise NotMessageable(interaction.channel_id)

        if by == SortBy.alphabetically:
            key = lambda message: Item(message=message).get_content(clean=True)
        elif by == SortBy.newest_first:
            key = lambda message: Item(message=message).get_timestamp()

        for message in sorted(
            [
                message
                async for message in interaction.channel.history(
                    limit=None, oldest_first=True
                )
                if Item.is_item(message)
            ],
            key=key,
        ):
            await Item.from_message(
                message=message,
                colour=self.bot.colour,
                done_label=self.bot.done_label,
                delete_label=self.bot.delete_label,
                delete_message=True,
            )

        await interaction.delete_original_response()

    @command(name="clear", description="Clear checked items in this channel")
    async def clear(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not isinstance(interaction.channel, Messageable):
            raise NotMessageable(interaction.channel_id)

        async for message in interaction.channel.history(limit=None):
            if message.author != self.bot.user:
                continue
            if not Item.is_item(message):
                continue
            if Item(message=message).get_colour() is not None:
                continue

            await message.delete()

        await interaction.delete_original_response()

    @command(name="undo", description="Undo the last deletion in this channel")
    async def undo(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if interaction.channel_id is None or not isinstance(
            interaction.channel, Messageable
        ):
            raise NotMessageable(interaction.channel_id)

        if len(self.bot.history.get(interaction.channel_id, [])) == 0:
            await interaction.followup.send("Nothing to undo 🤷", ephemeral=True)
        else:
            await gather(
                Item.from_message(
                    message=self.bot.history[interaction.channel_id].pop().message,
                    colour=self.bot.colour,
                    done_label=self.bot.done_label,
                    delete_label=self.bot.delete_label,
                    delete_message=False,
                ),
                interaction.delete_original_response(),
            )
