import discord, asyncio
from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.msg_cache = self.bot.msg_cache

    @discord.utils.cached_property
    def replied_reference(self):
        return (
            self.message.reference.resolved.to_reference()
            if self.message.reference
            else None
        )

    async def send(self, content: str = None, **kwargs):
        no_save = kwargs.pop("no_save", False)
        no_edit = kwargs.pop("no_edit", False)
        kwargs["embed"] = kwargs.pop("embed", None)
        if no_save:
            return await super().send(content, **kwargs)
        if self.message.id in self.msg_cache:
            ref = kwargs.pop("reference", None)
            if no_edit:
                self.msg_cache.pop(self.message.id)
                return await self.send(content, **kwargs)
            try:
                await self.msg_cache[self.message.id].edit(content=content, **kwargs)
            except:
                self.msg_cache.pop(self.message.id)
                return await self.send(content, reference=ref, **kwargs)
            return await self.channel.fetch_message(self.msg_cache[self.message.id].id)
        else:
            msg = await super().send(content, **kwargs)
            self.msg_cache[self.message.id] = msg
            return msg

    async def reply(self, content: str = None, **kwargs):
        return await self.send(content, reference=self.message, **kwargs)


class ContextEditor:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.msg_cache = {}
        bot.get_context = self.get_context
        bot.process_commands = self.process_commands
        bot.on_raw_message_edit = self.on_raw_message_edit
        bot.on_raw_message_delete = self.on_raw_message_delete

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
