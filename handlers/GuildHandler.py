import datetime

import discord
from discord import Webhook, AsyncWebhookAdapter

from utils.db.models import check_and_create_guild


class GuildLog:
    def __init__(self, bot):
        self.bot = bot
        self.once = False

    async def on_guild_join(self, guild):
        await check_and_create_guild(self.bot, guild)
        guilds = str(len(self.bot.guilds))
        users = str(len(set(self.bot.get_all_members())))
        for x in range(self.bot.shard_count):
            message = 'ydhelp | shard {}/{} | {} guilds | {} users'.format(x + 1, self.bot.shard_count, guilds, users)
            game = discord.Game(name=message, type=2)
            self.bot.log.info("joined: {} and set status as {} on shard {}".format(guild.name, message, x+1))
            await self.bot.change_presence(activity=game, shard_id=x)
        webhook = Webhook.from_url(self.bot.keys['guild_join_wh'], adapter=AsyncWebhookAdapter(self.bot.session))
        time = datetime.datetime.now()
        em = discord.Embed(title="New guild Added", color=discord.Color.green())
        em.set_author(name=guild.name, icon_url=guild.icon_url)
        em.set_thumbnail(url=guild.icon_url)
        em.add_field(name="Total users", value=str(len(guild.members)))
        em.add_field(name="guild Owner", value=str(guild.owner))
        em.add_field(name="Total guilds", value=str(len(self.bot.guilds)))
        em.set_footer(text="guild ID: " + str(guild.id))
        em.timestamp = time
        await webhook.send(username=guild.name, avatar_url=guild.icon_url if guild.icon else self.bot.user.avatar_url,
                           embed=em)

def setup(bot):
    bot.add_cog(GuildLog(bot))




