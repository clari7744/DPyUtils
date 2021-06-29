# TO ADD:
# wait_for reaction confirmation
# - optional yes/no reactions, default `✅/❌`, returns boolean maybe idk
# - params: bot,check=None,timeout=None,*,yes='✅',no='❌'
# wait_for_reaction_or_message

import discord, typing, os, traceback
from discord.ext import commands


def load_extensions(
    bot: commands.Bot,
    *,
    directories: typing.List = ["cogs"],
    extra_cogs: typing.List = [],
    skip: typing.List = [],
):
    extensions = [*extra_cogs]
    directories = [*directories]
    for _dir in directories:
        for file in os.listdir(_dir):
            if file.endswith(".py"):
                extensions.append(f"{_dir}.{file[:-3]}")
    print(f"Extensions to attempt to load: {', '.join(extensions)}")
    for e in extensions:
        if e in skip:
            print(f"Skipped {e}.")
            continue
        try:
            bot.load_extension(e)
            print(f"Loaded '{e}' successfully.")
        except Exception as err:
            print(f"Failed to load {e}!\nReason:\n{err}")
            print(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
