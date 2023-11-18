from discord import Embed, Message


def has_embed_content(message: Message) -> bool:
    return bool(message.embeds and message.embeds[0].description)


def get_content(message: Message) -> str:
    if message.embeds and message.embeds[0].description:
        return message.embeds[0].description
    else:
        return message.content


async def set_content(message: Message, content: str) -> None:
    if message.embeds and message.embeds[0].description:
        await message.edit(embed=Embed(description=content))
    else:
        await message.edit(content=content)


def is_strike(message: Message) -> bool:
    content = get_content(message)
    return content.startswith("~~") and content.endswith("~~")


async def set_strike(message: Message, strike: bool) -> None:
    content = get_content(message)

    if strike and not is_strike(message):
        await set_content(message, f"~~{content}~~")
    elif not strike and is_strike(message):
        await set_content(message, content.strip("~"))


def count_emoji(message: Message, emoji: str) -> int:
    for reaction in message.reactions:
        if isinstance(reaction.emoji, str):
            if reaction.emoji == emoji:
                return reaction.count
        elif reaction.emoji.name == emoji:
            return reaction.count
    else:
        return 0
