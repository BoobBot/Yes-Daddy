import asyncio
import datetime

import discord

from utils.config.config import set_home
from utils.db import models
from utils.db.models import get_guild, GuildEntry

fmt = '%H:%M:%S'


class ModlogHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_message_delete(self, message):
        guild = message.guild
        db: GuildEntry = await models.get_guild(self.bot, guild)
        if db.snipe["enabled"] and not message.author.bot:
            if len(message.content) > 0:
                db.snipe["data"][str(message.channel.id)] = {"msg": message.content, "user": str(message.author.id)}
                await db.save()

        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            cleanmsg = message.clean_content
            msg = \
                f":pencil: `{time.strftime(fmt)}` **Channel** {message.channel.mention}(`{message.channel.id}`) " \
                f"**{message.author}(`{message.author.id}`)'s** message(`{message.id}`) has been deleted. Content: " \
                f"{cleanmsg} "
            await channel.send(msg)

    async def on_member_join(self, member):
        guild = member.guild
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            users = len([e.name for e in guild.members])
            msg = f':white_check_mark: `{time.strftime(fmt)}` User **{member.name}** with id: `{member.id}` has ' \
                  f'joined the guild. Total users: `{users}`. '
            await channel.send(msg)

        if member.bot:
            autoroleb = db.auto_role_bot
            if autoroleb:
                roles = guild.roles
                role = discord.utils.get(roles, id=int(autoroleb))
                await member.add_roles(role)
        else:
            autorole = db.auto_role
            if autorole:
                roles = guild.roles
                role = discord.utils.get(roles, id=int(autorole))
                try:
                    await member.add_roles(role)
                except discord.errors.NotFound or discord.errors.Forbidden as e:
                    self.bot.log.error(f"shit: {repr(e)}", exc_info=False)

        await asyncio.sleep(1)
        g = await get_guild(self.bot, member.guild)
        if not g.invite_tracker["Channel"]:
            return
        db = g.invite_tracker
        channel = guild.get_channel(int(str(db["Channel"])))
        if not channel:
            g.invite_tracker = {"Channel": None, "Invites": {}}
            return await g.save()
        db_list = db["Invites"]
        inv_list = await guild.invites()
        for a in inv_list:
            try:
                if int(a.uses) > int(db_list[a.url]):
                    await channel.send(
                        f"{member.name} | {member.mention} (`{member.id}`)\nJoined using invite: `{a.url}`\nThe invite "
                        f"was used {a.uses} times\nMade by {a.inviter} (`{a.inviter.id}`)")
                    break
            except KeyError:
                await channel.send(
                    f"{member.name} | {member.mention} (`{member.id}`)\nJoined using invite: `{a.url}`\nThe invite "
                    f"was used {a.uses} times\nMade by {a.inviter} (`{a.inviter.id}`)")
                break
            else:
                pass
        for inv in inv_list:
            db["Invites"][inv.url] = inv.uses
            db["id"] = str(guild.id)
        await g.save()

    async def on_member_remove(self, member):
        guild = member.guild
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            users = len([e.name for e in guild.members])
            msg = f"<:ls:380047736877088788> `{time.strftime(fmt)}` User **{member.name}** with id: `{member.id}` has " \
                  f"left the guild or was kicked. Total members `{users}`. "
            await channel.send(msg)

    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        guild = before.guild
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            if before.content == after.content:
                return

            cleanbefore = before.clean_content
            cleanafter = after.clean_content
            time = datetime.datetime.now()

            msg = f":pencil: `{time.strftime(fmt)}` **Channel**: {before.channel.mention}(`{before.channel.id}`) **" \
                  f"{before.author}(`{before.author.id}`)'s** message(`{before.id}`) has been edited.\nBefore: " \
                  f"{cleanbefore}\nAfter: {cleanafter} "
            await channel.send(msg)

    async def on_guild_update(self, before, after):
        if before == self.bot.home:
            set_home(self.bot)
        guild = before
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            if before.name != after.name:
                msg = f':globe_with_meridians: `{time.strftime(fmt)}` guild name update. Before: **{before.name}** ' \
                      f'After: **{after.name}**. '
                await channel.send(msg)
            if before.region != after.region:
                msg = f':globe_with_meridians: `{time.strftime(fmt)}` guild region update. Before: **' \
                      f'{before.region}** After: **{after.region}**. '
                await channel.send(msg)
            if before.icon != after.icon:
                msg = f':globe_with_meridians: `{time.strftime(fmt)}` guild icon update. Before: **' \
                      f'{before.icon_url}** After: **{after.icon_url}**. '
                await channel.send(msg)
            if before.emojis != after.emojis:
                for i in before.emojis:
                    emojis = str(i)
                    msg = f':globe_with_meridians: `{time.strftime(fmt)}` Emoji update. Before: **{emojis}**.'
                    await channel.send(msg)
                for i in after.emojis:
                    emojis = str(i)
                    msg = f':globe_with_meridians: `{time.strftime(fmt)}` Emoji update. Before: **{emojis}**.'
                    await channel.send(msg)

    async def on_member_update(self, before, after):
        guild = before.guild
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            if not before.nick == after.nick:
                await channel.send(
                    f':person_with_pouting_face::skin-tone-3: `{time.strftime(fmt)}` **{before.name}** changed their '
                    f'nickname from **`{before.nick}`** to **`{after.nick}`**')
            if not before.name == after.name:
                await channel.send(
                    f':person_with_pouting_face::skin-tone-3: `{time.strftime(fmt)}` **{before.name}** changed their '
                    f'name from **`{before.name}`** to **`{after.name}`**')
            if not before.roles == after.roles:
                msg = f":person_with_pouting_face::skin-tone-3: `{time.strftime(fmt)}` **{before.name}'s** roles have" \
                      f" changed. Old: `{', '.join([r.name for r in before.roles])}` New: " \
                      f"`{', '.join([r.name for r in after.roles])}` "
                await channel.send(msg)
            if not before.bot:
                if not before.avatar == after.avatar:
                    await channel.send(
                        f':person_with_pouting_face::skin-tone-3: `{time.strftime(fmt)}` **{before.name}** changed '
                        f'their avatar from **{before.avatar_url}** to **{after.avatar_url}**')

    async def on_member_ban(self, guild, member):
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            msg = f':hammer: `{time.strftime(fmt)}` {member}({member.id}) has been banned!'
            await channel.send(msg)

    async def on_member_unban(self, guild, member):
        db: GuildEntry = await models.get_guild(self.bot, guild)
        modlog_channel = db.modlog_channel
        if modlog_channel:
            channel = self.bot.get_channel(int(modlog_channel))
            time = datetime.datetime.now()
            msg = f'🕊 `{time.strftime(fmt)}` {member}({member.id}) has been Unbanned!'
            await channel.send(msg)


def setup(bot):
    bot.add_cog(ModlogHandler(bot))
