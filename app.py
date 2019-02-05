import atexit

import discord
from discord.ext.commands import AutoShardedBot

from utils.db.models import get_prefix, check_db
from utils.config.setup_bot import setup_bot, shut_down
from utils.config.setup_bot import setup_logger


description = "a bot"


class Bot(AutoShardedBot):
    def __init__(self):
        atexit.register(shut_down, self)
        message = 'dhelp | dinvite'
        sgame = discord.Game(name=message, type=0)
        super().__init__(command_prefix=get_prefix, game=sgame, description=description)
        setup_bot(self)
        token = self.keys['debug_token'] if self.debug else self.keys['token']
        try:
            self.loop.run_until_complete(self.start(token))
        except discord.errors.LoginFailure or discord.errors.HTTPException as e:
            self.log.error(f"shit: {repr(e)}", exc_info=False)


if __name__ == "__main__":
    setup_logger()
    check_db()
    Bot()
