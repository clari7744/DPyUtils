import os
import traceback
from logging import getLogger
from typing import Iterable, List, Union

from discord import DMChannel, Member, User
from discord.ext import commands

log = getLogger(__name__)


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
    log.info(f"Extensions to attempt to load: {', '.join(extensions)}")
    extensions = sorted(f"'{e}'" for e in extensions if e not in skip)
    # sorted([f"'{e}'" for e in extensions if e not in skip], key=lambda x: x.lower().split(".")[-1])
    maxl = max(map(len, extensions))
    for e in extensions:
        try:
            await bot.load_extension(e.strip("'"))
            log.info(f"Loaded {e:{maxl}} successfully.")
        except Exception as err:
            log.error(f"Failed to load {e}!\nReason:\n{err}")
            log.error("".join(traceback.format_exception(type(err), err, err.__traceback__)))
    for e in skip:
        log.info(f"Skipped {e}")


async def try_dm(
    ctx: commands.Context,
    member: Union[User, Member],
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
        if (fallback_ctx and isinstance(ctx.channel, DMChannel)) or not fallback_ctx:
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
        return text[: max_len - 1].rstrip() + "…"
    return text


def yn(val: bool):
    """
    Convert a value to Yes/No
    """
    return "Yes" if val else "No"
