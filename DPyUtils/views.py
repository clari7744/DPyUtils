from typing import Union

from discord import Button, ButtonStyle, Interaction, Member, User, ui

from . import Context


class Confirmation(ui.View):
    def __init__(self, ctx: Union[Context, Interaction], *args, cancel_message="Cancelled", ephemeral=False, **kwargs):
        self.user: Union[Member, User] = ctx.user if isinstance(ctx, Interaction) else ctx.author
        self.resp: bool = False
        self.ephemeral: bool = ephemeral
        self.cancel_message: str = cancel_message

        super().__init__(*args, **kwargs)

    async def run(self) -> bool:
        await self.wait()
        return self.resp

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.user.id

    @ui.button(emoji="✅", label="Confirm", style=ButtonStyle(3))
    async def confirm(self, interaction: Interaction, button: Button) -> None:
        await interaction.response.defer()
        self.resp = True
        self.stop()

    @ui.button(emoji="❌", label="Cancel", style=ButtonStyle(4))
    async def cancel(self, interaction: Interaction, button: Button) -> None:
        await interaction.send(self.cancel_message, ephemeral=self.ephemeral)
        self.resp = False
        self.stop()
