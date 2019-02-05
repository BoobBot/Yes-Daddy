import datetime
import logging
import os

import psutil
import sys
from collections.__init__ import Counter

import aiohttp
import rethinkdb as r
from rethinkdb import Connection
from discord.ext import commands
from discord.ext.commands import AutoShardedBot

from utils.config.config import get_keys, get_config
from utils.formats import get_emoji_by_name, get_icon
from utils.help.HelpFormater import EmbededHelp

logger = logging.getLogger()

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
TIME_SEQ = COLOR_SEQ % (30 + MAGENTA)
NAME_SEQ = COLOR_SEQ % (30 + CYAN)
FORMAT = "[$TIME_SEQ%(asctime)-3s$RESET]" \
         "[$NAME_SEQ$BOLD%(name)-2s$RESET]" \
         "[%(levelname)-1s]" \
         "[%(message)s]" \
         "[($BOLD%(filename)s$RESET:%(lineno)d)]"


def auto_reconnect(self):
    while self._instance is None or not self._instance.is_open():
        self.reconnect()


Connection.check_open = auto_reconnect


def setup_logger():
    color_format = formatter_message(FORMAT, True)
    logging.setLoggerClass(ColoredLogger)
    color_formatter = ColoredFormatter(color_format)
    console = logging.StreamHandler()
    file = logging.FileHandler(filename=f'logs/daddy.log', encoding='utf-8', mode='w')
    console.setFormatter(color_formatter)
    file.setFormatter(color_formatter)
    logger.addHandler(console)
    logger.addHandler(file)
    wh = WebHookHandler("k")
    logger.addHandler(wh)
    return logger


def formatter_message(message: str, colored: bool = True):
    if colored:
        message = message.replace("$RESET", RESET_SEQ)
        message = message.replace("$BOLD", BOLD_SEQ)
        message = message.replace("$TIME_SEQ", TIME_SEQ)
        message = message.replace("$NAME_SEQ", NAME_SEQ)
        return message
    else:
        message = message.replace("$RESET", "")
        message = message.replace("$BOLD", "")
        return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': BLUE,
    'DEBUG': WHITE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        level_name = record.levelname
        if self.use_color and level_name in COLORS:
            level_name_color = COLOR_SEQ % (30 + COLORS[level_name]) + level_name + RESET_SEQ
            record.levelname = level_name_color
        message = record.msg
        if self.use_color and level_name in COLORS:
            message_color = COLOR_SEQ % (30 + BLUE) + message + RESET_SEQ
            record.msg = message_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):
    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.INFO)
        return


class WebHookHandler(logging.Handler):
    def __init__(self, special_args):
        logging.Handler.__init__(self)

    def emit(self, record):
        # TODO add webhook to tails.fun (no rate-limits there), use this handler in Production for log output
        pass


