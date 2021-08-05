import discord, inspect, datetime
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self, *args, **options):
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.start_time = datetime.datetime.now()
        self.utc_start_time = discord.utils.utcnow()

        options.setdefault("strip_after_prefix", True)
        options.setdefault(
            "allowed_mentions",
            discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=False
            ),
        )
        options.setdefault("case_insensitive", True)

        super().__init__(*args, **options)

    @classmethod
    def inspect(cls, obj, lines: bool = 0):
        _lines = inspect.getsourcelines(obj)
        return _lines if lines else "".join(_lines[0])
