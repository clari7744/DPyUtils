import discord
from discord.ext import commands


class Command(commands.Command):
    def __init__(self, func, **kwargs):
        for attr in ("flags", "trigger_typing"):
            val = kwargs.get(attr, getattr(func, f"__{attr}__", None))
            setattr(self, attr, val)
        super().__init__(func, **kwargs)

    async def invoke(self, ctx: commands.Context):
        if (
            self.trigger_typing is False
            or not getattr(ctx.bot, '_type_on_command', False)
            or not ctx.channel.permissions_for(ctx.me).send_messages
        ):
            pass
        elif getattr(ctx.bot, '_type_on_command', False) or self.trigger_typing is True:
            await ctx.trigger_typing()
        return await super().invoke(ctx)


def command(name=None, cls=None, **attrs):
    if cls is None:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **attrs)

    return decorator


def typing(on: bool):
    """
    A decorator to set typing to on or off for a specific command. Overrides bot settings.
    """

    def deco(func):
        if isinstance(func, commands.Command):
            func.trigger_typing = bool(on)
        else:
            func.__trigger_typing__ = bool(on)
        return func

    return deco


commands.command = command
commands.Command = Command
