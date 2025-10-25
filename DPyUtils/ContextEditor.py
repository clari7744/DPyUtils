import asyncio
import os
from typing import Union

from discord import (
    DMChannel,
    Emoji,
    Message,
    PartialEmoji,
    Permissions,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
    utils,
)
from discord.errors import Forbidden, HTTPException, NotFound
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_cache = self.bot.msg_cache
        self.msg_cache_size = self.bot.msg_cache_size

    async def reaction_delete(self, msg: Message, del_em: bool | str | int | Emoji | None):
        """
        Handles message-delete reactions.
        Adds the reaction to the message, waits for the author or a user with manage_messages to click the reaction, and then deletes the message.
        If the reaction isn't clicked, remove it.

        Parameters
        ----------
        msg :class:`Message`
            The message to add the reaction to.
        del_em : Union[:class:`bool`, :class:`int`, :class:`str`, :class:`Emoji`, None]
            The emoji to use for the delete reaction.
        """
        if str(del_em).lower() in ("true", "t", "1", "enabled", "on", "yes", "y"):  #
            del_em = "🗑️"  # If it's only a bool, then default to trash can unicode
        if not del_em:  # It wasn't enabled
            return
        if not isinstance(del_em, Emoji):
            try:
                del_em = await self.bot.fetch_emoji(int(del_em))  # Get a custom emoji by ID if possible
            except (NotFound, HTTPException):
                del_em = str(del_em)  # It's either unicode, full custom format `<a?:name:ID>`, or trash
        try:
            await msg.add_reaction(del_em)  # Attempt to add the reaction
        except HTTPException:
            return  # It failed, so do nothing
        try:
            await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: str(r.emoji) == del_em
                and not u.bot
                and (u.id == self.author.id or r.message.channel.permissions_for(u).manage_messages)
                and r.message.id == msg.id,
                timeout=120,
            )  # Wait for the author or a user with manage_messages to click the delete reaction
        except asyncio.TimeoutError:
            await msg.remove_reaction(del_em, self.me)  # They didn't click within two minutes, so delete the reaction
        else:
            try:
                await msg.delete()  # They *did* click the reaction, so attempt to delete the message
            except (NotFound, HTTPException):
                pass  # Weird things happen sometimes

    async def _send(self, content: str, **kwargs):
        """
        Sends a message with the given content and keyword arguments.

        Parameters
        ----------
        content :class:`str`
            The content of the message to send.
        """
        perms: Permissions = self.channel.permissions_for(self.me)

        def error(thing):
            if not getattr(self, "interaction", None):  # slash commands do be special
                raise commands.CheckFailure(
                    "Cannot Send",
                    f"I don't have permission to {thing} in {self.channel.mention}!",
                )  # A harmless error instead of icky 4xx

        if not perms.send_messages:  # Most basic can't send that you'd think discord.py would handle
            error("send messages")
        if (
            kwargs.get("embed", kwargs.get("embeds", None)) and not perms.embed_links
        ):  # it's trying to send an embed without perms, so fail lol
            error("embed links")
        if kwargs.get("file", kwargs.get("files", None)) and not perms.attach_files:  # same as embeds but files
            error("attach files")
        if kwargs.get("reference", None):
            try:
                return await super().send(content, **kwargs)  # whoooo all permission checks were passed
            except HTTPException as e:
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
        msg, del_em, use_react = await self._do_send(content, **kwargs)
        if not use_react:
            return msg
        self.bot.loop.create_task(self.reaction_delete(msg, del_em))
        return msg

    async def _do_send(self, content: str = None, **kwargs):
        no_save, no_edit = [kwargs.pop(k, False) for k in ("no_save", "no_edit")]
        clear_invoke_react = kwargs.pop("clear_invoke_react", True)
        clear_response_react = kwargs.pop("clear_response_react", True)
        del_em = kwargs.pop("del_em", await self.bot.get_del_emoji(self.bot, self.message))
        use_react = kwargs.pop("use_react", True)
        if kwargs.get("embed"):
            kwargs["embeds"] = [kwargs.pop("embed")]
        elif not kwargs.get("embeds"):
            kwargs["embed"] = None
        if any(k in kwargs for k in ("file", "files", "ephemeral")):
            no_edit = True
        mid = self.message.id

        if no_save:
            return await self._send(content, **kwargs), del_em, use_react

        if mid not in self.msg_cache:
            msg = await self._send(content, **kwargs)
            self.msg_cache[mid] = msg
            if len(self.msg_cache) >= self.msg_cache_size:
                self.bot.msg_cache = dict(list(self.msg_cache.items())[1:])  # Janky way of capping the dict=
            return msg, del_em, use_react

        if no_edit:
            self.msg_cache.pop(mid, None)
            return await self._do_send(content, **kwargs)

        if self.channel.permissions_for(self.me).manage_messages:
            if clear_invoke_react:
                try:
                    await self.message.clear_reactions()
                except (Forbidden, HTTPException):
                    pass
            if clear_response_react:
                try:
                    await self.msg_cache[mid].clear_reactions()
                except (Forbidden, HTTPException):
                    pass

        try:
            kwargs.pop("reference", None)
            await self.msg_cache[mid].edit(content=content, **kwargs)
        except NotFound:
            self.msg_cache.pop(mid, None)
            return await self._do_send(content, **kwargs)

        try:
            msg = await self.channel.fetch_message(self.msg_cache[mid].id)
        except (NotFound, HTTPException, Forbidden):
            msg = None
        return msg, del_em, use_react

    async def reply(self, content: str = None, **kwargs):
        return await self.send(content, reference=self.message, **kwargs)


