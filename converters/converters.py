import discord, re
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
from discord.ext.commands.errors import *


def search(argument, iterable, *attrs: str):
    result = None
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
        result = discord.utils.find(check, iterable)
    return result


class Member(MemberConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.MemberConverter
    """

    async def query_member_named(self, guild, argument):
        cache = guild._state.member_cache_flags.joined
        result = None
        if len(argument) > 5 and argument[-5] == "#":
            username, _, discriminator = argument.rpartition("#")
            members = await guild.query_members(username, limit=100, cache=cache)
            return discord.utils.find(
                lambda m: username.lower() == m.name.lower()
                or username.lower() == m.display_name.lower()
                and discriminator == discriminator,
                members,
            )
        else:
            members = await guild.query_members(argument, limit=100, cache=cache)
            result = search(argument, members, "name", "display_name")
        return result


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
            predicate = lambda u: u.name == name and u.discriminator == discrim
            result = discord.utils.find(predicate, state._users.values())
            if result is not None:
                return result
        result = search(state._users.values(), "name")
        if result is None:
            raise UserNotFound(argument)
        return result


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
            result = search(argument, guild._roles.values(), "name")
        if result is None:
            raise RoleNotFound(argument)
        return result


class CategoryChannel(CategoryChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.CategoryChannelConverter
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.get_all_categories = self.get_all_categories

    def get_all_categories(self):
        for guild in self.guilds:
            for channel in guild.categories:
                yield channel

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
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
        return result


class TextChannel(TextChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.TextChannelConverter
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.get_all_text_channels = self.get_all_text_channels

    def get_all_text_channels(self):
        for guild in self.guilds:
            for channel in guild.text_channels:
                yield channel

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
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
        return result


class VoiceChannel(VoiceChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.VoiceChannelConverter
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.get_all_voice_channels = self.get_all_voice_channels

    def get_all_voice_channels(self):
        for guild in self.guilds:
            for channel in guild.voice_channels:
                yield channel

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
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
        return result


class StageChannel(StageChannelConverter):
    """
    Custom converter to allow for looser searching, inherits from commands.StageChannelConverter
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.get_all_stage_channels = self.get_all_stage_channels

    def get_all_stage_channels(self):
        for guild in self.guilds:
            for channel in guild.stage_channels:
                yield channel

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None
        guild = ctx.guild
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
        return result
