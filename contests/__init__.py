from .contests import ContestsCog

def setup (bot):
    bot.add_cog(ContestsCog(bot))
