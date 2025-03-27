from .guesstheflag import GuessTheFlag

async def setup(bot):
    await bot.add_cog(GuessTheFlag(bot))
