import datetime
import re
from collections import namedtuple
from typing import Union

from discord.ext import commands

from .utils import _and, s

ParsedDuration = namedtuple(
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
        super().__init__("'{}' is an invalid format for time! Format must be '1y1w1d1h1m1s'.".format(argument))


class Duration:
    def __init__(self, original: str = "0", seconds: int = 0):
        try:
            seconds = int(seconds)
        except:
            raise TypeError("Seconds must be an integer.")  # pylint: disable=raise-missing-from
        self._original = str(original)
        self._seconds = int(seconds)

    def __str__(self):
        return self._original

    def __int__(self):
        return self._seconds

    def __bool__(self):
        return bool(self._seconds)

    def __iter__(self):
        yield from (self._original, self._seconds)

    def __gt__(self, other):
        return int(self) > int(other)

    def __ge__(self, other):
        return int(self) >= int(other)

    def __lt__(self, other):
        return int(self) < int(other)

    def __le__(self, other):
        return int(self) <= int(other)

    def __eq__(self, other):
        return int(self) == int(other)

    @property
    def original(self) -> str:
        """
        Returns the original argument passed to the duration converter.
        """
        return self._original

    @property
    def seconds(self) -> int:
        """
        Returns the amount of seconds that the duration passed in was converted to.
        """
        return self._seconds

    # TODO: Create a docstring for this class
    @classmethod
    async def convert(cls, ctx, argument):  # pylint: disable=unused-argument
        try:
            return cls(argument, int(argument))
        except:  # pylint:disable=bare-except
            pass
        seconds = 0
        match = re.findall(r"([0-9]+?(?:\.[0-9]+)?[ywdhms])", argument)
        if not match:
            raise InvalidTimeFormat(argument)
        for item in match:
            seconds += float(item[:-1]) * durations[item[-1]]
        return cls(argument, round(seconds))


def parse(param: Union[int, Duration, datetime.timedelta]) -> ParsedDuration:
    """
    This function takes an int or timedelta parameter of seconds and formats it, returning a named tuple ParsedDuration that has years, weeks, days, hours, minutes and seconds. It also includes the total_seconds, the input.
    """
    parsed = {}
    seconds = param.total_seconds() if isinstance(param, datetime.timedelta) else int(param)
    ts = int(seconds)
    for unit, sec in durations.items():
        parsed[unit], seconds = divmod(seconds, sec)
        parsed[unit] = int(parsed[unit])
    return ParsedDuration(
        years=parsed["y"],
        weeks=parsed["w"],
        days=parsed["d"],
        hours=parsed["h"],
        minutes=parsed["m"],
        seconds=parsed["s"],
        total_seconds=ts,
    )


def strfdur(
    param: Union[int, Duration, ParsedDuration, datetime.timedelta],
    *,
    compact: bool = False,
    letter: bool = False,
) -> str:
    dur: ParsedDuration = parse(param) if not isinstance(param, ParsedDuration) else param
    dict_times = {incr: getattr(dur, incr + "s") for incr in ["year", "week", "day", "hour", "minute", "second"]}
    times = [(k, int(v)) for k, v in dict_times.items() if v or (k not in ("year", "week") and compact)]

    def _fmt(unit, val):
        if compact:
            return str(val).zfill(2)
        if letter:
            return f"{val}{unit[0]}"
        return f"{val} {unit}{s(val)}"

    if compact:
        if any(t[0] in ("year", "week") for t in times):
            raise TypeError("Compact cannot be used with times greater than 7 days")
        for i, t in enumerate(times):
            if not t[1]:
                continue
            times = times[i:]
            break
        if len(times) == 1 and times[0][0] == "second":
            fmt = f"0:{_fmt(*times[0])}"
        else:
            fmt = ":".join(_fmt(*t) for t in times)
    else:
        fmt = _and(*(_fmt(*t) for t in times))
    #    elif len(times) > 2:
    #        fmt = f"{', '.join(_fmt(*t) for t in times[:-1])}, and {_fmt(*times[-1])}"
    #    else:
    #        fmt = " and ".join(_fmt(*t) for t in times)
    return fmt
