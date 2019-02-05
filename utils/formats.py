import textwrap
from typing import Sequence, Iterator

import aiohttp
import emoji
import discord
import rethinkdb as r
from discord.ext import commands
from discord.ext.commands import AutoShardedBot

from utils.checks.bot_checks import can_send, can_embed


# https://www.webpagefx.com/tools/emoji-cheat-sheet/
def get_emoji_by_name(name: str):
    return emoji.emojize(name, True)


def pagify(text: str, page_length: int = 1900,):
    return textwrap.wrap(text, page_length, break_long_words=False)


def escape(text: str):
    text = text.replace("@everyone", "@\u200beveryone")
    text = text.replace("@here", "@\u200bhere")
    return text


async def embed(ctx: commands.Context, text: str, color: discord.Color=discord.Color.purple()):
    if not can_send(ctx):
        return
    if not can_embed(ctx):
        await ctx.channel.send(f"{get_emoji_by_name(':x:')} **error** You must give this bot embed permissions")
    em = discord.Embed(description=text, color=color)
    await ctx.send(embed=em)


def get_icon():
    file = open("res/banner.txt")
    return file.read()


async def create_gist(bot: AutoShardedBot,
                      description: str,
                      filename: str, content: str,
                      public: bool=True,
                      session: aiohttp.ClientSession=None):

    api_uri = "https://api.github.com/gists"
    headers = {
        "Authorization": f"token {bot.keys['gist_token']}",
        "Content-Type": "application/json"
    }

    payload = {
        "description": description,
        "public": public,
        "files": {
            filename: {
                "content": content
            }
        }
    }
    try:
        res = await session.post(api_uri, headers=headers, json=payload)
        if res.status >= 200:
            data = await r.json()
            if 'message' in data:
                return "Failed to get gist"
            elif 'html_url' in data:
                return data['html_url']
            else:
                return "Failed to get gist"
        else:
            return "Failed to get gist"
    except aiohttp.client_exceptions as e:
        if bot.debug:
            bot.log.error(f"Failed to get gist: {repr(e)}", exc_info=True)
        else:
            bot.log.error(f"Failed to get gist: {repr(e)}", exc_info=False)
        return "Failed to get gist"
