import discord, asyncio, os, jishaku, traceback
from discord.ext import commands
from typing import Union


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


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_cache = self.bot.msg_cache
        self.msg_cache_size = self.bot.msg_cache_size

    async def add_del_button(self, del_em, kwargs: dict):
        del_em = await self.bot.make_emoji(self.bot, del_em, allow_partial=True)
        view = kwargs.get("view", None) or discord.ui.View()
        fail = False
        if len(view.children) < 25:
            view.add_item(DeleteButton(self))  # , emoji=del_em))
        else:
            fail = True
        kwargs["view"] = view
        return kwargs, fail

    async def reaction_delete(self, msg: discord.Message, del_em, fail: bool):
        if not fail:
            return
        del_em = await self.bot.make_emoji(self.bot, del_em)
        try:
            await msg.add_reaction(del_em)  # Attempt to add the reaction
        except:
            return  # It failed, so do nothing
        try:
            await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: str(r.emoji) == del_em
                and not u.bot
                and (
                    u.id == self.author.id
                    or r.message.channel.permissions_for(u).manage_messages
                )
                and r.message.id == msg.id,
                timeout=120,
            )  # Wait for the author or a user with manage_messages to click the delete reaction
        except asyncio.TimeoutError:
            await msg.remove_reaction(
                del_em, self.me
            )  # They didn't click within two minutes, so delete the reaction
        else:
            try:
                await msg.delete()  # They *did* click the reaction, so attempt to delete the message
            except:
                pass  # Weird things happen sometimes

    async def _send(self, content, **kwargs):
        perms: discord.Permissions = self.channel.permissions_for(self.me)

        def error(thing):
            raise commands.CheckFailure(
                "Cannot Send",
                f"I don't have permission to {thing} in {self.channel.mention}!",
            )  # A harmless error instead of icky 4xx

        if (
            not perms.send_messages
        ):  # Most basic can't send that you'd think discord.py would handle
            error("send messages")
        if (
            kwargs.get("embed", kwargs.get("embeds", None)) and not perms.embed_links
        ):  # it's trying to send an embed without perms, so fail lol
            error("embed links")
        if (
            kwargs.get("file", kwargs.get("files", None)) and not perms.attach_files
        ):  # same as embeds but files
            error("attach files")
        if kwargs.get("reference", None):
            try:
                return await super().send(
                    content, **kwargs
                )  # whoooo all permission checks were passed
            except discord.HTTPException as e:
                if "message_reference" in str(e):
                    kwargs.pop("reference")
                    return await super().send(content, **kwargs)
                else:
                    raise e
        return await super().send(content, **kwargs)

    async def send(self, content: str = None, **kwargs):
        """

        Inherits from commands.Context.send. See the documentation for that function for normal arguments.

        Creates a message cache that saves responses to be edited in subsequent commands.

        Parameters
        ------------
        no_save :class:`bool`
            Indicates whether to override this function and go straight to commands.Context.send without editing or saving message ID. Defaults to `False`.
        no_edit :class:`bool`
            Indicates whether to edit the previously sent message if editing a message or not. If this is set to `True`, the ID of the new message will still be saved. Defaults to `False`.
        clear_invoke_react :class:`bool`
            Indicates whether to clear reactions from the invoking message. Defaults to `True`.
        clear_response_react :class:`bool`
            Indicates whether to clear reactions from the response message. Defaults to `True`.
        del_em Union[:class:`bool`, :class:`int`, :class:`str`, :class:`Emoji`, None]
            Defines reaction that will be added to a message, that can then be clicked on to delete message. Set to `None` to disable for that message. Uses `bot.msg_del_emoji` by default, which can be set via an environment variable (`CTX_DELETE_EMOJI=str|int|bool`) or by initializing the class with `del_em=emoji`.
            Defaults to 🗑 if not set.
        del_em_timeout :class:`int`
            The amount of seconds until the reaction deletion times out.

        Raises
        -------
        See commands.Context.send

        Returns
        --------
        :class:`~discord.Message`
            The message that was sent or edited.
        """
        no_save, no_edit = [kwargs.pop(k, False) for k in ("no_save", "no_edit")]
        clear_invoke_react = kwargs.pop("clear_invoke_react", True)
        clear_response_react = kwargs.pop("clear_response_react", True)
        del_em = kwargs.pop(
            "del_em", await self.bot.get_del_emoji(self.bot, self.message)
        )
        kwargs.setdefault("embed", None)
        if any(k in kwargs for k in ("file", "files")):
            no_edit = True
        mid = self.message.id

        kwargs, fail = await self.add_del_button(del_em, kwargs)
        if no_save:
            msg: discord.Message = await self._send(content, **kwargs)
            self.bot.loop.create_task(self.reaction_delete(msg, del_em, fail))
            return msg

        if mid not in self.msg_cache:
            msg = await self._send(content, **kwargs)
            self.msg_cache[mid] = msg
            if len(self.msg_cache) >= self.msg_cache_size:
                self.bot.msg_cache = dict(
                    list(self.msg_cache.items())[1:]
                )  # Janky way of capping the dict
            self.bot.loop.create_task(self.reaction_delete(msg, del_em, fail))
            return msg

        if no_edit:
            self.msg_cache.pop(mid, None)
            return await self.send(content, **kwargs)

        if self.channel.permissions_for(self.me).manage_messages:
            if clear_invoke_react:
                await self.message.clear_reactions()
            if clear_response_react:
                try:
                    await self.msg_cache[mid].clear_reactions()
                except:
                    pass

        try:
            kwargs.pop("reference", None)
            await self.msg_cache[mid].edit(content=content, **kwargs)
        except discord.NotFound:
            self.msg_cache.pop(mid, None)
            return await self.send(content, **kwargs)

        try:
            msg = await self.channel.fetch_message(self.msg_cache[mid].id)
            self.bot.loop.create_task(self.reaction_delete(msg, del_em, fail))
        except:
            pass
        return msg

    async def reply(self, content: str = None, **kwargs):
        return await self.send(content, reference=self.message, **kwargs)


