import asyncio
import io
import logging
import os
from datetime import timedelta

import discord
import psutil
from discord.ext import commands

from utils.checks import checks
from utils.db.models import get_prefix
from utils.ctx import CustomContext


class Mod:
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())
        self.env = {}
        self.stdout = io.StringIO()

    @staticmethod
    def _role_from_string(guild, rolename, roles=None):
        if roles is None:
            roles = guild.roles
        roles = [r for r in roles if (r is not None)]
        role = discord.utils.find((lambda r: (r.name.lower() == rolename.lower())), roles)
        return role

    #########################################################
    # snipe things
    #########################################################
    # TODO non place holder msgs
    @commands.group(name="snipe")
    async def _snipe(self, ctx: CustomContext):
        if not ctx.subcommand_passed:
            g = await ctx.get_guild()
            m = g.snipe["data"].get(str(ctx.channel.id), None)
            if m:
                em = discord.Embed(color=discord.Color.blue())
                user = await self.bot.get_user_info(int(str(m["user"])))
                em.set_author(name=user.name, icon_url=user.avatar_url)
                em.add_field(name="Sniped message", value=m["msg"], inline=False)
                em.set_footer(text=f"Sniped by {ctx.author}", icon_url=ctx.author.avatar_url)

                await ctx.send(embed=em)
            else:
                await ctx.send("No snipes")

    @_snipe.command(name="clear")
    async def _clear(self, ctx: CustomContext):
        g = await ctx.get_guild()
        m = g.snipe["enabled"]
        if m:
            g.snipe["data"].clear()
            await g.save()
            await ctx.send("done")
        else:
            await ctx.send("not on")

    @_snipe.command(name="enable")
    async def _enable(self, ctx: CustomContext):
        g = await ctx.get_guild()
        m = g.snipe["enabled"]
        if m:
            await ctx.send("on")
        else:
            g.snipe["enabled"] = True
            await g.save()
            await ctx.send("done")

    @_snipe.command(name="disable")
    async def _disable(self, ctx: CustomContext):
        g = await ctx.get_guild()
        m = g.snipe["enabled"]
        if not m:
            await ctx.send("off")
        else:
            g.snipe["enabled"] = None
            g.snipe["data"].clear()
            await g.save()
            await ctx.send("done")

    #########################################################
    # mass add things
    #########################################################

    # noinspection PyBroadException
    @commands.command(pass_context=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def massadd(self, ctx: CustomContext, *, rolename):
        """Adds all members to a role"""
        guild = ctx.message.guild
        role = self._role_from_string(guild, rolename)
        # YAY counter
        nc = 0
        if role is None:
            await ctx.send("Role not found")
            return
        await ctx.send("Adding everyone to role '{}', please wait!".format(role.name))
        # we copy the list over so it doesn't change while we're iterating over it
        members = list(guild.members)
        for member in members:
            try:
                await member.add_roles(role, reason=f"Lets party! massadd command ran by {ctx.message.author}")
                nc += 1
            except Exception:
                continue
        await ctx.send("Finished Adding Roles to {} members!".format(nc))

    #########################################################
    # slow delete
    #########################################################

    @checks.admin_or_permissions(Manage_Messages=True)
    @commands.command(aliases=['slowdelete'])
    async def sd(self, ctx: CustomContext, limit: int):
        """deletes messages the slow why yes even over 14 days"""
        channel = ctx.channel
        if limit > 5000:
            limit = 5000
        async for msg in channel.history(limit=limit):
            await msg.delete()


    #########################################################
    # kick/bans
    #########################################################


    @commands.command(no_pm=True)
    @checks.admin_or_permissions(kick_members=True)
    async def kick(self, ctx: CustomContext, user: discord.Member, *, reason=None):
        """Kicks user."""

        if ctx.author == user:
            await ctx.send("lol no")
            return
        try:
            if reason:
                await user.kick(reason=f"{reason}, Command ran by {ctx.author}")
                await ctx.send('bye 👋🏼')
            else:
                await user.kick(reason=f"{ctx.author} ran this with no reason provided")
                await ctx.send('bye 👋🏼')

        except discord.errors.Forbidden:
            await ctx.send('❌ Permissions error of some kind.')
        except Exception as e:
            ctx.bot.log.error("wot", e)
            await ctx.send('❌ error of some kind.')

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def ban(self, ctx: CustomContext, user: discord.Member, days: str = None, *, reason=None):
        """Bans user and deletes last X days worth of messages."""
        if ctx.author == user:
            return await ctx.send("lol no")
        if days:
            if days.isdigit():
                days = int(days)
            else:
                days = 0
        else:
            days = 0
        if days > 7 or days < 0:
            days = 7
        else:
            days = days
        if reason:
            reason = f"{reason}, Command ran by {ctx.author}"
        else:
            reason = f"Command ran by {ctx.author}, with no reason provided"
        try:
            await ctx.guild.ban(user=user,
                                reason=reason,
                                delete_message_days=days)
            await ctx.send('bye 👋🏼 next time just stfu')
        except discord.errors.Forbidden:
            (await ctx.send('❌ Permissions error of some kind.'))
        except Exception as e:
            ctx.bot.log.error("? ", e)

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(ban_members=True)
    async def softban(self, ctx: CustomContext, user: discord.Member):
        """Kicks the user, deleting 3 day worth of messages."""
        guild = ctx.guild
        channel = ctx.channel
        can_ban = channel.permissions_for(guild.me).ban_members
        author = ctx.author
        if (author == user):
            (await ctx.send(
                '😂 LOL as much as i would love to see you ban yourself i cant let you do that.\n You should try the leave server button <:ls:380047736877088788> or `dfban` yourself.'))
            return
        try:
            invite = (await guild.channels[0].create_invite())
        except:
            invite = ''
        if can_ban:
            try:
                try:
                    (await user.send(
                        'You have been softbanned as a quick way to delete your messages.\nYou can now join the server again.{}'.format(
                            invite)))
                except:
                    pass
                (await ctx.guild.ban(user=user, reason="soft ban", delete_message_days=3))
                (await guild.unban(user))
                (await ctx.send('bye 👋🏼 see you in a sec.'))
            except discord.errors.Forbidden:
                (await ctx.send('❌ Permissions error of some kind.'))
            except Exception as e:
                print(e)
        else:
            (await ctx.send('❌ Permissions error of some kind.'))

    @commands.command(no_pm=True)
    @checks.admin_or_permissions(manage_nicknames=True)
    async def setnick(self, ctx: CustomContext, user: discord.Member, *, nickname=''):
        'Changes a members nick leaving empty will remove it.'
        nickname = nickname.strip()
        cl = 'changed'
        if (nickname == ''):
            nickname = None
            cl = 'cleared'
        try:
            (await user.edit(nick=nickname, reason="command ran by {}".format(ctx.message.author)))
            (await ctx.send("I have {} {}'s nickname 👌🏼".format(cl, user.name)))
        except discord.Forbidden:
            (await ctx.send('❌ Permissions error of some kind.'))

    @commands.command(no_pm=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def warn(self, ctx: CustomContext, user: discord.Member, *, reason: str = None):
        'Warns a Member.'
        msg = [('%s, ' % user.mention)]
        msg.append("you're doing something that might get you banned 🔨 if you keep doing it.")
        if reason:
            msg.append((' Specifically, %s.' % reason))
        msg.append('Be sure to **__read__** the dam rules huh?')
        try:
            (await user.send(' '.join(msg)))
        except:
            pass
        (await ctx.send(' '.join(msg)))

    @commands.command(aliases=['ar'], no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def addrole(self, ctx: CustomContext, rolename, user: discord.Member = None):
        'Adds a role to a user, defaults to author\n\n        Role name must be in quotes if there are spaces.'
        author = ctx.author
        channel = ctx.channel
        guild = ctx.guild
        if (user is None):
            user = author
        role = self._role_from_string(guild, rolename)
        if (role is None):
            (await ctx.send('❌ That role cannot be found.'))
            return
        if (not channel.permissions_for(guild.me).manage_roles):
            (await ctx.send("❌ I don't have manage_roles."))
            return
        (await user.add_roles(role, reason="{} ran this command!".format(ctx.message.author)))
        (await ctx.send('Added role {} to {} 👌🏼'.format(role.name, user.name)))

    @commands.command(aliases=['rr'], no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def removerole(self, ctx: CustomContext, rolename, user: discord.Member = None):
        'Removes a role from a user,\n        Role name must be in quotes if there are spaces.'
        guild = ctx.guild
        author = ctx.author
        role = self._role_from_string(guild, rolename)
        if (role is None):
            (await ctx.send('❌ Role not found.'))
            return
        if (user is None):
            user = author
        if (role in user.roles):
            try:
                (await user.remove_roles(role))
                (await ctx.send('Role successfully removed.👌🏼'))
            except discord.Forbidden:
                (await ctx.send("❌ I don't have permissions to manage roles!"))
        else:
            (await ctx.send('❌ User does not have that role.'))

    @commands.group(aliases=['er'], no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def editrole(self, ctx: CustomContext):
        'Edits roles'
        if (ctx.invoked_subcommand is None):
            (await ctx.send_cmd_help(ctx))

    @editrole.command(aliases=['colour', 'c'])
    async def color(self, ctx: CustomContext, role: discord.Role, value: discord.Colour):
        "Edits a role's color"
        try:
            (await role.edit(color=value, reason="{} ran this command!".format(ctx.message.author)))
            (await ctx.send('Done.👌🏼'))
        except discord.Forbidden:
            (await ctx.send('❌ I need permissions to manage roles first.'))
        except Exception as e:
            print(e)
            (await ctx.send('❌ Something went wrong.'))

    @editrole.command(aliases=['n'], name='name')
    @checks.admin_or_permissions(administrator=True)
    async def edit_role_name(self, ctx: CustomContext, role: discord.Role, name: str):
        "Edits a role's name "
        if (name == ''):
            (await ctx.send('❌ Name cannot be empty.'))
            return
        try:
            (await role.edit(name=name, reason="{} ran this command!".format(ctx.message.author)))
            (await ctx.send('Done.👌🏼'))
        except discord.Forbidden:
            (await ctx.send('❌ I need permissions to manage roles first.'))
        except Exception as e:
            print(e)
            (await ctx.send('❌ Something went wrong.'))

    #    @commands.cooldown(1, 15000, type=commands.BucketType.guild)
    @commands.command(aliases=['mn'], no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def massnick(self, ctx: CustomContext, rolename, *, nickname):
        'changes everyones nickname in a role'
        guild = ctx.guild
        counter = 0
        nc = 0
        (await ctx.send('This may take a min ⏲️'))
        if discord.utils.get(guild.roles, name=rolename):
            member_list = [members for members in guild.members if
                           (discord.utils.get(guild.roles, name=rolename) in members.roles)]
            for user in member_list:
                try:
                    (await user.edit(nick=nickname, reason="Changing nicks, requested by {}"
                                     .format(ctx.message.author)))
                    nc += 1
                    (await asyncio.sleep(1.5))
                except discord.Forbidden:
                    counter += 1
                except discord.HTTPException:
                    print('lol nickname rate limits')
                    (await ctx.send('lol nickname rate limits'))
            (await ctx.send('Finished 👌🏼 There were {} nicks set and {} errors❌'.format(nc, counter)))
        else:
            (await ctx.send(
                ('❌ ERROR: Could not find rolename `%s`, please make sure you typed it case accurate' % rolename)))

    @massnick.error
    async def mn_error(self, ctx: CustomContext, error):
        if type(error) is commands.CommandOnCooldown:
            fmt = (str(error)).split()
            word = fmt[7].strip("s")
            time = float(word)
            timer = round(time, 0)
            tdelta = str(timedelta(seconds=int(timer))).lstrip("0").lstrip(":")
            await ctx.send("❌ lol nickname rate limits You can try again in `{}`".format(tdelta))

    @commands.cooldown(1, 14400, type=commands.BucketType.guild)
    @commands.command(aliases=['mnc'], no_pm=True)
    @checks.admin_or_permissions(manage_roles=True)
    async def massnickc(self, ctx: CustomContext, rolename):
        'clears everyones nickname in a role'
        guild = ctx.guild
        counter = 0
        nc = 0
        (await ctx.send('This may take a min ⏲️'))
        if discord.utils.get(guild.roles, name=rolename):
            member_list = [members for members in guild.members if
                           (discord.utils.get(guild.roles, name=rolename) in members.roles)]
            for user in member_list:
                try:
                    (await user.edit(nick='', reason="rip nicks. Ran by {}".format(ctx.message.author)))
                    nc += 1
                    (await asyncio.sleep(1.5))
                except discord.Forbidden:
                    counter += 1
                except discord.HTTPException:
                    print('lol nickname rate limits')
                    (await ctx.send('❌ lol nickname rate limits'))
            (await ctx.send('Finished 👌🏼 There were {} nicks cleared and {} errors❌'.format(nc, counter)))
        else:
            (await ctx.send(
                ('❌ ERROR: Could not find rolename `%s`, please make sure you typed it case accurate' % rolename)))

    @massnickc.error
    async def mnc_error(self, ctx: CustomContext, error):
        if type(error) is commands.CommandOnCooldown:
            fmt = (str(error)).split()
            word = fmt[7].strip("s")
            time = float(word)
            timer = round(time, 0)
            tdelta = str(timedelta(seconds=int(timer))).lstrip("0").lstrip(":")
            await ctx.send("❌ lol nickname rate limits You can try again in `{}`".format(tdelta))

    @checks.admin_or_permissions(manage_channels=True)
    @commands.command(aliases=["sm"])
    async def slowmode(self, ctx: CustomContext, rate: int, channel: discord.TextChannel = None):
        """Activate slow mode for channel"""
        if channel is None:
            channel = ctx.channel
        headers = dict(Authorization=f"Bot {self.bot.http.token}")
        payload = {"rate_limit_per_user": rate}
        if 1 <= int(rate) <= 120:
            r = await self.bot.session.patch(f"https://discordapp.com/api/v7/channels/{channel.id}",
                                             headers=headers,
                                             json=payload)
            res = await r.json
            await ctx.send(
                content=f"slow mode set to {res['rate_limit_per_user']} seconds per user",
                delete_after=2)
        else:
            if int(rate) == 0:
                r = await self.bot.session.patch(f"https://discordapp.com/api/v7/channels/{channel.id}",
                                                 headers=headers, json=payload)
                await r.json()
                await ctx.send(content="Slow-mode disabled", delete_after=2)
            else:
                await ctx.send(content="You have entered an invalid rate. Please select aa number between 1 and 120.",
                               delete_after=2)


def setup(bot):
    bot.add_cog(Mod(bot))
