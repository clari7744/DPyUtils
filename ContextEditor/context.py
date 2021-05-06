import discord, asyncio
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_cache = self.bot.msg_cache
        self.msg_cache_size = self.bot.msg_cache_size

    async def send(self, content: str = None, **kwargs):
        """
        |coro|

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
        kwargs["embed"] = kwargs.pop("embed", None)
        if no_save:
            return await super().send(content, **kwargs)
        if self.message.id in self.msg_cache:
            if (
                clear_invoke_react
                and self.me.permissions_in(self.channel).manage_messages
            ):
                await self.message.clear_reactions()
            ref = kwargs.pop("reference", None)
            if no_edit:
                self.msg_cache.pop(self.message.id, None)
                return await self.send(content, **kwargs)
            try:
                await self.msg_cache.get(self.message.id).edit(
                    content=content, **kwargs
                )
                if (
                    clear_response_react
                    and self.me.permissions_in(self.channel).manage_messages
                ):
                    await self.msg_cache[self.message.id].clear_reactions()
            except:
                self.msg_cache.pop(self.message.id, None)
                return await self.send(content, reference=ref, **kwargs)
            return await self.channel.fetch_message(self.msg_cache[self.message.id].id)
        else:
            msg = await super().send(content, **kwargs)
            self.msg_cache[self.message.id] = msg
            if len(self.msg_cache) >= self.msg_cache_size:
                self.bot.msg_cache = dict(
                    list(self.msg_cache.items())[1:]
                )  # Janky way of capping the dict
            return msg

    async def reply(self, content: str = None, **kwargs):
        return await self.send(content, reference=self.message, **kwargs)


class ContextEditor:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.msg_cache = {}
        bot.msg_cache_size = 500
        bot.get_context = self.get_context
        bot.process_commands = self.process_commands

        bot.add_listener(self.on_raw_message_edit, "on_raw_message_edit")
        bot.add_listener(self.on_raw_message_delete, "on_raw_message_delete")

    async def get_context(self, message: discord.Message, *, cls=Context):
        return await super(commands.Bot, self.bot).get_context(message, cls=cls)

    async def process_commands(self, message: discord.Message):
        ctx = await self.bot.get_context(message, cls=Context)
        await self.bot.invoke(ctx)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        msg = await self.bot.get_channel(payload.channel_id).fetch_message(
            payload.message_id
        )
        if not msg.author.bot:
            await self.bot.process_commands(msg)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await asyncio.sleep(1)
        self.bot.msg_cache.pop(payload.message_id, None)
