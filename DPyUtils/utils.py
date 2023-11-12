import os
import traceback
from typing import Iterable, List, Union

import discord
from discord.ext import commands


async def load_extensions(
    bot: commands.Bot,
    *,
    directories: List[str] = ["cogs"],
    extra_cogs: List[str] = None,
    skip: List[str] = None,
):
    extensions = [*(extra_cogs or [])]
    directories = [*directories]
    skip = skip or []
    for _dir in directories:
        for file in os.listdir(_dir):
            if file.endswith(".py") and not file.startswith("__"):
                extensions.append(f"{_dir.replace('/', '.')}.{file[:-3]}")
    print(f"Extensions to attempt to load: {', '.join(extensions)}")
    extensions = [e for e in extensions if e not in skip]
    maxl = max(map(len, extensions)) + 2
    for e in extensions:
        e = f"'{e}'"
        try:
            await bot.load_extension(e.strip("'"))
            print(f"Loaded {e:{maxl}} successfully.")
        except Exception as err:
            print(f"Failed to load {e}!\nReason:\n{err}")
            print("".join(traceback.format_exception(type(err), err, err.__traceback__)))
    for e in skip:
        print(f"Skipped '{e}'")


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
    except Exception:
        if (fallback_ctx and isinstance(ctx.channel, discord.DMChannel)) or not fallback_ctx:
            return None
        return await ctx.send(content, **kwargs)


def s(value: Union[Iterable, int]):
    """
    returns `s` if the given number or iterable is not equal to 1
    """
    num = value if isinstance(value, (int, float)) else len(value)
    return "s" if num != 1 else ""


def an(value: str):
    """
    returns `an {value}` if the given value starts with a vowel, otherwise `a {value}`
    """
    return f"a{'n' if value.startswith(tuple('aeiou')) else ''} {value}"


def _and(*args: str):
    """
    Joins the given values with commas and the word "and" at the end
    """
    if len(args) > 2:
        fmt = f"{', '.join(args[:-1])}, and {args[-1]}"
    else:
        fmt = " and ".join(args)
    return fmt


def trim(text: str, max_len: int):
    """
    Trims the text to the maximum length and adds ellipsis if it's too long
    """
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def yn(val: bool):
    """
    Convert a value to Yes/No
    """
    return "Yes" if val else "No"
