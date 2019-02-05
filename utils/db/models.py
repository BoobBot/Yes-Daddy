import datetime
import sys

import discord
import rethinkdb as r
from rethinkdb import *
import json
# this will likely be a big file so lets use comments so i dont get lost in 4 weeks


# define the Guild class
class GuildEntry:
    def __init__(self, bot, data):
        self.bot = bot
        self._id = data["id"]
        self._blacklisted = data["blacklisted"]
        self._prefix = data["prefix"]
        self._modlog_channel = data["modlog_channel"]
        self._auto_role = data["auto_role"]
        self._auto_role_bot = data["auto_role_bot"]
        self._invite_tracker = data["invite_tracker"]
        self._snipe = data.get("snipe", {"enabled": None, "data": {}})
        self.guild_added = data["guild_added"]

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._prefix = prefix

    @property
    def blacklisted(self):
        return self._blacklisted

    @blacklisted.setter
    def blacklisted(self, blacklisted: bool):
        self._blacklisted = blacklisted

    @property
    def modlog_channel(self):
        return self._modlog_channel

    @modlog_channel.setter
    def modlog_channel(self, modlog_channel: str):
        self._modlog_channel = modlog_channel

    @property
    def auto_role(self):
        return self._auto_role

    @auto_role.setter
    def auto_role(self, auto_role: str):
        self._auto_role = auto_role

    @property
    def auto_role_bot(self):
        return self._auto_role_bot

    @auto_role_bot.setter
    def auto_role_bot(self, auto_role_bot: str):
        self._auto_role_bot = auto_role_bot

    @property
    def invite_tracker(self):
        return self._invite_tracker

    @invite_tracker.setter
    def invite_tracker(self, invite_tracker):
        self._invite_tracker = invite_tracker

    @property
    def snipe(self):
        return self._snipe

    @snipe.setter
    def snipe(self, snipe):
        self._snipe - snipe

    def guild_added(self):
        return self.guild_added

    async def save(self):
        await r.table('guilds').insert({
            "id": self._id,
            "blacklisted": self._blacklisted,
            "prefix": self._prefix,
            "modlog_channel": self._modlog_channel,
            "auto_role": self._auto_role,
            "auto_role_bot": self._auto_role_bot,
            "snipe": self._snipe,
            "guild_added": self.guild_added,
            "invite_tracker": self._invite_tracker
        }, conflict="replace").run(self.bot.conn)


#########################################################
# db init things
#########################################################
def check_db():
    json_file = open('config/config.json', mode="r")
    config = json.load(json_file)
    json_file.close()
    try:
        con = r.connect()
        try:
            d = r.db_create(config['db']).run(con)
            print(d)
        except ReqlRuntimeError:
            pass
        for t in config["tables"]:
            try:
                t = r.db(config['db']).table_create(t).run(con)
                print(t)
            except ReqlOpFailedError:
                continue
        con.close()
        r.set_loop_type("asyncio")
    except RqlDriverError as e:
        print(f"{e}\n\rRethinkDb running?\nexiting...")
        sys.exit()


async def check_and_create_guild(bot, guild):
    if not await r.table("guilds").get(str(guild.id)).run(bot.conn):
        time_now = datetime.datetime.today()
        await r.table('guilds').insert({
            "id": str(guild.id),
            "blacklisted": False,
            "prefix": None,
            "modlog_channel": None,
            "auto_role": None,
            "auto_role_bot": None,
            "invite_tracker": {"Channel": None, "Invites": {}},
            "snipe": {"enabled": None, "data": {}},
            "guild_added": str(time_now.strftime("%A, %B %d %Y, %I:%M:%S %p"))
        }, conflict="update").run(bot.conn)
        bot.log.info(f"added guild {str(guild.name)}")


async def get_guild(bot, guild):
    guild_id = str(guild.id)
    guild = await r.table('guilds').get(guild_id).run(bot.conn)
    if not guild:
        await check_and_create_guild(bot, bot.get_guild(int(guild_id)))
        guild = await r.table('guilds').get(guild_id).run(bot.conn)
    guild = GuildEntry(bot, guild)
    return guild


#########################################################
# prefix things
#########################################################
async def get_prefix(bot, msg):
    if bot.debug:
        return bot.config["debug_prefix"]
    if isinstance(msg.channel, discord.abc.PrivateChannel):
        # Dm`s
        return bot.config["dm_prefix"]
    try:
        g = await get_guild(bot, msg.guild)
        if g and g.prefix:
            return [msg.guild.me.mention + " ", g.prefix]
        else:
            prefixes = [msg.guild.me.mention + " "]
            [prefixes.append(x) for x in bot.config["prefixes"]]
            return prefixes
    except Exception as e:
        bot.log.error(e)
        prefixes = [msg.guild.me.mention + " "]
        [prefixes.append(x) for x in bot.config["prefixes"]]
        return prefixes
