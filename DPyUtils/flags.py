import re

import discord
from discord.ext import commands

if not discord.version_info >= (2, 0, 0):
    raise TypeError("Sorry, this can only be used in v2")
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from discord.utils import MISSING


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
    switch: :class:`bool`
        Whether flag will accept an argument or not. Defaults to true, if false then will raise an error if an argument is passed.
    description: :class:`str`
        A meta flag description, used in signatures.
    """

    switch: bool = False
    description: str = MISSING


def flag(
    *,
    name: str = MISSING,
    aliases: List[str] = MISSING,
    default: Any = MISSING,
    max_args: int = MISSING,
    override: bool = MISSING,
    switch: bool = False,
    description: str = MISSING,
    annotation: Any = MISSING,
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
    description: :class:`str`
        A meta flag description, used in signatures.
    annotation: Any
        The underlying evaluated annotation of the flag.
    """
    if switch and default is MISSING:
        default = False
    return Flag(
        name=name,
        aliases=aliases,
        default=default,
        max_args=max_args,
        override=override,
        switch=switch,
        description=description,
        annotation=annotation,
    )


class FlagConverter(
    commands.FlagConverter,
    metaclass=commands.flags.FlagsMeta,
    case_insensitive=True,
    prefix="-",
    delimiter=" ",
):
    @classmethod
    def _switch(cls, flag: Flag):
        return getattr(flag, "switch", False) and flag.annotation == bool

    @classmethod
    def parse_flags(cls, argument: str, *, ignore_extra: bool = True) -> Dict[str, List[str]]:
        # pylint: disable=no-member;
        result: Dict[str, List[str]] = {}
        flags = cls.__commands_flags__
        aliases = cls.__commands_flag_aliases__
        prefix = cls.__commands_flag_prefix__
        delim = cls.__commands_flag_delimiter__
        last_position = 0
        last_flag: Optional[Flag] = None

        case_insensitive = cls.__commands_flag_case_insensitive__
        prereg = cls.__commands_flag_regex__
        if delim == " ":
            regex = cls.__commands_flag_regex__ = re.compile(
                prereg.pattern.replace(f"){re.escape(delim)})", rf")({re.escape(delim)}|\Z))"),
                prereg.flags,
            )
        else:
            regex = prereg
        for match in regex.finditer(argument):
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
                        if not bool(last_flag.default):
                            result[last_flag.name] = ["True"]
                        else:
                            result[last_flag.name] = ["False"]
                    last_position = end
                    last_flag = flag
                    continue
                if not value:
                    raise commands.MissingFlagArgument(last_flag)
                name = last_flag.name.casefold() if case_insensitive else last_flag.name
                try:
                    values = result[name]
                except KeyError:
                    result[name] = [value]
                else:
                    values.append(value)
            last_position = end
            last_flag = flag

        # Get the remaining string, if applicable
        value = argument[last_position:].strip()

        # Add the remaining string to the last available flag
        if last_flag is not None:
            if cls._switch(last_flag):
                if value:
                    if not commands.converter._convert_to_bool(value):
                        raise FlagIsSwitch(last_flag)
                    result[last_flag.name] = ["True"]
                result[last_flag.name] = ["True"]
                return result

            if not value:
                raise commands.MissingFlagArgument(last_flag)
            name = last_flag.name.casefold() if case_insensitive else last_flag.name

            try:
                values = result[name]
            except KeyError:
                result[name] = [value]
            else:
                values.append(value)
        elif value and not ignore_extra:
            # If we're here then we passed extra arguments that aren't flags
            raise commands.TooManyArguments(f"Too many arguments passed to {cls.__name__}")

        # Verification of values will come at a later stage
        return result

    @classmethod
    def get_flag_signature(cls) -> str:
        flags = list(cls.get_flags().values())
        prefix = cls.__commands_flag_prefix__
        delim = cls.__commands_flag_delimiter__

        def format_flag(flag: Flag):
            name = flag.name if not flag.aliases else f"[{'|'.join((flag.name,*flag.aliases))}]"
            annotation = flag.annotation.__name__ if not getattr(flag, "switch", None) else "Switch"
            default = (
                f'="{flag.default}"'
                if isinstance(flag.default, str)
                else f"={flag.default}"
                if not flag.required
                else ""
            )
            description = f"\n\t{flag.description}" if flag.description is not MISSING else ""

            sig = prefix + name + delim + annotation + default
            sig = sig if flag.required else f"[{sig}]"
            return sig + description

        return "\n".join(map(format_flag, flags))


# Turns out this is useless and doesn't work, to debug later
# For now use `flags=` kwarg in command decorator (only works in clari7744's fork of DPy, maybe this function works in Rapptz?)
# def addflags(flags: commands.FlagConverter):
#    """
#    Decorator to add flags to a command's attributes to be used later (mostly by the help command).
#    """
#    if not issubclass(flags, commands.FlagConverter):
#        raise TypeError(f"{flags} must be a subclass of `DPyUtils.FlagConverter`.")

#    def deco(func):
#        if isinstance(func, commands.Command):
#            func.flags = flags
#        else:
#            func.__flags__ = flags
#        return func

#    return deco


def get_flag_signature(flagclass: FlagConverter):
    if not isinstance(flagclass, FlagConverter):
        raise TypeError(f"{flagclass} must be a subclass of `DPyUtils.FlagConverter`.")
    return flagclass.get_flag_signature()
