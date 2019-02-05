from discord.ext import commands
import discord


def check_hierarchy(ctx: commands.Context, role: discord.Role):
    return ctx.guild.me.top_role.position > role.position


def can_send(ctx: commands.Context):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).send_messages


def can_embed(ctx: commands.Context):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).embed_links


def can_delete(ctx: commands.Context):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).manage_messages


def can_ban(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).ban_members and check_hierarchy(ctx, member.top_role)


def can_kick(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).kick_members and check_hierarchy(ctx, member.top_role)


def can_edit_user_nick(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).manage_nicknames and check_hierarchy(ctx, member.top_role)


def can_edit_channel(ctx: commands.Context):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).manage_channels


def can_edit_role(ctx: commands.Context, role: discord.Role):
    if not ctx.guild:
        return False
    return ctx.guild.me.permissions_in(ctx.channel).manage_roles and check_hierarchy(ctx, role)
