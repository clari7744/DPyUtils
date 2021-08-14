import discord, re, asyncio, inspect
from discord.ext import commands
from typing import Iterable, Type, TypeVar, Literal

v2 = discord.version_info >= (2, 0, 0)
from discord.ext.commands.converter import (
    IDConverter,
    MemberConverter,
    UserConverter,
    RoleConverter,
    GuildConverter,
    #    GuildChannelConverter,
    CategoryChannelConverter,
    TextChannelConverter,
    #    ThreadConverter,
    VoiceChannelConverter,
    StageChannelConverter,
    ColorConverter,
    EmojiConverter,
)
from discord.ext.commands.converter import _utils_get, _get_from_guilds  # , TT, CT

if not v2:

    class Thread:
        ...

    d_thread = Thread
else:
    d_thread = discord.Thread
if v2:
    from discord.ext.commands.converter import (
        TT,
        CT,
        GuildChannelConverter,
        ThreadConverter,
    )
else:
    from discord.ext.commands.converter import (
        IDConverter as GuildChannelConverter,
        IDConverter as ThreadConverter,
    )

    CT = TypeVar("CT", bound=discord.abc.GuildChannel)
    TT = TypeVar("TT", bound=d_thread)


from discord.ext.commands.errors import (
    ArgumentParsingError,
    BadArgument,
    BadColorArgument,
    ChannelNotFound,
    MemberNotFound,
    NoPrivateMessage,
    RoleNotFound,
    #    ThreadNotFound,
    UserNotFound,
)

if v2:
    from discord.ext.commands.errors import ThreadNotFound
else:

    class ThreadNotFound(BadArgument):
        def __init__(self, argument):
            self.argument = argument
            super().__init__(f'Thread "{argument}" not found.')


# TODO:: Update GuildChannel converters to reflect new d.py 2.0 streamlined state


class UserNotType(BadArgument):
    def __init__(
        self,
        argument,
        _type: Literal["bot", "human"],
        _class: Literal["Member", "User"],
    ):
        self.argument = argument
        super().__init__(
            'Could not convert "{}" to a {} {}.'.format(argument, _type, _class)
        )


class KillCommand(BadArgument):
    pass


class InvalidPermission(BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f"{argument} is not a valid permission!")


def _m_or_u(iterable):
    if isinstance(iterable[0], discord.Member):
        return "Member"
    if isinstance(iterable[0], discord.User):
        return "User"
    return "???"


def search(
    argument,
    iterable,
    *attrs: str,
    mem_type: Literal["EITHER", "BOT", "HUMAN"] = "EITHER",
    **kwargs,
):
    discrim = kwargs.pop("discriminator", kwargs.pop("discrim", None))
    extra_checks = kwargs.pop("extra_checks", [])
    iterable = tuple(iterable)
    if len(iterable) < 1:
        raise Exception("Iterable is empty.")
    result = None
    checks = [
        lambda x: any([getattr(x, attr, None) == argument for attr in attrs]),
        lambda x: any([getattr(x, attr, None).startswith(argument) for attr in attrs]),
        lambda x: any(
            [
                getattr(x, attr, None).lower().startswith(argument.lower())
                for attr in attrs
            ]
        ),
        lambda x: any([argument in getattr(x, attr, None) for attr in attrs]),
        lambda x: any(
            [argument.lower() in getattr(x, attr, None).lower() for attr in attrs]
        ),
    ]
    checks.extend(extra_checks)
    for check in checks:
        if result:
            break
        result = [x for x in iterable if check(x)]
        if (
            isinstance(iterable[0], (discord.Member, discord.User, discord.ClientUser))
            and result
        ):
            if discrim:
                result = [x for x in result if x.discriminator == discrim]
            if mem_type in ["BOT", "HUMAN"]:
                if mem_type == "BOT":
                    result = [x for x in result if x.bot]
                elif mem_type == "HUMAN":
                    result = [x for x in result if not x.bot]
            else:
                raise ArgumentParsingError(
                    "Oh no! Something's gone wrong with the converter! Please DM 💜Clari#7744 (642416218967375882) the context of what caused this to break."
                )

    if isinstance(iterable[0], (discord.Member, discord.User, discord.ClientUser)):
        if not result:
            if mem_type == "BOT":
                raise UserNotType(argument, "bot", _m_or_u(iterable))
            elif mem_type == "HUMAN":
                raise UserNotType(argument, "human", _m_or_u(iterable))
    if len(result) < 1:
        return None
    if len(result) == 1:
        return result[0]
    return result


async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, KillCommand):
        await ctx.channel.send(str(error), delete_after=5)
    else:
        await ctx.bot.converters_original_on_command_error(ctx, error)


