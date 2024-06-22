import typing

from discord import Member, Role
from discord.ext import commands


def is_guild_owner():
    """
    Decorator to ensure that the command invoker is the guild owner.
    Only works in a guild, so implements :func:`@commands.guild_only` internally.

    Examples
    --------
    .. code-block:: python3

        @bot.command()
        @is_guild_owner()
        async def guild_owner_only(ctx):
            await ctx.send("You are the guild owner!")
    """

    def pred(ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.author.id == ctx.guild.owner_id:
            return True
        raise commands.CheckFailure("This command can only be used by the guild owner!")

    return commands.check(pred)


def check_hierarchy(
    ctx: commands.Context,
    obj: typing.Union[Member, Role],
    *,
    return_bool: bool = False,
):
    """
    Only works in a guild, so implements :func:`@commands.guild_only` internally.
    Ensure that both the bot and the command invoker are higher than the given object (Role or Member).

    Parameters
    ------------
    ctx: :class:`commands.Context`
        The context of the command.
    obj: Union[:class:`discord.Member`, :class:`discord.Role`]
        The object to check hierarchy against.
    return_bool: :class:`bool`
        Whether to return a boolean or raise an error. Defaults to False (raise an error).

    Examples
    --------
    .. code-block:: python3

        @bot.command()
        async def hierarchy(ctx, role: discord.Role):
            if check_hierarchy(ctx, role, return_bool=True):
                await ctx.send("I am higher than the role and you are higher than the role!")
            else:
                await ctx.send("I am not higher than the role or you are not higher than the role!")
    """
    if not ctx.guild:
        raise commands.NoPrivateMessage()

    def err(thing):
        if return_bool:
            return False
        raise commands.CheckFailure(f"{obj} is higher than {thing}!")

    if ctx.me.top_role <= getattr(obj, "top_role", obj):
        return err("me")
    if ctx.author.top_role <= getattr(obj, "top_role", obj):
        return err("you")
    return True
