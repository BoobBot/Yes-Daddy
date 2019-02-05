import discord
from discord.ext import commands

from utils.ctx import CustomContext


# :(
async def on_message(message):
    pass


class MessageHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command(self, ctx: commands.Context):
        cmd = ctx.command.qualified_name.replace(' ', '_')
        self.bot.commands_used[cmd] += 1
        message = ctx.message
        if isinstance(ctx.message.channel, discord.abc.PrivateChannel):
            destination = 'Private Message'
        else:
            destination = f'#{message.channel.name} ({message.guild.name})'

        self.bot.log.info(f'{message.created_at}: {message.author.name} in {destination}: {message.content}')

    async def process_commands(self, message: discord.Message):
        ctx = await self.bot.get_context(message, cls=CustomContext)
        if ctx.command is None:
            return
        await self.bot.invoke(ctx)

    async def on_message(self, message: discord.Message):
        self.bot.messages_sent += 1
        if message.mention_everyone:
            self.bot.at_everyone_seen += 1
        if message.author.bot:
            return
        await self.process_commands(message)


def setup(bot):
    bot.event(on_message)
    bot.add_cog(MessageHandler(bot))
