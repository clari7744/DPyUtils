import discord, asyncio, os
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_cache = self.bot.msg_cache
        self.msg_cache_size = self.bot.msg_cache_size

    async def reaction_delete(self, msg: discord.Message, del_em):
        if str(del_em).lower() in ("true", "t", "1", "enabled", "on", "yes", "y"):
            del_em = "🗑️"
        if not del_em:
            return
        if not isinstance(del_em, discord.Emoji):
            try:
                del_em = int(del_em)
                del_em = await self.bot.fetch_emoji(del_em)
            except:
                del_em = str(del_em)
        try:
            await msg.add_reaction(del_em)
        except:
            return
        try:
            r, u = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: str(r.emoji) == del_em
                and u.id == self.author.id
                and r.message.id == msg.id,
                timeout=120,
            )
        except asyncio.TimeoutError:
            await msg.remove_reaction(del_em, self.me)
        else:
            try:
                await msg.delete()
            except:
                pass

    async def _send(self, content, **kwargs):
        perms: discord.Permissions = self.me.permissions_in(self.channel)
        if not perms.send_messages:
            raise commands.CheckFailure(
                "Cannot Send",
                f"I don't have permission to send messages in {self.channel.mention}!",
            )
        if kwargs.get("embed", None) and not perms.embed_links:
            raise commands.CheckFailure(
                "Cannot Send",
                f"I don't have permission to embed links in {self.channel.mention}!",
            )
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
        no_save = kwargs.pop("no_save", False)
        no_edit = kwargs.pop("no_edit", False)
        clear_invoke_react = kwargs.pop("clear_invoke_react", True)
        clear_response_react = kwargs.pop("clear_response_react", True)
        del_em = kwargs.pop(
            "del_em", await self.bot.get_del_emoji(self.bot, self.message)
        )
        kwargs.setdefault("embed", None)
        if no_save:
            msg: discord.Message = await self._send(content, **kwargs)
            self.bot.loop.create_task(self.reaction_delete(msg, del_em))
            return msg
        if self.message.id not in self.msg_cache:
            msg = await self._send(content, **kwargs)
            self.msg_cache[self.message.id] = msg
            if len(self.msg_cache) >= self.msg_cache_size:
                self.bot.msg_cache = dict(
                    list(self.msg_cache.items())[1:]
                )  # Janky way of capping the dict
            self.bot.loop.create_task(self.reaction_delete(msg, del_em))
            return msg
        if clear_invoke_react and self.me.permissions_in(self.channel).manage_messages:
            await self.message.clear_reactions()
        ref = kwargs.pop("reference", None)
        if no_edit:
            self.msg_cache.pop(self.message.id, None)
            return await self.send(content, **kwargs)
        try:
            await self.msg_cache.get(self.message.id).edit(content=content, **kwargs)
            if (
                clear_response_react
                and self.me.permissions_in(self.channel).manage_messages
            ):
                await self.msg_cache[self.message.id].clear_reactions()
        except:
            self.msg_cache.pop(self.message.id, None)
            return await self.send(content, **kwargs)
        try:
            await self.msg_cache.get(self.message.id).edit(content=content, **kwargs)
            if (
                clear_response_react
                and self.me.permissions_in(self.channel).manage_messages
            ):
                await self.msg_cache[self.message.id].clear_reactions()
        except:
            self.msg_cache.pop(self.message.id, None)
            return await self.send(content, reference=ref, **kwargs)
        msg = await self.channel.fetch_message(self.msg_cache[self.message.id].id)
        self.bot.loop.create_task(self.reaction_delete(msg, del_em))
        return msg

    async def reply(self, content: str = None, **kwargs):
        return await self.send(content, reference=self.message, **kwargs)


class ContextEditor:
    def __init__(self, bot: commands.Bot, *, del_em=None):
        self.bot = bot
        bot.msg_cache = {}
        bot.msg_cache_size = 500
        bot.msg_del_emoji = del_em or os.getenv("CTX_DELETE_EMOJI", None)
        bot.get_del_emoji = self.get_del_emoji
        bot.get_context = self.get_context
        bot.process_commands = self.process_commands

        bot.add_listener(self.on_raw_message_edit, "on_raw_message_edit")
        bot.add_listener(self.on_raw_message_delete, "on_raw_message_delete")

    def cog_unload(self):
        self.bot.extra_events["on_raw_message_edit"] = [
            l
            for l in self.bot.extra_events.get("on_raw_message_edit", [])
            if l.__self__.__class__
            != getattr(
                self.bot.extensions.get("ContextEditor", None), "ContextEditor", None
            )
        ]
        self.bot.extra_events["on_raw_message_delete"] = [
            l
            for l in self.bot.extra_events.get("on_raw_message_delete", [])
            if l.__self__.__class__
            != getattr(
                self.bot.extensions.get("ContextEditor", None), "ContextEditor", None
            )
        ]
        self.bot.get_context = super(commands.Bot, self.bot).get_context
        self.bot.process_commands = super(commands.Bot, self.bot).process_commands
        del self.bot.msg_cache
        del self.bot.msg_cache_size
        del self.bot.msg_del_emoji
        del self.bot.get_del_emoji

    async def get_context(self, message: discord.Message, *, cls=Context):
        return await super(commands.Bot, self.bot).get_context(message, cls=cls)

    async def process_commands(self, message: discord.Message):
        ctx = await self.bot.get_context(message, cls=Context)
        await self.bot.invoke(ctx)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        try:
            msg = await self.bot.get_channel(payload.channel_id).fetch_message(
                payload.message_id
            )
        except:
            return
        if not msg.author.bot:
            await self.bot.process_commands(msg)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await asyncio.sleep(1)
        self.bot.msg_cache.pop(payload.message_id, None)

    async def get_del_emoji(self, bot: commands.Bot, message: discord.Message):
        """
        |coro|
        Returns bot.msg_del_emoji by default. Overwrite this to customize per locale.
        Parameters
        ----------
        bot :class:`Bot`
            Your bot instance
        message :class:`Message
            The message object that you want to use to detect locale for fetching del_emoji
        """
        return bot.msg_del_emoji


def setup(bot: commands.Bot):
    ContextEditor(bot)
