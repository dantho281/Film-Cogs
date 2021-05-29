"""discord red-bot contests"""
import discord
from redbot.core import Config, checks, commands

class ContestsCog(commands.Cog):
    """Contests Cog"""

    def __init__(self,bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=879255658497795933747566)

        default_guild_config = {
            "posting_channel": None
        }

        self.config.register_guild(**default_guild_config)

    @commands.group(name="contest")
    async def _contests(self, ctx):
        pass

    @commands.guild_only()
    @checks.mod()
    @_contests.command(name="setchannel")
    async def set_posting_channel(self, ctx, channel: discord.TextChannel):
        """Set the submission posting channel for this server.

        Usage:
        - `[p]contests setchannel <channel>`
        """
        await self.config.guild(ctx.guild).posting_channel.set(channel.id)
        check_value = await self.config.guild(ctx.guild).posting_channel()
        success_embed = discord.Embed(
            title="Submissions channel set!",
            description=f"Submissions channel set to <#{check_value}>",
            colour=await ctx.embed_colour()
        )
        await ctx.send(embed=success_embed)
