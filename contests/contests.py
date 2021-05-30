"""discord red-bot contests"""
import discord
import io
import mimetypes
import hashlib
import json
from redbot.core import Config, checks, commands

class ContestsCog(commands.Cog):
    """Contests Cog"""

    def __init__(self,bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=879255658497795933747566)

        default_guild_config = {
            "posting_channel": None,
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

    @_contests.command(name="draw")
    async def draw_entry(self, ctx, entry_id):
        """Draws a winner for the contest

        Usage:
        - `[p]contests draw <post_id`
        """
        async with ctx.channel.typing():
            contests_database_temp = await self.config.guild(ctx.guild).contests_database()
            channel_id = await self.config.guild(ctx.guild).posting_channel()
            channel = ctx.guild.get_channel(channel_id)
            await channel.send(content=f"<@{contests_database_temp[entry_id]['author_id']}>")



    @commands.guild_only()
    @_contests.command(name="submit")
    async def submit_entry(self, ctx):
        """Submit a contest entry

        Usage:
        - `[p]contests submit <link to image or attach an image>`
        """
        async with ctx.channel.typing():
            channel_id = await self.config.guild(ctx.guild).posting_channel()
            channel = ctx.guild.get_channel(channel_id)
            error_channel = ctx.guild.get_channel(ctx.message.channel.id)
            if ctx.message.attachments is not None:
                tempfile = await ctx.message.attachments[0].read()
                mimetype = ctx.message.attachments[0].content_type
                if "image/" not in mimetype:
                    await error_channel.send(
                        content="Please upload an image, not another type of file.",
                        reference=ctx.message,
                        mention_author=True
                    )
                    break
                else:
                     extension = mimetypes.guess_extension(mimetype)
                     author = ctx.message.author.name
                     author_id = ctx.message.author.id
                     try:
                         await ctx.message.delete()
                     except:
                         await error_channel.send(
                             content="Unable to delete submission request automatically, please delete your post yourself.",
                             delete_after=60,
                             reference=ctx.message,
                             mention_author=True
                         )
                     filehash = hashlib.md5(tempfile)
                     filename = filehash.hexdigest()
                     complete_name = f"{filename}{extension}"
                     discordfile = discord.File(filename=complete_name, fp=(io.BytesIO(tempfile)))
                     await channel.send(content=filename, file=discordfile)
                     contests_database_temp = await self.config.guild(ctx.guild).contests_database()
                     if type(contests_database_temp) is not dict:
                         contests_database_temp = {}
                     contests_database_temp[filename] = {
                         "author": author,
                         "author_id": author_id,
                     }
                     await self.config.guild(ctx.guild).contests_database.set(contests_database_temp)
            else:
                await error_channel.send(
                    content="Submission failed. Please attach an image to your message.",
                    reference=ctx.message,
                    mention_author=True
                )

