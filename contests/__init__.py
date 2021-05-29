from .contests import ContestsCog

def setup (bot):
    bot.add_cog(ContentsCog(bot))
