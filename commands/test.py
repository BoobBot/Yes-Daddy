from discord.ext import commands

from utils.checks import checks


class Test:
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 15000, type=commands.BucketType.guild)
    @commands.command(hidden=True)
    @checks.is_bot_owner()
    async def test(self, ctx):
        self.thisshoulderror


def setup(bot):
    bot.add_cog(Test(bot))
