from __future__ import annotations

from asyncio import gather

from discord import Colour, Intents, Interaction, Message
from discord.ext.commands import Bot

from listr.buttons import Action
from listr.commands import Commands
from listr.item import Item
from listr.utils.logging import get_logger

logger = get_logger(__name__)


class Listr(Bot):
    def __init__(
        self,
        command_prefix: str,
        bot_colour: int,
        done_label: str,
        delete_label: str,
    ) -> None:
        intents = Intents.default()
        intents.message_content = True
        super().__init__(command_prefix, intents=intents)

        self.colour = Colour(bot_colour)
        self.done_label = done_label
        self.delete_label = delete_label
        self.history: dict[int, list[Item]] = {}

    async def on_ready(self) -> None:
        await self.add_cog(Commands(bot=self))
        await self.tree.sync()

        logger.info(f"Logged in as {self.user}")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return

        await (
            await Item.from_message(
                message=message,
                colour=self.colour,
                done_label=self.done_label,
                delete_label=self.delete_label,
                delete_message=True,
            )
        ).delete_duplicates()

    async def on_interaction(self, interaction: Interaction) -> None:
        if (
            not interaction.data
            or not interaction.message
            or not interaction.channel_id
        ):
            return
        if not isinstance(custom_id := interaction.data.get("custom_id"), str):
            return

        action = Action(custom_id)

        if action == Action.DONE:
            await gather(
                Item(message=interaction.message).toggle_colour(self.colour),
                interaction.response.defer(),
            )
        elif action == Action.DELETE:
            if interaction.channel_id not in self.history:
                self.history[interaction.channel_id] = []
            self.history[interaction.channel_id].append(
                Item(message=interaction.message)
            )
            await interaction.message.delete()
