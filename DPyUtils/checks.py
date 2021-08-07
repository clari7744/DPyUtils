import discord, typing
from discord.ext import commands


def is_guild_owner():
    def pred(ctx: commands.Context):
        if ctx.author.id == ctx.guild.owner_id:
            return True
        raise commands.CheckFailure(
            f"This command can only be used by the guild owner!"
        )

    return commands.check(pred)


def check_hierarchy(
    ctx: commands.Context,
    obj: typing.Union[discord.Member, discord.Role],
    *,
    return_bool: bool = False,
):
    def err(thing):
        if return_bool:
            return False
        raise commands.CheckFailure(f"{obj} is higher than {thing}!")

    if ctx.bot.top_role <= getattr(obj, "top_role", obj):
        return err("me")
    if ctx.author.top_role <= getattr(obj, "top_role", obj):
        return err("you")
    return True
