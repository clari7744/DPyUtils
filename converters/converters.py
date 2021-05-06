import discord, re, typing, asyncio
from discord.ext import commands
from discord.ext.commands import (
    MemberConverter,
    UserConverter,
    RoleConverter,
    CategoryChannelConverter,
    TextChannelConverter,
    VoiceChannelConverter,
    StageChannelConverter,
)
from discord.ext.commands.converter import _get_from_guilds, _utils_get
from discord.ext.commands.errors import *


def search(argument, iterable, *attrs: str, **kwargs):
    if len(iterable) < 1:
        raise Exception("Iterable is empty.")
    result = None
    discrim = kwargs.pop("discriminator", None)
    checks = [
        lambda x: any([x.__getattribute__(attr) == argument for attr in attrs]),
        lambda x: any(
            [x.__getattribute__(attr).startswith(argument) for attr in attrs]
        ),
        lambda x: any(
            [
                x.__getattribute__(attr).lower().startswith(argument.lower())
                for attr in attrs
            ]
        ),
        lambda x: any([argument in x.__getattribute__(attr) for attr in attrs]),
        lambda x: any(
            [argument.lower() in x.__getattribute__(attr).lower() for attr in attrs]
        ),
    ]
    for check in checks:
        if result:
            break
        result = [x for x in iterable if check(x)]
    if isinstance(iterable[0], (discord.Member, discord.User)) and discrim and result:
        result = [x for x in result if x.discriminator == discrim] or None
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
    if len(result) > 20:
        raise KillCommand(
            f"Too many matches found for your search `{argument}`. Please refine your search and try again."
        )
    matchlist = "\n".join([f"**{i+1}.** {v} (`{v.id}`)" for i, v in enumerate(result)])
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


class Member(MemberConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.MemberConverter
    """

    async def query_member_named(self, guild, argument):
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
                discriminator=discriminator,
            )
        else:
            #            members = await guild.query_members(argument, limit=100, cache=cache)
            result = search(argument, guild.members, "name", "display_name")
        return result

    async def convert(self, ctx, argument: str) -> discord.Member:
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
                    #                    result = utils.get(members, name=name[:-5], discriminator=potential_discriminator)
                    result = search(
                        argument[:-5],
                        guild.members,
                        "name",
                        "display_name",
                        discriminator=potential_discriminator,
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
            return result
        return await result_handler(ctx, result, argument)


class User(UserConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.UserConverter
    """

    async def convert(self, ctx, argument):
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
            return result
        arg = argument
        # Remove the '@' character if this is the first character from the argument
        if arg[0] == "@":
            # Remove first character
            arg = arg[1:]
        # check for discriminator if it exists,
        if len(arg) > 5 and arg[-5] == "#":
            discrim = arg[-4:]
            name = arg[:-5]
            #            predicate = lambda u: u.name == name and u.discriminator == discrim
            result = search(
                argument, list(state._users.values()), "name", discriminator=discrim
            )
            if result is not None:
                return result
        result = search(argument, list(state._users.values()), "name")
        if result is None:
            raise UserNotFound(argument)
        if isinstance(result, discord.User):
            return result
        return await result_handler(ctx, result, argument)


class Role(RoleConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.RoleConverter
    """

    async def convert(self, ctx, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()
        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = search(argument, list(guild._roles.values()), "name")
        if result is None:
            raise RoleNotFound(argument)
        if isinstance(result, discord.Role):
            return result
        return await result_handler(ctx, result, argument)


class CategoryChannel(CategoryChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.CategoryChannelConverter
    """

    def get_all_categories(self):
        for guild in self.guilds:
            for channel in guild.categories:
                yield channel

    async def convert(self, ctx, argument):
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

    async def convert(self, ctx, argument, *, news=False):
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
        return await result_handler(ctx, result, argument)


class NewsChannel(TextChannel):
    """
    Custom news channel converter, literally just searches for text channels and then checks if it's news.
    """

    async def convert(slf, ctx, argument):
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

    async def convert(self, ctx, argument):
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

    async def convert(self, ctx, argument):
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
