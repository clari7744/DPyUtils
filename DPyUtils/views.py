from typing import Union

from discord import ButtonStyle, Interaction, Member, User, ui

from . import Context


class Confirmation(ui.View):
    """
    An easy drop-in confirmation dialog for your commands.

    Parameters
    ----------
    ctx : Union[Context, Interaction]
        The context or interaction to get the user from
    cancel_message : str = "Cancelled"
        The message to send when the user cancels
    ephemeral : bool = False
        Whether to send the cancel message in an ephemeral message

    Examples
    --------

    .. code-block:: python3

    async def confirm(ctx):
        confirm = Confirmation(ctx)
        await ctx.send("Are you sure?", view=confirm)
        if await confirm.run():
            await ctx.send("Do the thing here")

    """

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
    async def confirm(self, interaction: Interaction, button: ui.Button) -> None:
        await interaction.response.defer()
        self.resp = True
        self.stop()

    @ui.button(emoji="❌", label="Cancel", style=ButtonStyle(4))
    async def cancel(self, interaction: Interaction, button: ui.Button) -> None:
        await interaction.send(self.cancel_message, ephemeral=self.ephemeral)
        self.resp = False
        self.stop()