class ContextEditor:
    def __init__(self, bot: commands.Bot, context: Context, del_em: str = None, msg_cache_size: int = 500):
        # TODO Format this better later
        """
        A psuedo-cog that enables triggering commands on message edit, as well as adding a reaction to allow the triggering user to delete the response.

        Parameters
        ----------
        bot :class:`commands.Bot`
            Your bot instance
        context :class:`Context`
            The context class to use for the bot
        **kwargs
            del_em :class:`str`
                The emoji used for bot.msg_del_emoji
            msg_cache_size :class:`int`
                The maximum size allowed for the cache before it starts removing messages.
        """
        self.Context = context
        self.bot = bot
        self.bot_super = super(bot.__class__, self.bot)

        bot.msg_cache = {}
        bot.msg_cache_size = msg_cache_size
        bot.msg_del_emoji = del_em or os.getenv("CTX_DELETE_EMOJI") or None
        bot.get_del_emoji = self.get_del_emoji
        bot.make_emoji = self.make_emoji

        bot.get_context = self.get_context
        bot.process_commands = self.process_commands
        bot.invoke = self.invoke

        bot.add_listener(self.on_raw_message_edit, "on_raw_message_edit")
        bot.add_listener(self.on_raw_message_delete, "on_raw_message_delete")

    async def get_context(self, message: Message, *, cls=None):
        return await self.bot_super.get_context(message, cls=cls or self.Context)

    async def process_commands(self, message: Message):
        ctx = await self.bot.get_context(message, cls=self.Context)
        await self.bot.invoke(ctx)

    async def invoke(self, ctx: commands.Context):
        if ctx.command is not None:
            #            if not self.bot.msg_cache.get(ctx.message.id, None):
            #                await ctx.trigger_typing()
            await self.bot_super.invoke(ctx)

    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        """
        Handles message edits by processing commands on the edited message.

        Parameters
        ----------
        payload :class:`RawMessageUpdateEvent`
            The payload from the message edit event.
        """
        # Sending a message with an attachment link triggers a message edit with content None to show the embed, this should hopefully catch that.
        if payload.data.get("content") is None:
            return
        chan = self.bot.get_channel(payload.channel_id)
        if not chan:
            return
        me = chan.me if isinstance(chan, DMChannel) else chan.guild.me
        if not chan.permissions_for(me).read_messages:
            return
        try:
            msg = await chan.fetch_message(payload.message_id)
        except (NotFound, Forbidden, HTTPException):
            return
        # if it was edited, and less than 3 seconds ago
        if (
            msg.edited_at is not None
            and (utils.utcnow() - msg.edited_at).total_seconds() < 3
            and not msg.author.bot
            and chan.permissions_for(me).send_messages
        ):
            await self.bot.process_commands(msg)

    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        """
        Handles message deletes by removing the message from the cache.

        Parameters
        ----------
        payload :class:`RawMessageDeleteEvent`
            The payload from the message delete event.
        """
        await asyncio.sleep(1)
        self.bot.msg_cache.pop(payload.message_id, None)

    # fix this lol
    # if i want it to be a bot function then it probably should work better than this
    # and i should fix that `self` and stuff

    async def get_del_emoji(self, bot: commands.Bot, message: Message):
        """
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
        emoji: Union[Emoji, PartialEmoji, int, str],
        *,
        allow_partial: bool = False,
    ):
        """
        Converts a string or integer to an emoji object if possible.

        Parameters
        ----------
        bot :class:`Bot`
            Your bot instance
        emoji : Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`int`, :class:`str`]
            The emoji to convert.
        allow_partial :class:`bool`
            Whether to allow partial emoji objects to be returned. Defaults to False.

        Returns
        -------
        Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`, :class:`int`]
            The emoji object if possible, otherwise the original input.
        """
        if str(emoji).lower() in ("true", "t", "1", "enabled", "on", "yes", "y"):
            emoji = "🗑️"  # If it's only a bool, then default to trash can unicode
        if not emoji:  # It wasn't enabled
            return None
        if isinstance(emoji, Emoji):
            return emoji
        if emoji.isdigit():
            emoji = bot.get_emoji(int(emoji))  # Get a custom emoji by ID if possible
            if emoji is None:
                emoji = (int if allow_partial else str)(emoji)
        else:
            emoji = str(emoji)
        return emoji


async def setup(bot: commands.Bot):
    ContextEditor(bot, Context)


async def teardown(bot: commands.Bot):
    bot_super = super(bot.__class__, bot)

    def get_l(listnr: str):
        return utils.find(
            lambda e: e.__self__.__class__.__name__ == "ContextEditor",
            bot.extra_events["on_raw_message_" + listnr],
        )

    bot.remove_listener(get_l("edit"))
    bot.remove_listener(get_l("delete"))

    bot.get_context = bot_super.get_context
    bot.process_commands = bot_super.process_commands
    bot.invoke = bot_super.invoke

    del bot.msg_cache, bot.msg_cache_size
    del bot.msg_del_emoji, bot.get_del_emoji, bot.make_emoji
