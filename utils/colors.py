import io
import discord
from colorthief import ColorThief
import numpy as np

from discord.ext.commands import AutoShardedBot


async def get_effective_color(bot: AutoShardedBot, member: discord.Member):
    if member.color != discord.Color.default():
        return member.color
    dom_color = await get_dominant_color(bot, bot.get_user(member.id).avatar_url)
    if dom_color != discord.Color.default():
        return dom_color
    return get_random_color()


def get_random_color():
    color = list(np.random.choice(range(256), size=3))
    print(color[0])
    return discord.Color.from_rgb(int(color[0]), int(color[1]), int(color[2]))


async def get_dominant_color(bot: AutoShardedBot, url: str):
    async with bot.session.get(url) as resp:
        image = await resp.read()
    with io.BytesIO(image) as f:
        try:
            color = ColorThief(f).get_color(quality=10)
        except:
            return discord.Color.default()
    if not color:
        return discord.Color.default()
    return discord.Color.from_rgb(*color)