class Formatter(commands.HelpFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def setup_bot(bot):
    bot.config = bot.loop.run_until_complete(get_config())
    bot.remove_command('help')
    discord_log = logging.getLogger('discord')
    log = logging.getLogger("main")
    discord_log.setLevel(logging.CRITICAL)
    bot.log, bot.logger, = log, log
    log.info(f"{get_icon()}\nLoading....\n")
    bot.formatter = EmbededHelp()
    bot.debug = any('debug' in arg.lower() for arg in sys.argv)
    bot.uptime = datetime.datetime.utcnow()
    bot.commands_used = Counter()
    bot.messages_sent = 0
    bot.process = psutil.Process()
    bot.at_everyone_seen = 0
    bot.session = aiohttp.ClientSession(loop=bot.loop)
    bot.keys = bot.loop.run_until_complete(get_keys())
    bot.config = bot.loop.run_until_complete(get_config())
    bot.conn = bot.loop.run_until_complete(r.connect("localhost", db=bot.config['db'], port=28015))
    bot.loop.run_until_complete(module_loader(bot, "handlers"))
    bot.loop.run_until_complete(module_loader(bot, "commands"))
    if bot.debug:
        discord_log.setLevel(logging.INFO)


def shut_down(bot: AutoShardedBot):
    bot.log.info("exiting, cleaning up things")
    bot.http._session.close()
    bot.session.close()
    bot.conn.close()
    handlers = logger.handlers[:]
    bot.log.info("bye o/")
    for h in handlers:
        h.close()
        logger.removeHandler(h)


async def module_loader(bot,
                        path: str,
                        name: str = None,
                        reload: bool = False,
                        unload: bool = False,
                        ctx: commands.Context = None):
    if unload and name:
        try:
            bot.unload_extension(f'{path}.{name}')
            if ctx:
                await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')},unloaded {path}/{name}")

        except Exception as e:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to unload {path}/{name}: : {repr(e)}")
            if bot.debug:
                bot.log.error(f"Failed to unload {path}/{name}: {repr(e)}", exc_info=True)
            else:
                bot.log.error(f"Failed to unload {path}/{name}: {repr(e)}", exc_info=False)
        return

    if unload:
        unloaded = 0
        err_counter = 0
        for file in os.listdir(f"{path}"):
            try:
                if file.endswith(".py"):
                    file_name = file[:-3]
                    bot.unload_extension(f"{path}.{file_name}")
                    unloaded += 1

            except Exception as e:
                err_counter += 1
                if bot.debug:
                    bot.log.error(f"Failed to unload {path}/{file_name}: {repr(e)}", exc_info=True)
                else:
                    bot.log.error(f"Failed to unload {path}/{file_name}: {repr(e)}", exc_info=False)
                continue
        if err_counter > 0 and unloaded < 1:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to unload {err_counter} {path}")

        if err_counter > 0 and unloaded > 0:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, "
                               f"Failed to unload {err_counter} {path}, "
                               f"Unloaded {unloaded} {path} ")

        if ctx:
            await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')}, Unloaded {unloaded} {path}")
        bot.log.info(f"Unloaded {unloaded} {path}")
        return

    if reload and name:
        try:
            bot.load_extension(f'{path}.{name}')
            if ctx:
                await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')}, Reloaded {path}/{name}")
                bot.log.info(f"Done {get_emoji_by_name(':ok_hand:')}, Reloaded {path}/{name}")

        except Exception as e:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to reload {path}/{name}: : {repr(e)}")
            if bot.debug:
                bot.log.error(f"Failed to reload {path}/{name}: {repr(e)}", exc_info=True)
            else:
                bot.log.error(f"Failed to reload {path}/{name}: {repr(e)}", exc_info=False)
        return

    if reload:
        reloaded = 0
        err_counter = 0
        for file in os.listdir(f"{path}"):
            try:
                if file.endswith(".py"):
                    file_name = file[:-3]
                    bot.unload_extension(f"{path}.{file_name}")
                    bot.load_extension(f"{path}.{file_name}")
                    reloaded += 1

            except Exception as e:
                err_counter += 1
                if bot.debug:
                    bot.log.error(f"Failed to reload {path}/{file_name}: {repr(e)}", exc_info=True)
                else:
                    bot.log.error(f"Failed to reload {path}/{file_name}: {repr(e)}", exc_info=False)
                continue

        if err_counter > 0 and reloaded < 1:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to reload {err_counter} {path}")

        if err_counter > 0 and reloaded > 0:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, "
                               f"Failed to reload {err_counter} {path}, "
                               f"Reloaded {reloaded} {path} ")

        if ctx:
            await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')}, Reloaded {reloaded} {path}")
        bot.log.info(f"Reloaded {reloaded} {path}")
        return

    if not name:
        loaded = 0
        err_counter = 0
        for file in os.listdir(f"{path}"):
            try:
                if file.endswith(".py"):
                    file_name = file[:-3]
                    bot.load_extension(f"{path}.{file_name}")
                    loaded += 1
            except Exception as e:
                err_counter += 1
                if bot.debug:
                    bot.log.error(f"Failed to load {path}/{file_name}: {repr(e)}", exc_info=True)
                else:
                    bot.log.error(f"Failed to load {path}/{file_name}: {repr(e)}", exc_info=False)
                continue

        if err_counter > 0 and loaded < 1:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to load {err_counter} {path}")
                return
        if err_counter > 0 and loaded > 0:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, "
                               f"Failed to load {err_counter} {path}, "
                               f"Loaded {loaded} {path} ")
            bot.log.error(f"{get_emoji_by_name(':rage:')}, "
                          f"Failed to load {err_counter} {path}, "
                          f"Loaded {loaded} {path} ")
            return
        if ctx:
            await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')}, Loaded {loaded} {path}")
        bot.log.info(f"Loaded {loaded} {path}")
        return

    if name:
        try:
            bot.load_extension(f'{path}.{name}')
            bot.log.info(f"Done {get_emoji_by_name(':ok_hand:')}, Loaded {path}/{name}")
            if ctx:
                await ctx.send(f"Done {get_emoji_by_name(':ok_hand:')}, Loaded {path}/{name}")

        except Exception as e:
            if ctx:
                await ctx.send(f"{get_emoji_by_name(':rage:')}, Failed to load {path}/{name}: : {repr(e)}")
            if bot.debug:
                bot.log.error(f"Failed to load {path}/{name}: {repr(e)}", exc_info=True)
            else:
                bot.log.error(f"Failed to load {path}/{name}: {repr(e)}", exc_info=False)