async def result_handler(ctx: commands.Context, result, argument):
    if not hasattr(ctx.bot, "converters_original_on_command_error"):
        ctx.bot.converters_original_on_command_error = ctx.bot.on_command_error
        ctx.bot.on_command_error = on_command_error
    if len(result) == 1:
        return result[0]
    if len(result) < 1:
        raise BadArgument(
            "Your argument was invalid and somehow made it all the way to the multiple-result handler, please DM 💜Clari#7744 (642416218967375882) and provide the context that caused this to happen."
        )
    if len(result) > 20:
        raise KillCommand(
            f"Too many matches found for your search `{argument}`. Please refine your search and try again."
        )
    matchlist = "\n".join(
        [
            f"**{i+1}.** {v.mention if not isinstance(v, (discord.User, discord.Member, discord.Color, discord.CategoryChannel)) else v} (`{v.id}`){f' (`{v.category}`)' if getattr(v, 'category', None) else ''}"
            for i, v in enumerate(result)
        ]
    )
    t = (
        re.match(r"<class 'discord\..+?\.(.+?)'>", str(type(result[0])))
        .group(1)
        .lower()
        .replace("chan", " chan")
    )
    todel = await ctx.channel.send(
        f"There were multiple matches for your search `{argument}`. Please send the number of the correct {t} below, or `cancel` this command and refine your search.\n\n{matchlist}",
        delete_after=22,
        allowed_mentions=discord.AllowedMentions().none(),
    )
    try:
        msg = await ctx.bot.wait_for(
            "message",
            timeout=20,
            check=lambda m: (m.content.isdigit() or m.content.lower() in ["cancel"])
            and m.author == ctx.author
            and m.channel == ctx.channel,
        )
    except asyncio.TimeoutError:
        raise KillCommand(f"Canceled command due to timeout.")
    finally:
        try:
            await msg.delete()
            await todel.delete()
        except:
            pass
    if msg.content.lower() in ["cancel"]:
        raise KillCommand("Canceled command.")
    try:
        num = int(msg.content)
    except:
        raise KillCommand(f"`{msg.content}` is not a number. Canceled command.")
    if num > len(result) or num == 0:
        raise KillCommand(
            f"`{num}` {'is too big' if num != 0 else 'cannot be zero'}. Canceled command."
        )
    result = result[num - 1]
    return result


async def check_bot(
    argument,
    result,
    error,
    mem_type: Literal["EITHER", "MEMBER", "BOT"] = "EITHER",
):
    if mem_type == "EITHER":
        return result
    if mem_type == "BOT":
        if not getattr(result, "bot", False):
            raise UserNotType(argument, "bot", error)
        return result
    elif mem_type == "HUMAN":
        if getattr(result, "bot", True):
            raise UserNotType(argument, "human", error)
        return result
    return result


class Member(MemberConverter, discord.Member):
    """
    Custom converter to allow for looser searching, inherits from commands.MemberConverter
    """

    mem_type: Literal["EITHER", "MEMBER", "BOT"] = "EITHER"

    @staticmethod
    async def query_member_named(guild: discord.Guild, argument, mem_type="EITHER"):
        if not guild.chunked:
            await guild.chunk()
        result = None
        if len(argument) > 5 and argument[-5] == "#":
            username, _, discriminator = argument.rpartition("#")
            result = search(
                username,
                guild.members,
                "name",
                "display_name",
                discrim=discriminator,
                mem_type=mem_type,
            )
        else:
            #            members = await guild.query_members(argument, limit=100, cache=cache)
            result = search(
                argument, guild.members, "name", "display_name", mem_type=mem_type
            )
        return result

    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument: str  # , *, mem_type="EITHER"
    ) -> discord.Member:
        bot = ctx.bot
        mem_type = cls.mem_type
        match = IDConverter._get_id_match(argument) or re.match(
            r"<@!?([0-9]{15,20})>$", argument
        )
        guild = ctx.guild
        result = None
        user_id = None
        if match is None:
            # not a mention...
            if guild:
                if len(argument) > 5 and argument[-5] == "#":
                    potential_discriminator = argument[-4:]
                    result = search(
                        argument[:-5],
                        guild.members,
                        "name",
                        "display_name",
                        discrim=potential_discriminator,
                        mem_type=mem_type,
                    )
            else:
                result = _get_from_guilds(bot, "get_member_named", argument)
        else:
            user_id = int(match.group(1))
            if guild:
                result = guild.get_member(user_id) or _utils_get(
                    ctx.message.mentions, id=user_id
                )
            else:
                result = _get_from_guilds(bot, "get_member", user_id)
        if result is None:
            if guild is None:
                raise MemberNotFound(argument)
            if user_id is not None:
                result = await MemberConverter().query_member_by_id(bot, guild, user_id)
            else:
                result = await cls.query_member_named(guild, argument)
            if not result:
                raise MemberNotFound(argument)
        if isinstance(result, discord.Member):
            return await check_bot(argument, result, "Member", mem_type=mem_type)
        return await result_handler(ctx, result, argument)


