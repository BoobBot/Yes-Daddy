import datetime
from datetime import timedelta

import discord
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
import traceback
from utils.formats import pagify


class Error:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            await ctx.send_cmd_help(ctx)
        elif isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            await ctx.send_cmd_help(ctx)
        elif isinstance(error, commands.DisabledCommand):
            pass
        elif isinstance(error, commands.CommandOnCooldown):
            fmt = (str(error)).split()
            word = fmt[7].strip("s")
            time = float(word)
            timer = round(time, 0)
            delta = str(timedelta(seconds=int(timer))).lstrip("0").lstrip(":")
            await ctx.send(f"❌ lol, rate limits You can try again in `{delta}`")
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            ctx.command.reset_cooldown(ctx)
            pass
        elif isinstance(error, commands.BotMissingPermissions):
            ctx.command.reset_cooldown(ctx)
            await ctx.send(error.missing_perms)
        elif isinstance(error, commands.CheckFailure):
            ctx.command.reset_cooldown(ctx)
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Nope that command is not available in DMs.")

        else:
            if ctx.bot.debug:
                ctx.bot.log.error(f"shit: {repr(error)}", exc_info=True)
            else:
                ctx.bot.log.error(f"shit: {repr(error)}", exc_info=False)
            ctx.command.reset_cooldown(ctx)
            webhook = Webhook.from_url(ctx.bot.keys['error_wh'], adapter=AsyncWebhookAdapter(ctx.bot.session))
            await webhook.edit(name="Error")
            channel = ctx.message.channel
            t = datetime.datetime.now()
            avatar = ctx.bot.user.avatar_url
            fmt = '[ %I:%M:%S ] %B/%d/%Y'
            long = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            error_title = "Error"
            desc = '`{}: {}`'.format(type(error.original).__name__, str(error.original))
            em = discord.Embed(color=0xFF0000, description=desc)
            em.set_author(name=error_title, icon_url=avatar)
            em.set_footer(text=t.strftime(fmt))
            em.add_field(name="Content", value=ctx.message.content)
            em.add_field(name="Invoker", value="{}\n({})".format(ctx.message.author.mention, str(ctx.message.author)))
            c = "Private channel" if isinstance(ctx.message.channel, discord.abc.PrivateChannel) else \
                f"{channel.mention}\n({channel.name})"
            em.add_field(name="Channel", value=c)
            if not isinstance(ctx.message.channel, discord.abc.PrivateChannel):
                em.add_field(name="Guild", value=ctx.message.guild.name)
            await webhook.send(embed=em)
            print(long)
            pages = pagify(str(long))
            if pages:
                for page in pages:
                    await webhook.send(f"```py\n{page}\n```")
            er = f"Error in command '**__{ctx.command.qualified_name}__**' - `{type(error.original).__name__}`: `" \
                 f"{str(error.original)}` "
            e = discord.Embed(title="**Error** :x:", description="Error in command", color=0xFFC0CB)
            e.add_field(name="traceback", value=er)
            await channel.send(embed=e)


def setup(bot):
    bot.add_cog(Error(bot))
