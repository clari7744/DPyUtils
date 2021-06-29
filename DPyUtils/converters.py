import discord, re, asyncio, inspect
from discord.ext import commands
from discord.ext.commands import (
    MemberConverter,
    UserConverter,
    RoleConverter,
    ColorConverter,
    EmojiConverter,
    GuildConverter,
    CategoryChannelConverter,
    TextChannelConverter,
    VoiceChannelConverter,
    StageChannelConverter,
)
from discord.ext.commands.converter import _utils_get
from discord.ext.commands.errors import *


class MemberNotHuman(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Could not convert "{}" to a human Member.'.format(argument))


class UserNotHuman(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Could not convert "{}" to a human User.'.format(argument))


class MemberNotBot(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Could not convert "{}" to a bot Member.'.format(argument))


class UserNotBot(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__('Could not convert "{}" to a bot User.'.format(argument))


def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result


def search(argument, iterable, *attrs: str, mem_type="EITHER", **kwargs):
    discrim = kwargs.pop("discrim", None)
    discrim = kwargs.pop("discriminator", discrim)
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
    for check in checks:
        if result:
            break
        result = [x for x in iterable if check(x)]
        if (
            isinstance(iterable[0], (discord.Member, discord.User, discord.ClientUser))
            and discrim
            and result
        ):
            result = [x for x in result if x.discriminator == discrim] or []
        if (
            isinstance(iterable[0], (discord.Member, discord.User, discord.ClientUser))
            and result
            and mem_type != "EITHER"
        ):
            if mem_type == "BOT":
                result = [x for x in result if x.bot]
                if not result:
                    raise (
                        MemberNotBot(argument)
                        if isinstance(iterable[0], discord.Member)
                        else UserNotBot(argument)
                    )
            elif mem_type == "HUMAN":
                result = [x for x in result if not x.bot]
                if not result:
                    raise (
                        MemberNotHuman(argument)
                        if isinstance(iterable[0], discord.Member)
                        else UserNotHuman(argument)
                    )
            else:
                raise commands.ArgumentParsingError(
                    "Oh no! Something's gone wrong with the converter! Please DM 💜Clari#7744 (642416218967375882) the context of what caused this to break."
                )
    if len(result) < 1:
        return None
    if len(result) == 1:
        return result[0]
    return result


class KillCommand(BadArgument):
    pass


async def on_command_error(ctx, error):
    if isinstance(error, KillCommand):
        await ctx.send(str(error), no_save=True, delete_after=5)
    else:
        await ctx.bot.converters_original_on_command_error(ctx, error)


async def result_handler(ctx, result, argument):
    if not hasattr(ctx.bot, "converters_original_on_command_error"):
        ctx.bot.converters_original_on_command_error = ctx.bot.on_command_error
        ctx.bot.on_command_error = on_command_error
    if len(result) == 1:
        return result[0]
    if len(result) < 1:
        raise commands.BadArgument(
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
        re.match("<class 'discord\..+?\.(.+?)'>", str(type(result[0])))
        .group(1)
        .lower()
        .replace("chan", " chan")
    )
    todel = await ctx.send(
        f"There were multiple matches for your search `{argument}`. Please send the number of the correct {t} below, or `cancel` this command and refine your search.\n\n{matchlist}",
        no_save=True,
        delete_after=22,
        allowed_mentions=discord.AllowedMentions().none(),
    )
    try:
        msg = await ctx.bot.wait_for(
            "message",
            timeout=20,
            check=lambda m: (
                re.match("\d+", m.content) or m.content.lower() == "cancel"
            )
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
    if msg.content.lower() == "cancel":
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


async def check_bot(argument, result, error, mem_type="EITHER"):
    if mem_type == "EITHER":
        return result
    if not getattr(result, "bot", False) and mem_type == "BOT":
        raise (MemberNotBot(argument) if error == "Member" else UserNotBot(argument))
    if getattr(result, "bot", True) and mem_type == "HUMAN":
        raise (
            MemberNotHuman(argument) if error == "Member" else UserNotHuman(argument)
        )
    return result


class Member(MemberConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.MemberConverter
    """

    async def query_member_named(
        self, guild: discord.Guild, argument, mem_type="EITHER"
    ):
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

    async def convert(
        self, ctx: commands.Context, argument: str, *, mem_type="EITHER"
    ) -> discord.Member:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(
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
                result = await self.query_member_by_id(bot, guild, user_id)
            else:
                result = await self.query_member_named(guild, argument)
            if not result:
                raise MemberNotFound(argument)
        if isinstance(result, discord.Member):
            return await check_bot(argument, result, "Member", mem_type=mem_type)
        return await result_handler(ctx, result, argument)


class BotMember(Member):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument, mem_type="BOT")


class HumanMember(Member):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument, mem_type="HUMAN")


class User(UserConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.UserConverter
    """

    async def convert(
        self, ctx: commands.Context, argument, *, mem_type="EITHER"
    ) -> discord.User:
        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        result = None
        state = ctx._state
        if match is not None:
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id) or _utils_get(
                ctx.message.mentions, id=user_id
            )
            if result is None:
                try:
                    result = await ctx.bot.fetch_user(user_id)
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
            name = arg[:-5]
            result = search(
                argument,
                tuple(ctx.bot.users),
                "name",
                discrim=discrim,
                mem_type=mem_type,
            )
            if result is not None:
                if isinstance(result, (discord.User, discord.ClientUser)):
                    return await check_bot(argument, result, "User", mem_type=mem_type)
                return await result_handler(ctx, result, argument)
        result = search(argument, tuple(ctx.bot.users), "name", mem_type=mem_type)
        if result is None:
            raise UserNotFound(argument)
        if isinstance(result, (discord.User, discord.ClientUser)):
            return await check_bot(argument, result, "User", mem_type=mem_type)
        return await result_handler(ctx, result, argument)


class BotUser(User):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument, mem_type="BOT")


class HumanUser(User):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument, mem_type="HUMAN")


class Role(RoleConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.RoleConverter
    """

    async def convert(self, ctx: commands.Context, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()
        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = search(argument, tuple(guild.roles), "name")
        if result is None:
            raise RoleNotFound(argument)
        if isinstance(result, discord.Role):
            return result
        return await result_handler(ctx, result, argument)


class Color(ColorConverter):
    async def convert(self, ctx: commands.Context, argument):
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
            raise BadColourArgument(arg)
        return method()


class Emoji(EmojiConverter):
    async def convert(self, ctx: commands.Context, argument):
        # https://gist.github.com/Phxntxm/a91e0cfadb19b2071554d59edcd1df6c
        return await super().convert(ctx, argument)


class Guild(GuildConverter):
    async def convert(self, ctx: commands.Context, argument):
        return await super().convert(ctx, argument)


class CategoryChannel(CategoryChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.CategoryChannelConverter
    """

    def get_all_categories(self):
        for guild in self.guilds:
            for channel in guild.categories:
                yield channel

    async def convert(self, ctx: commands.Context, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
        bot.get_all_categories = self.get_all_categories
        if match is None:
            # not a mention
            if guild:
                result = search(argument, guild.categories, "name")
            else:
                result = search(argument, bot.get_all_categories(), "name")
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, "get_channel", channel_id)
            if not isinstance(result, discord.CategoryChannel):
                raise ChannelNotFound(argument)
        if result is None:
            raise ChannelNotFound(argument)
        if isinstance(result, discord.CategoryChannel):
            return result
        return await result_handler(ctx, result, argument)


class TextChannel(TextChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.TextChannelConverter
    """

    def get_all_text_channels(self):
        for guild in self.guilds:
            for channel in guild.text_channels:
                yield channel

    async def convert(
        self, ctx: commands.Context, argument, *, news=False
    ) -> discord.TextChannel:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
        bot.get_all_text_channels = self.get_all_text_channels
        if match is None:
            # not a mention
            if guild:
                result = search(argument, guild.text_channels, "name")
            else:
                result = search(argument, bot.get_all_text_channels(), "name")
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, "get_channel", channel_id)
            if not isinstance(result, discord.TextChannel):
                raise ChannelNotFound(argument)
        if result is None:
            raise ChannelNotFound(argument)
        if isinstance(result, discord.TextChannel):
            if news and not result.is_news():
                raise ChannelNotFound(argument)
            return result
        if news:
            result = [c for c in result if c.is_news()]
        if len(result) == 1:
            return result
        if not result:
            raise ChannelNotFound(argument)
        return await result_handler(ctx, result, argument)


class NewsChannel(TextChannel):
    """
    Custom news channel converter, literally just searches for text channels and then checks if it's news.
    """

    async def convert(self, ctx, argument) -> discord.TextChannel:
        return await super().convert(
            ctx, argument, news=True
        )  # Get matching text channels


class VoiceChannel(VoiceChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.VoiceChannelConverter
    """

    def get_all_voice_channels(self):
        for guild in self.guilds:
            for channel in guild.voice_channels:
                yield channel

    async def convert(self, ctx: commands.Context, argument) -> discord.VoiceChannel:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
        bot.get_all_voice_channels = self.get_all_voice_channels
        if match is None:
            # not a mention
            if guild:
                result = search(argument, guild.voice_channels, "name")
            else:
                result = search(argument, bot.get_all_voice_channels(), "name")
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, "get_channel", channel_id)
            if not isinstance(result, discord.VoiceChannel):
                raise ChannelNotFound(argument)
        if result is None:
            raise ChannelNotFound(argument)
        if isinstance(result, discord.VoiceChannel):
            return result
        return await result_handler(ctx, result, argument)


class StageChannel(StageChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.StageChannelConverter
    """

    def get_all_stage_channels(self):
        for guild in self.guilds:
            for channel in guild.stage_channels:
                yield channel

    async def convert(self, ctx: commands.Context, argument) -> discord.StageChannel:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
        bot.get_all_stage_channels = self.get_all_stage_channels
        if match is None:
            # not a mention
            if guild:
                result = search(argument, guild.stage_channels, "name")
            else:
                result = search(argument, bot.get_all_stage_channels(), "name")
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, "get_channel", channel_id)
            if not isinstance(result, discord.StageChannel):
                raise ChannelNotFound(argument)
        if result is None:
            raise ChannelNotFound(argument)
        if isinstance(result, discord.StageChannel):
            return result
        return await result_handler(ctx, result, argument)


class AnyChannelBase(commands.Converter):
    async def convert(self, ctx: commands.Context, argument, converters):
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
    async def convert(self, ctx: commands.Context, argument):
        converters = [
            CategoryChannel,
            TextChannel,
            NewsChannel,
            VoiceChannel,
            StageChannel,
        ]
        return await super().convert(ctx, argument, converters)


class NonCategoryChannel(AnyChannelBase):
    async def convert(self, ctx: commands.Context, argument):
        converters = [TextChannel, NewsChannel, VoiceChannel, StageChannel]
        return await super().convert(ctx, argument, converters)
