from discord.ext import commands
import discord


def is_owner_check(ctx):
    return str(ctx.message.author.id) in ctx.bot.config["owners"]


def is_bot_owner():
    return commands.check(is_owner_check)


# TODO check role/db
def is_donor_check(ctx):
    return False


def is_donor():
    return commands.check(is_donor_check)


def check_permissions(ctx, perms):
    if is_owner_check(ctx):
        return True
    elif not perms:
        return False
    ch = ctx.message.channel
    author = ctx.message.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())


def role_or_permissions(ctx, check, **perms):
    if check_permissions(ctx, perms):
        return True
    ch = ctx.message.channel
    if isinstance(ch, discord.abc.PrivateChannel):
        return False
    if check:
        return True


def mod_or_permissions(**perms):
    def predicate(ctx):
        return role_or_permissions(ctx, ctx.message.author.permissions_in(ctx.message.channel).manage_roles, **perms)

    return commands.check(predicate)


def admin_or_permissions(**perms):
    def predicate(ctx):
        return role_or_permissions(ctx, ctx.message.author.permissions_in(ctx.message.channel).manage_guild, **perms)

    return commands.check(predicate)


def guild_owner_or_permissions(**perms):
    def predicate(ctx):
        guild = ctx.message.guild
        if not guild:
            return False

        if ctx.message.author.id == guild.owner.id:
            return True

        return check_permissions(ctx, perms)

    return commands.check(predicate)


def guild_owner():
    return guild_owner_or_permissions()


def admin():
    return admin_or_permissions()


def mod():
    return mod_or_permissions()
