from typing import Union

import discord

from . import Context


class Confirmation(discord.ui.View):
    def __init__(
        self, ctx: Union[Context, discord.Interaction], *args, cancel_message="Cancelled", ephemeral=False, **kwargs
    ):
        self.user: Union[discord.Member, discord.User] = ctx.author if isinstance(ctx, Context) else ctx.user
        self.resp: bool = False
        self.ephemeral: bool = ephemeral
        self.cancel_message: str = cancel_message

        super().__init__(*args, **kwargs)

    async def run(self) -> bool:
        await self.wait()
        return self.resp

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    @discord.ui.button(emoji="✅", label="Confirm", style=discord.ButtonStyle(3))
    async def confirm(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.response.defer()
        self.resp = True
        self.stop()

    @discord.ui.button(emoji="❌", label="Cancel", style=discord.ButtonStyle(4))
    async def cancel(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.send(self.cancel_message, ephemeral=self.ephemeral)
        self.resp = False
        self.stop()
