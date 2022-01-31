import discord
from . import Context


class Confirmation(discord.ui.View):
    def __init__(self, ctx: Context, *args, **kwargs):
        self.ctx = ctx
        super().__init__(*args, **kwargs)

    resp: bool = False

    async def run(self):
        await self.wait()
        return self.resp

    async def interaction_check(
        self, item: discord.ui.Item, interaction: discord.Interaction
    ):
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(emoji="✅", label="Confirm", style=discord.ButtonStyle(3))
    async def confirm(self, button: discord.Button, interaction: discord.Interaction):
        self.resp = True
        self.stop()

    @discord.ui.button(emoji="❌", label="Cancel", style=discord.ButtonStyle(4))
    async def cancel(self, button: discord.Button, interaction: discord.Interaction):
        self.resp = False
        self.stop()
