import discord, re, typing, collections, datetime
from discord.ext import commands


ParsedDuration = collections.namedtuple(
    "ParsedDuration",
    "years weeks days hours minutes seconds total_seconds",
    defaults=[0, 0, 0, 0, 0, 0, 0],
)

# All short times corresponding to amount of seconds
durations = {
    "y": 31536000,  # 60*60*24*365
    "w": 604800,  # 60*60*24*7
    "d": 86400,  # 60*60*24
    "h": 3600,  # 60*60
    "m": 60,  # 60
    "s": 1,  # 60/60
}


class InvalidTimeFormat(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(
            "'{}' is an invalid format for time! Format must be '1y1w1d1h1m1s'.".format(
                argument
            )
        )


class DurationParser(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return int(argument)
        except:
            pass
        seconds = 0
        match = re.findall("([0-9]+[ywdhms])", argument)
        if not match:
            raise InvalidTimeFormat(argument)
        for item in match:
            seconds += int(item[:-1]) * durations[item[-1]]
        return seconds


def parse(param: typing.Union[int, datetime.timedelta]):
    """
    This function takes an int or timedelta parameter of seconds and formats it, returning a named tuple ParsedDuration that has years, weeks, days, hours, minutes and seconds. It also includes the total_seconds, the input.
    """
    parsed = {}
    seconds = (
        param.total_seconds() if isinstance(param, datetime.timedelta) else int(param)
    )
    ts = int(seconds)
    for unit, sec in durations.items():
        parsed[unit] = int(seconds // sec)
        seconds = int(seconds - (parsed[unit] * sec))
    return ParsedDuration(
        years=parsed["y"],
        weeks=parsed["w"],
        days=parsed["d"],
        hours=parsed["h"],
        minutes=parsed["m"],
        seconds=parsed["s"],
        total_seconds=ts,
    )