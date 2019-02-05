import datetime

import discord
from discord import Webhook, AsyncWebhookAdapter

from utils.config.config import set_home
from utils.db.models import check_and_create_guild
from utils import formats


class Ready:
    def __init__(self, bot):
        self.bot = bot
        self.once = False

    async def on_connect(self):
        self.bot.gateway_server_name = self.bot.shards[0].ws._trace[0]
        self.bot.session_server_name = self.bot.shards[0].ws._trace[1]

    async def on_resumed(self):
        print(dir(self))
        self.bot.gateway_server_name = self.bot.shards[0].ws._trace[0]
        self.bot.session_server_name = self.bot.shards[0].ws._trace[1]

    async def on_ready(self):
        set_home(self.bot)
        self.bot.gateway_server_name = self.bot.shards[0].ws._trace[0]
        self.bot.session_server_name = self.bot.shards[0].ws._trace[1]
        for x in self.bot.guilds:
            await check_and_create_guild(self.bot, x)
        guilds = str(len(self.bot.guilds))
        users = str(len(set(self.bot.get_all_members())))
        info = f"\nConnected {formats.get_emoji_by_name(':zap:')}\n" \
               f"Gateway server {formats.get_emoji_by_name(':globe_with_meridians:')}: " \
               f"{self.bot.gateway_server_name}\n" \
               f"session server {formats.get_emoji_by_name(':lock:')}: {self.bot.session_server_name}\n" \
               f"Logged in {formats.get_emoji_by_name(':satellite:')}\n" \
               f"User {formats.get_emoji_by_name(':bust_in_silhouette:')}: " \
               f"{self.bot.user.name}({str(self.bot.user.id)})\n" \
               f"Avatar {formats.get_emoji_by_name(':rice_scene:')}:\n" \
               f"{self.bot.user.avatar_url_as(static_format='png', size=512)}\n" \
               f"oauth link {formats.get_emoji_by_name(':link:')}:\n{discord.utils.oauth_url(self.bot.user.id)}\n" \
               f"guilds {formats.get_emoji_by_name(':bar_chart:')}: {guilds}\n" \
               f"Users {formats.get_emoji_by_name(':bar_chart:')}: {users}\n" \
               f"Home {formats.get_emoji_by_name(':house:')}: {self.bot.home.name}\n" \
               f"Home users {formats.get_emoji_by_name(':bar_chart:')}: {str(len(set(self.bot.home.members)))}\n"
        self.bot.log.info(info)

        for x in range(self.bot.shard_count):
            message = "with hammers 🔨"
            # '!help | shard {}/{} | {} guilds | {} users'.format(x + 1, self.bot.shard_count, guilds, users)
            game = discord.Game(name=message, type=2)
            self.bot.log.info("logged in and ready on shard: {} and set status as ".format(x + 1) + message)
            await self.bot.change_presence(activity=game, shard_id=x)
        res = await self.bot.session.get(self.bot.user.avatar_url_as(static_format='png', size=1024))
        data = await res.read()
        webhook = Webhook.from_url(self.bot.keys['ready_wh'], adapter=AsyncWebhookAdapter(self.bot.session))
        await webhook.edit(name="on_ready", avatar=data)
        if self.bot.debug:
            self.bot.log.info(f'Is running in Debug, prefix is now {self.bot.config["debug_prefix"]}')

        time = datetime.datetime.now()
        fmt = '[ %H:%M:%S ] %d-%B-%Y'
        em = discord.Embed(title=f"{self.bot.user.name} Restarted",
                           description=info,
                           colour=0x20B2AA)
        em.set_author(name='', url=self.bot.user.avatar_url, icon_url=self.bot.user.avatar_url)
        em.set_footer(text=time.strftime(fmt),
                      icon_url=self.bot.user.avatar_url)
        await webhook.send(embed=em)
        self.bot.log.info("Finished on ready task")




def setup(bot):
    bot.add_cog(Ready(bot))