class BotMember(Member):
    mem_type = "BOT"


#    @classmethod
#    async def convert(cls, ctx: commands.Context, argument):
#        return await Member.convert(ctx, argument, mem_type="BOT")


class HumanMember(Member):
    mem_type = "HUMAN"


#    @classmethod
#    async def convert(cls, ctx: commands.Context, argument):
#        return await Member.convert(ctx, argument, mem_type="HUMAN")


class User(UserConverter, discord.User):
    """
    Custom converter to allow for looser searching, inherits from commands.UserConverter
    """

    mem_type: Literal["EITHER", "MEMBER", "BOT"] = "EITHER"

    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument  # , *, mem_type="EITHER"
    ) -> discord.User:
        bot = ctx.bot
        mem_type = cls.mem_type
        match = cls._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        result = None
        if match is not None:
            user_id = int(match.group(1))
            result = bot.get_user(user_id) or _utils_get(
                ctx.message.mentions, id=user_id
            )
            if result is None:
                try:
                    result = await bot.fetch_user(user_id)
                except discord.HTTPException:
                    raise UserNotFound(argument) from None
            return await check_bot(argument, result, "User", mem_type=mem_type)
        arg = argument
        # Remove the '@' character if this is the first character from the argument
        if arg[0] == "@":
            # Remove first character
            arg = arg[1:]
        # check for discriminator if it exists,
        if len(arg) > 5 and arg[-5] == "#":
            discrim = arg[-4:]
            name = arg[:-5]  # pylint: disable=unused-variable
            result = search(
                argument,
                tuple(bot.users),
                "name",
                discrim=discrim,
                mem_type=mem_type,
            )
            if result is not None:
                if isinstance(result, (discord.User, discord.ClientUser)):
                    return await check_bot(argument, result, "User", mem_type=mem_type)
                return await result_handler(ctx, result, argument)
        result = search(argument, tuple(bot.users), "name", mem_type=mem_type)
        if result is None:
            raise UserNotFound(argument)
        if isinstance(result, (discord.User, discord.ClientUser)):
            return await check_bot(argument, result, "User", mem_type=mem_type)
        return await result_handler(ctx, result, argument)


class BotUser(User):
    mem_type = "BOT"


#    @classmethod
#    async def convert(cls, ctx: commands.Context, argument):
#        return await User.convert(ctx, argument, mem_type="BOT")


class HumanUser(User):
    mem_type = "HUMAN"


#    @classmethod
#    async def convert(cls, ctx: commands.Context, argument):
#        return await User.convert(ctx, argument, mem_type="HUMAN")


class Role(RoleConverter, discord.Role):
    """
    Custom converter to allow for looser searching, inherits from commands.RoleConverter
    """

    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()
        match = cls._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = search(argument, tuple(guild.roles), "name")
        if result is None:
            raise RoleNotFound(argument)
        if isinstance(result, discord.Role):
            return result
        return await result_handler(ctx, result, argument)


class Color(ColorConverter, discord.Color):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        try:
            int_arg = int(argument)
            return discord.Color(int_arg)
        except:
            pass
        if argument[0] == "#":
            return self.parse_hex_number(argument[1:])
        if argument[0:2] == "0x":
            rest = argument[2:]
            # Legacy backwards compatible syntax
            if rest.startswith("#"):
                return self.parse_hex_number(rest[1:])
            return self.parse_hex_number(rest)
        arg = argument.lower()
        if arg[0:3] == "rgb":
            return self.parse_rgb(arg)
        arg = arg.replace(" ", "_")
        try:
            return self.parse_hex_number(argument)
        except:
            pass
        method = getattr(discord.Colour, arg, None)
        if arg.startswith("from_") or method is None or not inspect.ismethod(method):
            raise BadColorArgument(arg)
        return method()


class Emoji(EmojiConverter):
    async def convert(self, ctx: commands.Context, argument):
        # https://gist.github.com/Phxntxm/a91e0cfadb19b2071554d59edcd1df6c
        return await super().convert(ctx, argument)


class Guild(GuildConverter):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument)


def get_all(bot, thing):
    def _get_all(self):
        for guild in self.guilds:
            for channel in getattr(guild, thing):
                yield channel

    if not getattr(bot, f"get_all_{thing}", False):
        setattr(bot, f"get_all_{thing}", _get_all)


