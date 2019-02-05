

import itertools
import inspect
from discord.ext import commands
from discord.ext.commands.core import GroupMixin, Command
from discord.ext.commands.errors import CommandError

from utils.help.Paginator import Paginator


# code was given to me, heavily edited for my needs
# seems to come from https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/formatter.py#L126
class EmbededHelp(commands.HelpFormatter):
    def __init__(self, show_hidden=False, show_check_failure=False, width=65):
        super().__init__(show_hidden, show_check_failure, width)
        self.width = width
        self.show_hidden = show_hidden
        self.show_check_failure = show_check_failure
        self.context = ""
        self.command = ""
        self._paginator = ""

    def has_subcommands(self):
        return isinstance(self.command, GroupMixin)

    def is_bot(self):
        return self.command is self.context.bot

    def is_cog(self):
        return not self.is_bot() and not isinstance(self.command, Command)

    @property
    def max_name_size(self):
        try:
            coms = self.command.all_commands if not self.is_cog() else self.context.bot.all_commands
            if coms:
                return max(map(lambda c: len(c.name) if self.show_hidden or not c.hidden else 0, coms.values()))
            return 0
        except AttributeError:
            return len(self.command.name)

    @property
    def clean_prefix(self):
        user = self.context.bot.user
        return self.context.prefix.replace(user.mention, '@' + user.name)

    def get_command_signature(self):
        prefix = self.clean_prefix
        cmd = self.command
        return prefix + cmd.signature

    def get_ending_note(self):
        command_name = self.context.invoked_with
        return f"Type {self.clean_prefix}{command_name} command for more info on a command.\nYou can also type " \
               f"{self.clean_prefix}{command_name} category for more info on a category. "

    async def filter_command_list(self):
        def sane_no_suspension_point_predicate(tup):
            cmd = tup[1]
            if self.is_cog():
                if cmd.instance is not self.command:
                    return False

            if cmd.hidden and not self.show_hidden:
                return False

            return True

        async def predicate(tup):
            if sane_no_suspension_point_predicate(tup) is False:
                return False

            cmd = tup[1]
            try:
                return await cmd.can_run(self.context)
            except CommandError:
                return False

        iterator = self.command.all_commands.items() if not self.is_cog() else self.context.bot.all_commands.items()
        if self.show_check_failure:
            return filter(sane_no_suspension_point_predicate, iterator)

        ret = []
        for elem in iterator:
            valid = await predicate(elem)
            if valid:
                ret.append(elem)

        return ret

    def _add_subcommands_to_page(self, max_width, coms, prefix: bool=True):
        p = self.context.prefix
        if not prefix:
            p = ""
        for name, command in coms:
            if name in command.aliases:
                continue
            entry = f'**{p}{name}**: `{command.short_doc}`'
            alias = ", ".join(command.aliases)
            if alias:
                entry = f'**{p}{name}**: `{command.short_doc}`\n**aliases**: `{alias}`'
            self._paginator.add_line(f'{entry}')
            if hasattr(command, "group"):
                for x in command.commands:
                    entry = f'**{p}{name} {x.name}**\n`{x.short_doc}`'
                    alias = ", ".join(x.aliases)
                    if alias:
                        entry = f'**{p}{name} {x.name}**: `{x.short_doc}`\n**aliases**: `{alias}`'
                    self._paginator.add_line(f'{entry}')

    async def format_help_for(self, context, command_or_bot):
        self.context = context
        self.command = command_or_bot
        return await self.format()

    async def format(self):
        self._paginator = Paginator()
        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)
        if description:
            self._paginator.add_line(description, empty=False)

        if isinstance(self.command, Command):
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            cogs = self.context.bot.cogs
            if cog in cogs and hasattr(cogs[cog], "name"):
                cog = cogs[cog].name
            return cog + ':' if cog is not None else '\u200bNo Category:'

        filtered = await self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            for category, coms in itertools.groupby(data, key=category):
                coms = sorted(coms)
                if len(coms) > 0:
                    self._paginator.add_line(category)

                self._add_subcommands_to_page(max_width, coms)
        else:
            filtered = sorted(filtered)
            if filtered:
                self._paginator.add_line('Commands:')
                self._add_subcommands_to_page(max_width, filtered, False)

        self._paginator.add_line()
        ending_note = self.get_ending_note()
        self._paginator.add_line(ending_note)
        return self._paginator.pages
