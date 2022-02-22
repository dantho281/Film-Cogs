"""discord red-bot contests"""
import discord
import io
import mimetypes
import hashlib
from redbot.core import Config, checks, commands


class ReactionVote:
    def __init__(self, bot, guild, emote, user, message, entries):
        self.bot = bot
        self.guild = guild
        self.emote = emote
        self.user = user
        self.message = message
        self.entries = entries


class ReplaceVote:
    def __init__(self, bot, old_vote, new_vote, user_id, entries, guild):
        self.bot = bot
        self.old_vote = old_vote
        self.new_vote = new_vote
        self.user_id = user_id
        self.entries = entries
        self.guild = guild


class ContestsCog(commands.Cog):
    """Contests Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=879255658497795933747566)

        default_guild_config = {
            "posting_channel": None,
            "listen_channel": None
        }

        self.config.register_guild(**default_guild_config)

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if ctx.author.bot or not ctx.guild:
            return
        listen_channel = await self.config.guild(ctx.guild).listen_channel()
        if listen_channel is None:
            return
        if ctx.channel.id != listen_channel:
            return
        async with ctx.channel.typing():
            error_channel = ctx.guild.get_channel(ctx.channel.id)
            channel_id = await self.config.guild(ctx.guild).posting_channel()
            channel = ctx.guild.get_channel(channel_id)
            if len(ctx.attachments) > 0:
                tempfile = await ctx.attachments[0].read()
                mimetype = ctx.attachments[0].content_type
                if "image/" in mimetype:
                    extension = mimetypes.guess_extension(mimetype)
                    author = ctx.author.name
                    author_id = ctx.author.id
                    try:
                        await ctx.delete()
                    except:
                        await error_channel.send(
                            content="Unable to delete submission request automatically, please delete your post yourself.",
                            delete_after=20,
                            reference=ctx,
                            mention_author=True
                        )
                    filehash = hashlib.md5(tempfile)
                    filename = filehash.hexdigest()
                    contests_database_temp = await self.config.guild(ctx.guild).contests_database()
                    if type(contests_database_temp) is not dict:
                        contests_database_temp = {}
                    if filename in contests_database_temp:
                        await error_channel.send(
                            content=f"<@{author_id}> this image has been submitted previously, duplicate submissions are not allowed."
                        )
                    else:
                        complete_name = f"{filename}{extension}"
                        discordfile = discord.File(filename=complete_name, fp=(io.BytesIO(tempfile)))
                        message = await channel.send(content=filename, file=discordfile)
                        contests_database_temp[filename] = {
                            "author": author,
                            "author_id": author_id,
                            "votes": {
                                "one": [],
                                "two": [],
                                "three": [],
                            },
                        }
                        await self.config.guild(ctx.guild).contests_database.set(contests_database_temp)
                        await message.add_reaction('1️⃣')
                        await message.add_reaction('2️⃣')
                        await message.add_reaction('3️⃣')
                else:
                    await error_channel.send(
                        content="Please upload an image, not another type of file.",
                        delete_after=20,
                        reference=ctx,
                        mention_author=True
                    )
                    try:
                        await ctx.delete()
                    except:
                        await error_channel.send(
                            content="Unable to delete submission request automatically, please delete your post yourself.",
                            delete_after=20,
                            reference=ctx,
                            mention_author=True
                        )
            else:
                try:
                    await ctx.delete()
                except:
                    await error_channel.send(
                        content="Unable to delete submission request automatically, please delete your post yourself.",
                        delete_after=20,
                        reference=ctx,
                        mention_author=True
                        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            # this is a DM
            return

        if payload.member.bot:
            # Don't operate on bot reacts
            return

        guild = self.bot.get_guild(payload.guild_id)
        operating_channel = await self.config.guild(guild).posting_channel()
        if payload.channel_id != operating_channel:
            # Only operate inside the contest channel
            return

        if str(payload.emoji) == "1️⃣" or str(payload.emoji) == "2️⃣" or str(payload.emoji) == "3️⃣":
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            entries = await self.config.guild(guild).contests_database()
            reaction = ReactionVote(
                self,
                guild,
                str(payload.emoji),
                payload.user_id,
                message,
                entries
            )
            if str(payload.emoji) == "1️⃣":
                entries[message.content]['votes']['one'].append(payload.user_id)
                await self.config.guild(guild).contests_database.set(entries)
            if str(payload.emoji) == "2️⃣":
                entries[message.content]['votes']['two'].append(payload.user_id)
                await self.config.guild(guild).contests_database.set(entries)
            if str(payload.emoji) == "3️⃣":
                entries[message.content]['votes']['three'].append(payload.user_id)
                await self.config.guild(guild).contests_database.set(entries)
            message.remove_reaction(str(payload.emoji), payload.member)

    async def replace_vote(vote, old_vote=None):
        if old_vote is None:
            del vote.entries[vote.message.content]["votes"][vote.old_vote][vote.old_vote.index(vote.user_id)]
            vote.entries[vote.message.content]["votes"][vote.new_vote].append(vote.user_id)
            await vote.bot.config.guild(vote.guild).contests_database.set(vote.entries)
        if old_vote is not None:
            del old_vote.old_vote[vote.old_vote.index(vote.user_id)]
            vote.entries[vote.message.content]["votes"][vote.new_vote].append(vote.user_id)
            await vote.bot.config.guild(vote.guild).contests_database.set(vote.entries)

    def check_duplicate_reaction(reaction):
        if str(reaction.emote) == "1️⃣":
            newvote = "one"
        if str(reaction.emote) == "2️⃣":
            newvote = "two"
        if str(reaction.emote) == "3️⃣":
            newvote = "three"
        # Check if you've already voted on this entry
        for rating in ["one", "two", "three"]:
            if reaction.entries[reaction.message.content]["votes"][rating][reaction.user]:
                vote = ReplaceVote(
                    reaction.bot,
                    reaction.entries[reaction.message.content]["votes"][rating].
                    reaction.entries[reaction.message.content]["votes"][newvote],
                    reaction.user,
                    reaction.entries,
                    reaction.guild
                )
                ContestsCog.replace_vote(vote)
                break
        # Check if you've already put this vote on another entry
        for entry in reaction.entries:
            if entry["votes"][newvote][reaction.user]:
                vote = ReplaceVote(
                    reaction.bot,
                    reaction.entries[reaction.message.content]["votes"][rating].
                    reaction.entries[reaction.message.content]["votes"][newvote],
                    reaction.user,
                    reaction.entries,
                    reaction.guild
                )
                old_vote = ReplaceVote(
                    reaction.bot,
                    entry["votes"][rating],
                    reaction.entries[reaction.message.content]["votes"][newvote],
                    reaction.user,
                    reaction.entries,
                    reaction.guild
                )
                ContestsCog.replace_vote(vote, old_vote)
                break

    @commands.group(name="contest")
    async def _contests(self, ctx):
        pass

    @commands.guild_only()
    @checks.mod()
    @_contests.command(name="setpostchannel")
    async def set_posting_channel(self, ctx, channel: discord.TextChannel):
        """Set the submission posting channel for this server.

        Usage:
        - `[p]contests setpostchannel <channel>`
        """
        await self.config.guild(ctx.guild).posting_channel.set(channel.id)
        check_value = await self.config.guild(ctx.guild).posting_channel()
        success_embed = discord.Embed(
            title="Submissions channel set!",
            description=f"Submissions channel set to <#{check_value}>",
            colour=await ctx.embed_colour()
        )
        await ctx.send(embed=success_embed)

    @_contests.command(name="setlistenchannel")
    async def set_listening_channel(self, ctx, channel: discord.TextChannel):
        """Set the submission listening channel for this server.

        Usage:
        - `[p]contests setlistenchannel <channel>`
        """
        await self.config.guild(ctx.guild).listen_channel.set(channel.id)
        check_value = await self.config.guild(ctx.guild).listen_channel()
        success_embed = discord.Embed(
            title="Listening channel set!",
            description=f"Listening channel set to <#{check_value}>",
            colour=await ctx.embed_colour()
        )
        await ctx.send(embed=success_embed)

    @_contests.command(name="draw")
    async def draw_entry(self, ctx, entry_id):
        """Draws a winner for the contest

        Usage:
        - `[p]contests draw <post_id>`
        """
        async with ctx.channel.typing():
            contests_database_temp = await self.config.guild(ctx.guild).contests_database()
            channel = ctx.guild.get_channel(ctx.message.channel.id)
            try:
                await channel.send(content=f"<@{contests_database_temp[entry_id]['author_id']}>")
            except:
                await channel.send(content="Invalid post ID provided, please check again.")

    @_contests.command(name="reset")
    async def reset_contests(self, ctx):
        """Reset the current contest records

        Usage:
        [p]contests reset
        """
        error_channel = ctx.guild.get_channel(ctx.message.channel.id)
        reset_database = {}
        try:
            await self.config.guild(ctx.guild).contests_database.set(reset_database)
            await error_channel.send(
                content="Reset contest successfully.",
                delete_after=20,
                reference=ctx.message,
                mention_author=True
            )
        except:
            await error_channel.send(
                content="Unable to reset contest.",
                delete_after=20,
                reference=ctx.message,
                mention_author=True
            )

    @commands.guild_only()
    @_contests.command(name="submit")
    async def submit_entry(self, ctx):
        """Submit a contest entry

        Usage:
        - `[p]contests submit <attach an image>`
        """
        async with ctx.channel.typing():
            channel_id = await self.config.guild(ctx.guild).posting_channel()
            channel = ctx.guild.get_channel(channel_id)
            error_channel = ctx.guild.get_channel(ctx.message.channel.id)
            if len(ctx.message.attachments) > 0:
                tempfile = await ctx.message.attachments[0].read()
                mimetype = ctx.message.attachments[0].content_type
                if "image/" in mimetype:
                    extension = mimetypes.guess_extension(mimetype)
                    author = ctx.message.author.name
                    author_id = ctx.message.author.id
                    try:
                        await ctx.message.delete()
                    except:
                        await error_channel.send(
                            content="Unable to delete submission request automatically, please delete your post yourself.",
                            delete_after=20,
                            reference=ctx.message,
                            mention_author=True
                        )
                    filehash = hashlib.md5(tempfile)
                    filename = filehash.hexdigest()
                    contests_database_temp = await self.config.guild(ctx.guild).contests_database()
                    if type(contests_database_temp) is not dict:
                        contests_database_temp = {}
                    if filename in contests_database_temp:
                        await error_channel.send(
                            content=f"<@{author_id}> this image has been submitted previously, duplicate submissions are not allowed."
                        )
                    else:
                        complete_name = f"{filename}{extension}"
                        discordfile = discord.File(filename=complete_name, fp=(io.BytesIO(tempfile)))
                        await channel.send(content=filename, file=discordfile)
                        contests_database_temp[filename] = {
                            "author": author,
                            "author_id": author_id,
                        }
                        await self.config.guild(ctx.guild).contests_database.set(contests_database_temp)
                else:
                    await error_channel.send(
                        content="Please upload an image, not another type of file.",
                        reference=ctx.message,
                        mention_author=True
                    )
            else:
                await error_channel.send(
                    content="Submission failed. Please attach an image to your message.",
                    reference=ctx.message,
                    mention_author=True
                )

