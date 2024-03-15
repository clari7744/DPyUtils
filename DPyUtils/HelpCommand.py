from discord import Color, DMChannel, Embed, utils
from discord.ext.commands import Bot, Cog, Command, Context, Group, HelpCommand, Paginator
from discord.ext.commands.help import _HelpCommandImpl

from .flags import FlagConverter
from .utils import trim


class EmbedHelpCommand(HelpCommand):
    def __init__(self, **options):
        options["command_attrs"] = dict(
            **options.get("command_attrs", {}),
            brief="Shows help for categories and commands. Type `{prefix}{help} help` for more info\n",
            help="\n".join(
                "This command will show a list of usable categories by default."
                "You can also type `{prefix}{help} <category>` for a list of usable commands in that category, or `{prefix}{help} <command>` for more information on using that command.\n"
                "`<argument>` indicates a required argument."
                "`[argument]` indicates an optional argument."
                "`...` indicates a greedy argument (you can give many items of the same time to that argument).",
            ),
        )
        super().__init__(**options)
        self.width = options.pop("width", 200)
        self.paginator = Paginator(
            prefix=None,
            suffix=None,
            max_size=4096,
        )

    async def prepare_help_command(self, ctx: Context, command: str | None = None):
        self.paginator.max_size = 4096 - len(self.get_ending_note())

    def get_ending_note(self):
        return f"""
Type `{self.context.clean_prefix}{self.invoked_with} <cog>` to get a list of commands for that cog.
Type `{self.context.clean_prefix}{self.invoked_with} <command>` to get info on that command.
"""

    async def send_error_message(self, error):
        return await self.context.send(error)

    async def filter_commands(self, commands, *, sort=False, key=None):
        self.show_hidden = True if (await self.context.bot.is_owner(self.context.author)) else False
        if isinstance(self.context.channel, DMChannel):
            return commands
        return await super().filter_commands(commands, sort=sort, key=key)

    def get_command_signature(self, command):
        parent = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + " " + parent.signature)
            parent = parent.parent
        parent_sig = " ".join(reversed(entries))
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent_sig:
                fmt = parent_sig + " " + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + " " + command.name
        return f"{self.context.clean_prefix}{alias} {command.signature}"

    def add_command_formatting(self, command: Command):
        """A utility function to format the non-indented block of commands and groups.

        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """
        if command.description:
            self.paginator.add_line(command.description, empty=True)
        signature = self.get_command_signature(command)
        self.paginator.add_line(f"`{signature}`", empty=True)
        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def fmt_commands(self, cmds: list[Command]):
        for cmd in cmds:
            width = self.get_max_size(cmds) - (utils._string_width(cmd.name) - len(cmd.name))
            entry = f"`{cmd.name:<{width}}` | {cmd.short_doc}"
            self.paginator.add_line(trim(entry, self.width))

    async def send_help(self, embed: Embed):
        embed.description = embed.description.format(prefix=self.context.clean_prefix, help=self.context.invoked_with)
        embed.color = self.context.me.color or Color.random()
        embed.set_author(
            icon_url=self.context.author.avatar,
            name=f"Requested by {self.context.author}",
        )
        return await self.context.send(embed=embed)

    async def send_bot_help(self, mapping):
        ctx: Context = self.context
        embed = Embed(title="Cogs")
        cogs: list[str] = [
            str(x.qualified_name) for x in mapping.keys() if x and (await self.filter_commands(x.walk_commands()))
        ] + [
            ""
        ]  # zip cuts elements from longer list, this is a janky fix
        clen = len(cogs) // 2
        print(clen)
        half1 = map(lambda cog: f"{cog:<18}", cogs[:clen])
        half2 = cogs[clen:]
        desc = "\n".join([" ".join(line) for line in zip(half1, half2)])
        embed.description = f"```\n{desc}```{self.get_ending_note()}"
        nocog = [
            cmd
            for cmd in (await self.filter_commands(ctx.bot.commands))
            if not cmd.cog and not isinstance(cmd, _HelpCommandImpl)
        ]
        if nocog:
            self.fmt_commands(nocog)
            embed.add_field(name="No Category", value=self.paginator.pages[0])
        return await self.send_help(embed)

    async def send_cog_help(self, cog: Cog):
        embed = Embed(title=f"{cog.qualified_name}")
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)
        cmds = await self.filter_commands(cog.get_commands())
        if not cmds:
            embed.description = "You do not have permissions to use any commands in this cog."
            return await self.send_help(embed)
        self.fmt_commands(cmds)
        self.paginator.add_line(self.get_ending_note())
        embeds = []
        for i, p in enumerate(self.paginator.pages, 1):
            embed.description = p
            embed.set_footer(text=f"Page {i}/{len(self.paginator.pages)}")
            embeds.append(embed)
        for e in embeds:
            await self.send_help(e)

    # NEED BETTER FORMATTING, IE less commands per page and actual paginator
    # Use DiscordUtils.CustomEmbedPaginator, custom function for this.

    async def send_group_help(self, group: Group):
        embed = Embed(title=f"{group} Subcommands")
        self.add_command_formatting(group)
        #        cmds = await self.filter_commands(group.commands)
        #        if not cmds:
        #            return
        cmds = group.commands
        self.fmt_commands(cmds)
        self.paginator.add_line(self.get_ending_note())
        embeds = []
        for i, p in enumerate(self.paginator.pages, 1):
            embed.description = p
            embed.set_footer(text=f"Page {i}/{len(self.paginator.pages)}")
            embeds.append(embed)
        for e in embeds:
            await self.send_help(e)

    async def send_command_help(self, command: Command):
        ctx: Context = self.context
        await self.filter_commands(ctx.bot.commands)
        embed = Embed(title=f"{command}", description=command.help or "")
        embed.description += (
            f"\n\nUsage: `{ctx.clean_prefix}{(command.full_parent_name+' ') if command.parent else ''}{command.name}{(' '+command.signature) if command.signature else ''}`\n\n"
            "Type `{prefix}{help} help` to view command syntax."
        )
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join([f"`{a}`" for a in command.aliases]), inline=False)
        if getattr(command, "flags", None) is not None:
            flags: FlagConverter = command.flags
            embed.add_field(
                name="Flags",
                value=f"```\n{flags.get_flag_signature()}```",
                inline=False,
            )
        await self.send_help(embed)


class HelpCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        help_command = EmbedHelpCommand(command_attrs={"name": "help", "aliases": ["h"]})
        help_command.cog = self
        bot.help_command = help_command

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


async def setup(bot: Bot):
    HelpCog(bot)