class GuildChannel(GuildChannelConverter):
    @staticmethod
    async def _resolve_channel(
        ctx: commands.Context,
        argument: str,
        attribute: str,
        _type: Type[CT],
        *,
        news=False,
    ):
        bot = ctx.bot
        for t in "categories text_channels voice_chanmels stage_channels".split():
            get_all(bot, t)
        match = IDConverter._get_id_match(argument) or re.match(
            r"<#([0-9]{15,20})>$", argument
        )
        result = None
        guild = ctx.guild
        if match is None:
            # not a mention
            if guild:
                iterable: Iterable[CT] = getattr(guild, attribute)
                result = search(argument, iterable, "name")
            else:
                result = search(
                    argument,
                    getattr(bot, f"get_all_{attribute}", bot.get_all_channels)(),
                    "name",
                )
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, "get_channel", channel_id)
            if not isinstance(result, _type):
                raise ChannelNotFound(argument)
        if result is None:
            raise ChannelNotFound(argument)
        if isinstance(result, discord.TextChannel):
            if news and not result.is_news():
                raise ChannelNotFound(argument)
            return result
        if news:
            result = [c for c in result if c.is_news()]
        if isinstance(result, _type):
            return result
        return await result_handler(ctx, result, argument)

    @staticmethod
    async def _resolve_thread(
        ctx: commands.Context, argument: str, attribute: str, _type: Type[TT]
    ):
        bot = ctx.bot
        get_all(bot, "threads")
        match = IDConverter._get_id_match(argument) or re.match(
            r"<#([0-9]{15,20})>$", argument
        )
        result = None
        guild = ctx.guild
        if match is None:
            # not a mention
            if guild:
                iterable: Iterable[TT] = getattr(guild, attribute)
                result = search(argument, iterable, "name")
            else:
                result = search(
                    argument,
                    getattr(bot, f"get_all_{attribute}", bot.get_all_channels)(),
                    "name",
                )
        else:
            thread_id = int(match.group(1))
            if guild:
                result = guild.get_thread(thread_id)
            if not isinstance(result, _type):
                raise ThreadNotFound(argument)
        if result is None or not isinstance(result, _type):
            raise ThreadNotFound(argument)

        return await result_handler(ctx, result, argument)


class CategoryChannel(CategoryChannelConverter, discord.CategoryChannel):
    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument: str
    ) -> discord.CategoryChannel:
        return await GuildChannel._resolve_channel(
            ctx, argument, "categories", discord.CategoryChannel
        )


class TextChannel(TextChannelConverter, discord.TextChannel):
    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument: str
    ) -> discord.CategoryChannel:
        return await GuildChannel._resolve_channel(
            ctx, argument, "text_channels", discord.TextChannel
        )


class NewsChannel(TextChannelConverter, discord.TextChannel):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> discord.TextChannel:
        return await GuildChannel._resolve_channel(
            ctx, argument, "text_channels", discord.TextChannel, news=True
        )


class VoiceChannel(VoiceChannelConverter, discord.VoiceChannel):
    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument: str
    ) -> discord.VoiceChannel:
        return await GuildChannel._resolve_channel(
            ctx, argument, "voice_channels", discord.VoiceChannel
        )


class StageChannel(StageChannelConverter, discord.StageChannel):
    @classmethod
    async def convert(
        cls, ctx: commands.Context, argument: str
    ) -> discord.StageChannel:
        return await GuildChannel._resolve_channel(
            ctx, argument, "stage_channels", discord.StageChannel
        )


class Thread(ThreadConverter, d_thread):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> d_thread:
        if not v2:
            raise commands.CheckFailure("Sorry, you can't use this until v2")
        return await GuildChannel._resolve_thread(ctx, argument, "threads", d_thread)


class AnyChannelBase(commands.Converter):
    converters: list

    @classmethod
    async def convert(cls, ctx: commands.Context, argument, converters=[]):
        converters = converters or cls.converters
        print(cls.converters)
        result = None
        for converter in converters:
            if result:
                break
            try:
                result = await converter().convert(ctx, argument)
            except:
                continue
        if not result:
            raise ChannelNotFound(argument)
        return result


class AnyChannel(AnyChannelBase):
    converters = [
        CategoryChannel,
        TextChannel,
        VoiceChannel,
        StageChannel,
        Thread,
    ]


class NonCategoryChannel(AnyChannelBase):
    converters = [TextChannel, VoiceChannel, StageChannel, Thread]


class IgnoreCaseLiteral(commands.Converter):
    def __class_getitem__(self, *parameters):
        self.parameters = tuple(str(param).lower() for param in parameters)
        return self

    async def convert(self, ctx: commands.Context, argument):
        if str(argument).lower() not in self.parameters:
            raise commands.BadArgument(
                f"{argument} is not a valid option!\nOptions: {', '.join(self.parameters)}"
            )
        return argument


class Permissions(commands.Converter, discord.Permissions):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument) -> discord.Permissions:
        if argument.isdigit() and int(argument) < discord.Permissions.all().value:
            return discord.Permissions(int(argument))
        perms = argument.replace("server", "guild").lower().split()
        perm = discord.Permissions()
        for p in perms:
            try:
                setattr(perm, p, True)
            except:
                raise InvalidPermission(p)
        return perm
