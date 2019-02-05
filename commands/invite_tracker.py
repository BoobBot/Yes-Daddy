import discord
from discord.ext import commands

from utils.checks import checks


class InviteMirror:
    def __init__(self, bot):
        self.bot = bot

    @checks.admin_or_permissions(administrator=True)
    @commands.group(name='invitemirror', no_pm=True)
    async def invite_mirror(self, ctx):
        """Shows who joined with which invite"""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @invite_mirror.command(name='here', no_pm=True)
    async def channel(self, ctx, channel: discord.TextChannel = None):
        """Sets the Modlog Channel."""
        if channel is None:
            channel = ctx.channel
        guild = ctx.message.guild
        g = await ctx.get_guild()
        if g.invite_tracker["Channel"]:
            await ctx.send(
                "Channel already registered, use invitemirror disable then set a new channel to switch channels.")
            return
        if not ctx.message.guild.me.permissions_in(channel).manage_channels:
            await ctx.send("I dont have the manage channels permission.")
            return
        if ctx.message.guild.me.permissions_in(channel).send_messages:
            invlist = await guild.invites()
            g.invite_tracker = {"Channel": str(channel.id), "Invites": {}}
            for i in invlist:
                g.invite_tracker["Invites"][i.url] = i.uses
            await g.save()
            await ctx.send("I will now send invitemirror notifications here")
        else:
            return

    @invite_mirror.command(name='disable', pass_context=True, no_pm=True)
    async def disable(self, ctx):
        """disables the invite mirror"""
        g = await ctx.get_guild()
        db = g.invite_tracker
        if not db:
            await ctx.send("settings not found, use invitemirror channel to set a channel.")
            return
        g.invite_tracker = {"Channel": None, "Invites": None}
        await g.save()
        await ctx.send("I will no longer send invite tracker notifications here")


def setup(bot):
    bot.add_cog(InviteMirror(bot))
