import discord
from .bot import Bot
from .converters import (
    GuildChannel,
    CategoryChannel,
    TextChannel,
    NewsChannel,
    VoiceChannel,
    StageChannel,
    Thread,
    AnyChannel,
    NonCategoryChannel,
)
from .converters import (
    BotMember,
    BotUser,
    HumanMember,
    HumanUser,
    Member,
    User,
)
from .converters import (
    Color,
    Emoji,
    Guild,
    Role,
)
from .converters import IgnoreCaseLiteral, Permissions
from .checks import check_hierarchy, is_guild_owner
from .commands import command, Command

from .duration import (
    Duration,
    ParsedDuration,
    parse as parse_duration,
    strfdur,
)

from .utils import load_extensions, try_dm, s


if discord.version_info >= (2, 0, 0):
    from .ContextEditor2 import Context
    from ._flags import Flag, flag, FlagConverter, FlagIsSwitch, flags
else:
    from .ContextEditor import Context