class ContextEditor:
    def __init__(self, bot: commands.Bot, **kwargs):
        # TODO Format this better later
        """
        Options:
        `del_em` The emoji used for bot.msg_del_emoji
        msg_cache_size :class:`int` The maximum size allowed for the cache before it starts removing messages.
        """
        self.bot = bot
        self.bot_super = super(bot.__class__, self.bot)

        bot.msg_cache = {}
        bot.msg_cache_size = kwargs.pop("msg_cache_size", 500)
        bot.msg_del_emoji = kwargs.pop("del_em", os.getenv("CTX_DELETE_EMOJI", None))
        bot.get_del_emoji = self.get_del_emoji
        bot.make_emoji = self.make_emoji

        bot.get_context = self.get_context
        bot.process_commands = self.process_commands
        bot.invoke = self.invoke

        bot.add_listener(self.on_raw_message_edit, "on_raw_message_edit")
        bot.add_listener(self.on_raw_message_delete, "on_raw_message_delete")

    async def get_context(self, message: discord.Message, *, cls=Context):
        return await self.bot_super.get_context(message, cls=cls)

    async def process_commands(self, message: discord.Message):
        ctx = await self.bot.get_context(message, cls=Context)
        await self.bot.invoke(ctx)

    async def invoke(self, ctx: commands.Context):
        if ctx.command is not None:
            #            if not self.bot.msg_cache.get(ctx.message.id, None):
            #                await ctx.trigger_typing()
            await self.bot_super.invoke(ctx)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        chan = self.bot.get_channel(payload.channel_id)
        if not chan:
            return
        me = chan.me if isinstance(chan, discord.DMChannel) else chan.guild.me
        if not chan.permissions_for(me).read_messages:
            return
        try:
            msg = await chan.fetch_message(payload.message_id)
        except:
            return
        if not msg.author.bot and chan.permissions_for(me).send_messages:
            await self.bot.process_commands(msg)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await asyncio.sleep(1)
        self.bot.msg_cache.pop(payload.message_id, None)

    # fix this lol
    # if i want it to be a bot function then it probably should work better than this
    # and i should fix that `self` and stuff

    async def get_del_emoji(self, bot: commands.Bot, message: discord.Message):
        """
        |coro|
        Returns bot.msg_del_emoji by default. Overwrite this to customize per locale.
        Parameters
        ----------
        bot :class:`Bot`
            Your bot instance
        message :class:`Message`
            The message object that you want to use to detect locale for fetching del_emoji
        """
        return bot.msg_del_emoji

    async def make_emoji(
        self,
        bot: commands.Bot,
        emoji: Union[discord.Emoji, discord.PartialEmoji, int, str],
        *,
        allow_partial: bool = False,
    ):
        if str(emoji).lower() in ("true", "t", "1", "enabled", "on", "yes", "y"):
            emoji = "🗑️"  # If it's only a bool, then default to trash can unicode
        if not emoji:  # It wasn't enabled
            return None
        if isinstance(emoji, discord.Emoji):
            return emoji
        if emoji.isdigit():
            try:
                emoji = await bot.fetch_emoji(
                    int(emoji)
                )  # Get a custom emoji by ID if possible
            except:
                emoji = (int if allow_partial else str)(emoji)
        else:
            emoji = str(emoji)
        return emoji


def setup(bot: commands.Bot):
    ContextEditor(bot)


def teardown(bot: commands.Bot):
    bot_super = super(bot.__class__, bot)
    get_l = lambda l: discord.utils.find(
        lambda e: e.__self__.__class__.__name__ == "ContextEditor",
        bot.extra_events["on_raw_message_" + l],
    )
    bot.remove_listener(get_l("edit"))
    bot.remove_listener(get_l("delete"))

    bot.get_context = bot_super.get_context
    bot.process_commands = bot_super.process_commands
    bot.invoke = bot_super.invoke

    del bot.msg_cache, bot.msg_cache_size
    del bot.msg_del_emoji, bot.get_del_emoji, bot.make_emoji
