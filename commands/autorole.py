import discord
from discord.ext import commands
from utils.checks import checks


class Autorole:

    def __init__(self, bot):
        self.bot = bot

    @checks.admin_or_permissions(manage_roles=True)
    @commands.group(no_pm=True)
    async def autorole(self, ctx):
        """Autorole Settings
        Adds a role on join to users and bots."""
        if ctx.invoked_subcommand is None:
            await ctx.send_cmd_help(ctx)

    @checks.admin_or_permissions(administrator=True)
    @autorole.command(no_pm=True)
    async def info(self, ctx):
        """Shows Auto Status."""
        guild = await ctx.get_guild()
        bot_role_id = guild.auto_role_bot
        role_id = guild.auto_role
        desc = '**Status:**\n'
        if role_id:
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
            desc += f'➠ Role: **@{role.name}** \n'
        else:
            desc += '➠ Role: **none** \n'
        if bot_role_id:
            role = discord.utils.get(ctx.guild.roles, id=int(bot_role_id))
            desc += f'➠ Bot role: **@{role.name}** \n'
        else:
            desc += '➠ Bot role: **none** \n'

        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @autorole.command(no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def role(self, ctx, *, role: discord.Role):
        """Sets the Autorole Role."""
        if role is None:
            return await ctx.send("❌ That role cannot be found.")
        if not ctx.channel.permissions_for(ctx.guild.me).manage_roles:
            return await ctx.send("❌ I don't have manage_roles.")
        guild = await ctx.get_guild()
        guild.auto_role = str(role.id)
        await guild.save()
        desc = f'➠ AutoRole set to: **@{role.name}**\n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @autorole.command(no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def botrole(self, ctx, *, role: discord.Role):
        """Sets the Autorole for Bots."""
        if role is None:
            return await ctx.send("❌ That role cannot be found.")
        if not ctx.channel.permissions_for(ctx.guild.me).manage_roles:
            return await ctx.send("❌ I don't have manage_roles.")
        guild = await ctx.get_guild()
        guild.auto_role_bot = str(role.id)
        await guild.save()
        desc = f'➠ AutoRole for Bots set to: **@{role.name}**\n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @checks.admin_or_permissions(administrator=True)
    @autorole.command(no_pm=True)
    async def disable(self, ctx):
        """Disable Autorole"""
        guild = await ctx.get_guild()
        guild.auto_role = None
        await guild.save()
        desc = f'➠ Autorole disabled on **{ctx.guild.name}** \n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)

    @checks.admin_or_permissions(administrator=True)
    @autorole.command(no_pm=True)
    async def disablebot(self, ctx):
        """Disable Autorole for Bots"""
        guild = await ctx.get_guild()
        guild.auto_role_bot = None
        await guild.save()
        desc = f'➠ Autorole for Bots disabled on **{ctx.guild.name}** \n'
        em = discord.Embed(description=desc, color=discord.Color.blue())
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Autorole(bot))
