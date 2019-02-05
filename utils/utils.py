import datetime
import random

import discord
import rethinkdb as r

random = random.SystemRandom()


def get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(random.choice(allowed_chars) for i in range(length))


def gen_key():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789.'
    return get_random_string(50, chars)


async def update(bot):
    for url, auth in bot.keys["bot_lists"].items():
        payload = {
            'server_count': bot.gcount
        }
        headers = {
            'authorization': auth,
            'content-type': 'application/json'
        }
        async with bot.session.post(url.format(bot.user.id), json=payload, headers=headers) as resp:
            bot.log.info(f'Updated {url}, Got {resp}')


def get_role_by_id(roles, role_id: int):
    return discord.utils.get(roles, id=role_id)


async def get_role_from_string(guild, rolename, roles=None):
    if roles is None:
        roles = guild.roles
    roles = [role for role in roles if (r is not None)]
    role = discord.utils.find((lambda role: (role.name.lower() == rolename.lower())), roles)
    return role


def get_bot_uptime(self, *, brief=False):
    now = datetime.datetime.utcnow()
    delta = now - self.bot.uptime
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    if not brief:
        if days:
            fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h} hours, {m} minutes, and {s} seconds'
    else:
        fmt = '{h} hours {m} minutes and {s} seconds'
        if days:
            fmt = ('{d} days ' + fmt)
    return fmt.format(d=days, h=hours, m=minutes, s=seconds)
