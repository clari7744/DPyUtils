import discord
from discord.ext import commands
from dataclasses import dataclass
from discord.utils import MISSING
from typing import Any, Dict, List, Optional


class FlagIsSwitch(commands.FlagError):
    def __init__(self, flag):
        self.flag = flag
        super().__init__(f"Flag {flag.name!r} is a switch! (Accepts no arguments.)")


@dataclass
class Flag(commands.Flag):
    """Represents a flag parameter for :class:`FlagConverter`.

    The :func:`~discord.ext.commands.flag` function helps
    create these flag objects, but it is not necessary to
    do so. These cannot be constructed manually.

    Attributes
    ------------
    name: :class:`str`
        The name of the flag.
    aliases: List[:class:`str`]
        The aliases of the flag name.
    attribute: :class:`str`
        The attribute in the class that corresponds to this flag.
    default: Any
        The default value of the flag, if available.
    annotation: Any
        The underlying evaluated annotation of the flag.
    max_args: :class:`int`
        The maximum number of arguments the flag can accept.
        A negative value indicates an unlimited amount of arguments.
    override: :class:`bool`
        Whether multiple given values overrides the previous value.
    switch: :class:`str`
        Whether flag will accept an argument or not. Defaults to true, if false then will raise an error if an argument is passed.
    """

    switch: bool = False


def flag(
    *,
    name: str = MISSING,
    aliases: List[str] = MISSING,
    default: Any = MISSING,
    max_args: int = MISSING,
    override: bool = MISSING,
    switch: bool = False,
) -> Any:
    """Override default functionality and parameters of the underlying :class:`FlagConverter`
    class attributes.

    Parameters
    ------------
    name: :class:`str`
        The flag name. If not given, defaults to the attribute name.
    aliases: List[:class:`str`]
        Aliases to the flag name. If not given no aliases are set.
    default: Any
        The default parameter. This could be either a value or a callable that takes
        :class:`Context` as its sole parameter. If not given then it defaults to
        the default value given to the attribute.
    max_args: :class:`int`
        The maximum number of arguments the flag can accept.
        A negative value indicates an unlimited amount of arguments.
        The default value depends on the annotation given.
    override: :class:`bool`
        Whether multiple given values overrides the previous value. The default
        value depends on the annotation given.
    switch: :class:`str`
        Whether flag will accept an argument or not. Defaults to true, if false then will raise an error if an argument is passed.
    """
    return Flag(
        name=name,
        aliases=aliases,
        default=default,
        max_args=max_args,
        override=override,
        switch=switch,
    )


class FlagConverter(
    commands.FlagConverter,
    metaclass=commands.flags.FlagsMeta,
    case_insensitive=True,
    prefix="-",
    delimiter=" ",
):
    __commands_flag_prefix__ = "-"
    __commands_flag_delimiter__ = " "

    def _switch(flag: Flag):
        return getattr(flag, "switch", False) and flag.annotation == bool

    @classmethod
    def parse_flags(cls, argument: str) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        flags = cls.__commands_flags__  # pylint: disable=no-member
        aliases = cls.__commands_flag_aliases__  # pylint: disable=no-member
        prefix = cls.__commands_flag_prefix__  # pylint: disable=no-member
        delim = cls.__commands_flag_delimiter__  # pylint: disable=no-member
        last_position = 0
        last_flag: Optional[Flag] = None

        case_insensitive = (
            cls.__commands_flag_case_insensitive__
        )  # pylint: disable=no-member
        for match in cls.__commands_flag_regex__.finditer(
            argument
        ):  # pylint: disable=no-member
            begin, end = match.span(0)
            key = match.group("flag")
            if case_insensitive:
                key = key.casefold()

            if key in aliases:
                key = aliases[key]

            flag = flags.get(key)
            if last_position and last_flag is not None:
                value = argument[last_position : begin - 1].lstrip()
                if cls._switch(last_flag):
                    if value:
                        if not commands.converter._convert_to_bool(value):
                            raise FlagIsSwitch(last_flag)
                        result[last_flag.name] = [value]
                    else:
                        if (
                            not bool(last_flag.default)
                            or flag.default is discord.utils.MISSING
                        ):
                            result[last_flag.name] = ["True"]
                        else:
                            result[last_flag.name] = ["False"]
                    last_position = end
                    last_flag = flag
                    continue
                if not value:
                    raise commands.MissingFlagArgument(last_flag)
                try:
                    values = result[last_flag.name]
                except KeyError:
                    result[last_flag.name] = [value]
                else:
                    values.append(value)
            last_position = end
            last_flag = flag

        # Add the remaining string to the last available flag
        if last_position and last_flag is not None:
            value = argument[last_position:].strip()
            if cls._switch(last_flag):
                if value:
                    if not commands.converter._convert_to_bool(value):
                        raise FlagIsSwitch(last_flag)
                    result[last_flag.name] = ["True"]
                result[last_flag.name] = ["True"]
                return result

            if not value:
                raise MissingFlagArgument(last_flag)
            try:
                values = result[last_flag.name]
            except KeyError:
                result[last_flag.name] = [value]
            else:
                values.append(value)

        # Verification of values will come at a later stage
        return result
