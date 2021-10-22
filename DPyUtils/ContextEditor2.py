import discord, traceback
from discord.ext import commands
from .ContextEditor import Context as OldContext, ContextEditor, teardown as _teardown


class DeleteButton(discord.ui.Button):
    def __init__(self, ctx: commands.Context, *args, **kwargs):
        self.ctx = ctx
        kwargs.update(style=discord.ButtonStyle(4), label="Delete")
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        try:
            if (
                interaction.user.id == self.ctx.author.id
                or self.ctx.channel.permissions_for(interaction.user).manage_messages
            ):
                await interaction.message.delete()
            else:
                await interaction.response.send_message(
                    "You can only delete your own messages.", ephemeral=True
                )
        except Exception as e:
            print(traceback.format_exception(type(e), e, e.__traceback__))


class Context(OldContext):
    async def add_del_button(self, kwargs: dict):
        if kwargs.get("use_react", False):
            return kwargs
        view = kwargs.get("view", discord.ui.View())
        use_react = False
        #        emoji = await self.get_del_emoji(self.bot, self.message)
        if len(view.children) < 25:
            view.add_item(DeleteButton(self))  # , emoji=emoji))
        else:
            use_react = True
        kwargs.update(view=view, use_react=use_react)
        return kwargs

    @discord.utils.copy_doc(OldContext.send)
    async def send(self, content: str = None, **kwargs):
        return await super().send(content, **(await self.add_del_button(kwargs)))


def setup(bot: commands.Bot):
    ContextEditor(bot, Context)


def teardown(bot: commands.Bot):
    _teardown(bot)
