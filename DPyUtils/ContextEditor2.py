import traceback
from logging import getLogger

from discord import ButtonStyle, Interaction, ui
from discord.ext import commands
from discord.utils import copy_doc

from .ContextEditor import Context as OldContext
from .ContextEditor import ContextEditor
from .ContextEditor import teardown as _teardown

log = getLogger(__name__)


class DeleteButton(ui.Button):
    """
    A button that deletes the message it is attached to.

    Parameters
    ----------
    ctx : commands.Context
        The context of the command that created the message.
    """

    def __init__(self, ctx: commands.Context, *args, **kwargs):
        self.ctx = ctx
        kwargs.update(style=ButtonStyle(4), label="Delete")
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction):
        try:
            if (
                interaction.user.id == self.ctx.author.id
                or self.ctx.channel.permissions_for(interaction.user).manage_messages
            ):
                await interaction.message.delete()
            else:
                await interaction.response.send_message(
                    "You can only delete your own command responses.", ephemeral=True
                )
        except Exception as e:
            log.error(traceback.format_exception(type(e), e, e.__traceback__))


class Context(OldContext):
    """
    A subclass of `commands.Context` that adds a delete button to the message.
    """

    async def add_del_button(self, kwargs: dict):
        """
        A hook that adds a delete button to the message as long as the message has less than 25 buttons.
        """
        view = kwargs.get("view", ui.View())
        if kwargs.get("use_react", False) or view is None:
            return kwargs
        use_react = False
        #        emoji = await self.get_del_emoji(self.bot, self.message)
        if len(view.children) < 25:
            try:
                view.add_item(DeleteButton(self))  # , emoji=emoji))
            except Exception as e:
                log.error(traceback.format_exception(type(e), e, e.__traceback__))
                use_react = True
        else:
            use_react = True
        kwargs.update(view=view, use_react=use_react)
        return kwargs

    @copy_doc(OldContext.send)
    async def send(self, content: str = None, **kwargs):
        return await super().send(content, **(await self.add_del_button(kwargs)))


async def setup(bot: commands.Bot):
    ContextEditor(bot, Context)


async def teardown(bot: commands.Bot):
    await _teardown(bot)
