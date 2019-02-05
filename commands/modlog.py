import discord
from discord.ext import commands

from utils.checks import checks
from utils.db.models import get_guild, GuildEntry


class ModLog:

    def __init__(self, bot):
        self.bot = bot

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group(no_pm=True)
    async def modlog(self, ctx):
        """Modlog Settings"""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @checks.admin_or_permissions(administrator=True)
    @modlog.group(no_pm=True)
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Sets the Modlog Channel."""
        if channel is None:
            channel = ctx.channel
        g: GuildEntry = await ctx.get_guild()
        g.modlog_channel = str(channel.id)
        await g.save()
        desc = f'➠ Modlog Channel set to: **#{channel.name}**\n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @checks.admin_or_permissions(administrator=True)
    @modlog.command(no_pm=True)
    async def off(self, ctx):
        """Disables Modlog"""
        g: GuildEntry = await ctx.get_guild()
        g.modlog_channel = None
        await g.save()
        desc = f'➠ Modlog disabled on **{ctx.guild.name}** \n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @checks.admin_or_permissions(administrator=True)
    @modlog.command(no_pm=True)
    async def status(self, ctx):
        """Shows the Modlog Status"""
        g: GuildEntry = await ctx.get_guild()
        modlog_channel = g.modlog_channel
        await g.save()
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            desc = f'➠ Modlog enabled on **#{channel.name}**'
            em = discord.Embed(description=desc, color=discord.Color.blue())
            await ctx.send(embed=em)
        else:
            await ctx.send(f'Modlog disabled on **{ctx.guild.name}**')


def setup(bot):
    bot.add_cog(ModLog(bot))
