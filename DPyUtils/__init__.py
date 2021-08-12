# pylint: disable=import-error
from .bot import Bot
from .converters import (
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
from .ContextEditor import Context
from .duration import (
    Duration,
    DurationParser,
    ParsedDuration,
    parse as parse_duration,
    strfdur,
)
from ._flags import Flag, flag, FlagConverter, FlagIsSwitch, flags
from .utils import load_extensions, try_dm
