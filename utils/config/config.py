import json

import aiofiles as fs
import random


async def get_config():
    file = await fs.open('config/config.json', mode="r")
    lines = await file.read()
    return json.loads(lines)


async def get_keys():
    file = await fs.open('config/keys.json', mode="r")
    lines = await file.read()
    return json.loads(lines)


async def get_proxy():
    keys = await get_keys()
    return f'http://{random.choice(keys["proxies"])}'


async def get_imagur_id():
    keys = await get_keys()
    return f'Client-ID {random.choice(keys["imagur_ids"])}'


def set_home(bot):
    bot.home = bot.get_guild(int(bot.config["home"]))



