import discord
from discord.ext import commands

from utils.db.models import get_guild
from utils.colors import get_effective_color
from utils.formats import embed


class CustomContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self):
        return self.bot.session

    @property
    def db_conn(self):
        return self.bot.conn

    @staticmethod
    async def confirm(ctx: commands.Context, message: str=None):
        text = '*Are you sure you want to proceed?* `(Y/N)`'
        if message:
            text = message
        await ctx.send(text)
        resp = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        if resp.content.lower().strip() == "n":
            return False
        else:
            return True

    @staticmethod
    async def send_cmd_help(self):
        channel = self.message.channel
        if self.invoked_subcommand:
            ps = await self.bot.formatter.format_help_for(self, self.invoked_subcommand)
            for p in ps:
                p.title = "Missing args :x:"
                p.color = discord.Color.red()
                await channel.send(embed=p)
        else:
            ps = await self.bot.formatter.format_help_for(self, self.command)
            for p in ps:
                p.title = "Missing args :x:"
                p.color = discord.Color.red()
                await channel.send(embed=p)

    @staticmethod
    async def get_color(self, member):
        return await get_effective_color(self, member)

    @staticmethod
    async def em(self, text, color):
        return await embed(self, text, color)

    async def get_guild(self):
        return await get_guild(self.bot, self.guild)

