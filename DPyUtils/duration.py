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


class Duration:
    def __init__(self, original: str = "0", seconds: int = 0):
        if not isinstance(seconds, int) or isinstance(seconds, str) and str.isdigit():
            raise TypeError("Seconds must be an integer!")
        self._original = str(original)
        self._seconds = int(seconds)

    def __str__(self):
        return self._original

    def __int__(self):
        return self._seconds

    def __iter__(self):
        yield from (self._original, self._seconds)

    @property
    def original(self):
        """
        Returns the original argument passed to the duration converter.
        """
        return self._original

    @property
    def seconds(self):
        """
        Returns the amount of seconds that the duration passed in was converted to.
        """
        return self._seconds

    # TODO: Create a docstring for this class
    @classmethod
    async def convert(cls, ctx, argument):
        try:
            return cls(argument, int(argument))
        except:
            pass
        seconds = 0
        match = re.findall("([0-9]+?(?:\.[0-9]+)?[ywdhms])", argument)
        if not match:
            raise InvalidTimeFormat(argument)
        for item in match:
            seconds += float(item[:-1]) * durations[item[-1]]
        return cls(argument, round(seconds))


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
        parsed[unit], seconds = divmod(seconds, sec)
    return ParsedDuration(
        years=parsed["y"],
        weeks=parsed["w"],
        days=parsed["d"],
        hours=parsed["h"],
        minutes=parsed["m"],
        seconds=parsed["s"],
        total_seconds=ts,
    )


def strfdur(param: typing.Union[int, datetime.timedelta, ParsedDuration]):
    dur: ParsedDuration = (
        parse(param) if not isinstance(param, ParsedDuration) else param
    )
    dict_times = {
        incr: getattr(dur, incr + "s")
        for incr in ["year", "week", "day", "hour", "minute", "second"]
    }
    times = [(x[0], int(x[1])) for x in dict_times.items() if x[1]]
    if len(times) > 2:
        fmt = "{}, and {}".format(
            ", ".join(f"{t[1]} {t[0]}{'s' if t[1] != 1 else ''}" for t in times[:-1]),
            f"{times[-1][1]} {times[-1][0]}{'s' if times[-1][0] != 1 else ''}",
        )
    else:
        fmt = " and ".join(f"{t[1]} {t[0]}{'s' if t[1] != 1 else ''}" for t in times)
    return fmt
