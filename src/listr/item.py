from __future__ import annotations

from asyncio import gather
from datetime import datetime
from typing import Optional

from discord import Colour, Embed, Message
from discord.abc import Messageable
from pydantic import BaseModel, field_validator

from listr.buttons import Buttons
from listr.errors import NotAnItem


class Item(BaseModel):
    message: Message

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def is_item(message: Message) -> bool:
        return len(message.embeds) > 0

    @field_validator("message")
    @classmethod
    def check_message_is_item(cls, message: Message) -> Message:
        if not cls.is_item(message):
            raise NotAnItem(message.id)

        return message

    @classmethod
    async def from_parts(
        cls,
        channel: Messageable,
        content: str,
        icon_url: Optional[str],
        timestamp: datetime,
        colour: Colour,
        done_label: str,
        delete_label: str,
    ) -> Item:
        return cls(
            message=await channel.send(
                embed=Embed(
                    colour=colour,
                    timestamp=timestamp,
                ).set_author(
                    name=content,
                    icon_url=icon_url,
                ),
                view=Buttons(done_label, delete_label),
            )
        )

    @classmethod
    async def from_message(
        cls,
        message: Message,
        colour: Colour,
        done_label: str,
        delete_label: str,
        delete_message: bool,
    ) -> Item:
        content: Optional[str] = None
        icon_url: Optional[str] = None
        timestamp: Optional[datetime] = None

        if cls.is_item(message):
            content = message.embeds[0].author.name
            icon_url = message.embeds[0].author.icon_url
            timestamp = message.embeds[0].timestamp

        content = content or message.content
        icon_url = (
            icon_url or message.author.avatar.url if message.author.avatar else None
        )
        timestamp = timestamp or message.created_at

        results = await gather(
            cls.from_parts(
                channel=message.channel,
                content=content,
                icon_url=icon_url,
                timestamp=timestamp,
                colour=colour,
                done_label=done_label,
                delete_label=delete_label,
            ),
            *([message.delete()] if delete_message else []),
        )
        return results[0]

    def get_embed(self) -> Embed:
        return self.message.embeds[0]

    async def set_embed(self, embed: Embed) -> Item:
        return Item(message=await self.message.edit(embed=embed))

    def get_content(self, clean: bool = False) -> str:
        content = self.get_embed().author.name or ""
        return content.strip().lower() if clean else content

    async def set_content(self, content: str) -> Item:
        embed = self.get_embed()
        embed.set_author(
            name=content,
            icon_url=embed.author.icon_url,
        )
        return await self.set_embed(embed)

    def get_colour(self) -> Optional[Colour]:
        return self.get_embed().colour

    async def set_colour(self, colour: Optional[Colour]) -> Item:
        embed = self.get_embed()
        embed.colour = colour
        return await self.set_embed(embed)

    async def toggle_colour(self, colour: Optional[Colour]) -> Item:
        return await self.set_colour(colour if self.get_colour() is None else None)

    def get_timestamp(self) -> datetime:
        return self.get_embed().timestamp or self.message.created_at

    async def set_timestamp(self, timestamp: datetime) -> Item:
        embed = self.get_embed()
        embed.timestamp = timestamp
        return await self.set_embed(embed)

    async def delete_duplicates(self) -> None:
        async for message in self.message.channel.history(
            limit=None,
            oldest_first=True,
        ):
            if (
                message.id != self.message.id
                and self.is_item(message)
                and self.get_content(clean=True)
                == Item(message=message).get_content(clean=True)
            ):
                await message.delete()
