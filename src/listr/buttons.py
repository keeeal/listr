from enum import StrEnum

from discord import ButtonStyle
from discord.ui import Button, View


class Action(StrEnum):
    DONE = "done"
    DELETE = "delete"


class Buttons(View):
    def __init__(self, done_label: str, delete_label: str) -> None:
        super().__init__(timeout=None)
        self.add_item(
            Button(
                label=done_label, custom_id=Action.DONE.value, style=ButtonStyle.grey
            )
        )
        self.add_item(
            Button(
                label=delete_label,
                custom_id=Action.DELETE.value,
                style=ButtonStyle.grey,
            )
        )
