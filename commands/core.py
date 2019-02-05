import inspect

import discord
import rethinkdb as r
from discord.ext import commands as Commands

from utils.checks import checks
from utils.ctx import CustomContext
from utils.db.models import get_prefix
from utils.formats import pagify
from utils.config.setup_bot import module_loader


class Core:

    def __init__(self, bot):
        self.bot = bot

    @Commands.group(name='load')
    @checks.is_bot_owner()
    async def load(self, ctx: Commands.Context):
        """module loader commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @load.command(name="handler", aliases=["event", "h", "e"])
    @checks.is_bot_owner()
    async def handler(self, ctx: Commands.Context, *, module: str):
        """loads a event/handler"""
        await module_loader(bot=self.bot, path="handlers", name=module, ctx=ctx)

    @load.command(name="command", aliases=["cog", "com", "c"])
    @checks.is_bot_owner()
    async def command(self, ctx: Commands.Context, *, module: str):
        """loads a command/cog"""
        await module_loader(bot=self.bot, path="commands", name=module, ctx=ctx)

    @load.command(name="all")
    @checks.is_bot_owner()
    async def all(self, ctx: Commands.Context):
        """loads everything,(this will likely error as at a min this command is already loaded)"""
        await module_loader(bot=self.bot, path="commands", ctx=ctx)
        await module_loader(bot=self.bot, path="handlers", ctx=ctx)

    @Commands.group(name='unload')
    @checks.is_bot_owner()
    async def unload(self, ctx: Commands.Context):
        """module unloader commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @unload.command(name="handler", aliases=["event", "h", "e"])
    @checks.is_bot_owner()
    async def _handler(self, ctx, *, module: str):
        """unloads a event/handler"""
        await module_loader(bot=self.bot, path="handlers", name=module, unload=True, ctx=ctx)

    @unload.command(name="command", aliases=["cog", "com", "c"])
    @checks.is_bot_owner()
    async def _command(self, ctx, *, module: str):
        """unloads a command/cog"""
        await module_loader(bot=self.bot, path="commands", name=module, unload=True, ctx=ctx)

    @unload.command(name="all")
    @checks.is_bot_owner()
    async def _all(self, ctx: Commands.Context):
        """unloads everything,(including this command, rending the bot useless until restart)"""
        maybe = await ctx.confirm(ctx,
                                  message="This will unload ***all*** modules "
                                          "***including*** this one!(rending the bot useless until restart)"
                                          " y/n?")
        if maybe:
            await module_loader(bot=self.bot, path="commands", unload=True, ctx=ctx)
            await module_loader(bot=self.bot, path="handlers", unload=True, ctx=ctx)
            return
        await ctx.send("ok")

    @Commands.group(name='reload')
    @checks.is_bot_owner()
    async def reload(self, ctx: Commands.Context):
        """module reloader commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @reload.command(name="handler", aliases=["event", "h", "e"])
    @checks.is_bot_owner()
    async def __handler(self, ctx: Commands.Context, *, module: str):
        """reloads a event/handler"""
        await module_loader(bot=self.bot, path="handlers", name=module, reload=True, ctx=ctx)

    @reload.command(name="command", aliases=["cog", "com", "c"])
    @checks.is_bot_owner()
    async def __command(self, ctx: Commands.Context, *, module: str):
        """reloads a command/cog"""
        await module_loader(bot=self.bot, path="commands", name=module, reload=True, ctx=ctx)

    @reload.command(name="all")
    @checks.is_bot_owner()
    async def __all(self, ctx: Commands.Context):
        """reloads everything"""
        await module_loader(bot=self.bot, path="commands", reload=True, ctx=ctx)
        await module_loader(bot=self.bot, path="handlers", reload=True, ctx=ctx)

    @Commands.command(name="debug", aliases=["eval"])
    @checks.is_bot_owner()
    async def debug(self, ctx: Commands.Context, *, code: str):
        """Evaluates code."""
        code = code.strip('` ')
        python = '```py\n{}\n```'

        env = {
            'r': r,
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'guild': ctx.message.guild,
            'channel': ctx.message.channel,
            'author': ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))
            return
        if len(str(result)) >= 1900:
            pages = pagify(str(result))
            for page in pages:
                await ctx.send(f"```{page}```")
            return
        await ctx.send(python.format(result))

    async def process_commands(self, message: discord.Message):
        ctx = await self.bot.get_context(message, cls=CustomContext)
        if ctx.command is None:
            return
        await self.bot.invoke(ctx)

    @Commands.command()
    @checks.is_bot_owner()
    async def sudo(self, ctx, user: discord.Member, *, command):
        "Runs the [command] as if [user] had run it. DON'T ADD A PREFIX\n        "
        message = ctx.message
        message.author = user
        p = await get_prefix(self.bot, message)
        message.content = (p[0] + command)
        await self.process_commands(message)

    # https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/bot.py#L95
    @Commands.command(name="help", aliases=["h", "halp"])
    async def _help(self, ctx: Commands.Context, *commands: str):
        """Help menu"""
        destination = ctx.message.channel
        if len(commands) == 0:
            pages = await self.bot.formatter.format_help_for(ctx, self.bot)
        elif len(commands) == 1:
            name = commands[0]
            if name in self.bot.cogs:
                command = self.bot.cogs[name]
            else:
                command = self.bot.all_commands.get(name)
                if command is None:
                    await destination.send(self.bot.command_not_found.format(name))
                    return

            pages = await self.bot.formatter.format_help_for(ctx, command)
        else:
            name = commands[0]
            command = self.bot.all_commands.get(name)
            if command is None:
                await destination.send(self.bot.command_not_found.format(name))
                return
            for key in commands[1:]:
                try:
                    command = command.all_commands.get(key)
                    if command is None:
                        await destination.send(self.bot.command_not_found.format(key))
                        return
                except AttributeError:
                    await destination.send(self.bot.command_has_no_subcommands.format(command, key))
                    return
            pages = await self.bot.formatter.format_help_for(ctx, command)
        p = 0
        links = "Website: **[https://tails.fun](https://tails.fun)**\n"
        for embed in pages:
            if p == 0:
                embed.set_author(
                    name=f"Help for {self.bot.user.name}",
                    icon_url=self.bot.user.avatar_url,
                    url=discord.utils.oauth_url(self.bot.user.id)
                )
                if embed.description:
                    desc = links
                    desc += embed.description
                    embed.description = desc
                else:
                    embed.description = links
            p += 1
            embed.color = await ctx.get_color(self.bot, ctx.author)
            embed.set_footer(text=f"page {p}/{len(pages)}")
            await destination.send(embed=embed)


def setup(bot):
    bot.add_cog(Core(bot))
