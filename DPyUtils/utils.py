# TO ADD:
# wait_for reaction confirmation
# - optional yes/no reactions, default `✅/❌`, returns boolean maybe idk
# - params: bot,check=None,timeout=None,*,yes='✅',no='❌'
# wait_for_reaction_or_message

import discord, os, traceback
from discord.ext import commands
from typing import Union, List, Iterable


def load_extensions(
    bot: commands.Bot,
    *,
    directories: List = ["cogs"],
    extra_cogs: List = [],
    skip: List = [],
):
    extensions = [*extra_cogs]
    directories = [*directories]
    for _dir in directories:
        for file in os.listdir(_dir):
            if file.endswith(".py") and not file.startswith("__"):
                extensions.append(f"{_dir.replace('/', '.')}.{file[:-3]}")
    print(f"Extensions to attempt to load: {', '.join(extensions)}")
    extensions = [e for e in extensions if e not in skip]
    for e in extensions:
        try:
            bot.load_extension(e)
            print(f"Loaded '{e}' successfully.")
        except Exception as err:
            print(f"Failed to load {e}!\nReason:\n{err}")
            print(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
    for e in skip:
        print(f"Skipped {e}")


async def try_dm(
    ctx: commands.Context,
    member: Union[discord.User, discord.Member],
    content=None,
    *,
    fallback_ctx: bool = False,
    **kwargs,
):
    if member.bot:
        return None if not fallback_ctx else await ctx.send(content, **kwargs)
    try:
        return await member.send(content, **kwargs)
    except:
        if (
            fallback_ctx and isinstance(ctx.channel, discord.DMChannel)
        ) or not fallback_ctx:
            return None
        return await ctx.send(content, **kwargs)


def s(value: Union[Iterable, int]):
    num = value if isinstance(value, int) else len(value)
    return "s" if num != 1 else ""
