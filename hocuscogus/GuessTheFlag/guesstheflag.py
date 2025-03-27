import discord
import random
import json
import os
from discord.ext import commands
from redbot.core import commands, Config

class GuessTheFlag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_guild(scores={})
        self.flags_path = os.path.join(os.path.dirname(__file__), "data", "flags")  # 本地存儲的標誌的路徑
    
    async def get_random_flag(self):
        """Escolhe uma bandeira aleatória e retorna seu nome e caminho."""
        files = [f for f in os.listdir(self.flags_path) if f.endswith(".png")]
        chosen_flag = random.choice(files)
        country_name = os.path.splitext(chosen_flag)[0]
        return country_name, os.path.join(self.flags_path, chosen_flag)
    
    async def get_options(self, correct_country):
        """Gera três opções erradas para acompanhar a correta."""
        files = [f for f in os.listdir(self.flags_path) if f.endswith(".png")]
        countries = [os.path.splitext(f)[0] for f in files if f != f"{correct_country}.png"]
        wrong_options = random.sample(countries, 3)
        options = wrong_options + [correct_country]
        random.shuffle(options)
        return options

    @commands.command()
    async def guessflag(self, ctx):
        """Inicia um jogo de adivinhação de bandeiras."""
        correct_country, flag_path = await self.get_random_flag()
        options = await self.get_options(correct_country)
        
        file = discord.File(flag_path, filename="flag.png")
        embed = discord.Embed(title="Adivinhe a bandeira!", color=discord.Color.blue())
        embed.set_image(url="attachment://flag.png")
        
        view = discord.ui.View()
        for option in options:
            view.add_item(FlagButton(option, correct_country, self))
        
        await ctx.send(embed=embed, file=file, view=view)

    async def update_score(self, guild, user):
        """Atualiza a pontuação do usuário."""
        scores = await self.config.guild(guild).scores()
        scores[user] = scores.get(user, 0) + 1
        await self.config.guild(guild).scores.set(scores)
    
    @commands.command()
    async def rank(self, ctx):
        """Mostra o ranking dos jogadores."""
        scores = await self.config.guild(ctx.guild).scores()
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(title="Ranking Global", color=discord.Color.gold())
        for idx, (user_id, score) in enumerate(sorted_scores[:10], start=1):
            user = self.bot.get_user(int(user_id)) or f"<@{user_id}>"
            embed.add_field(name=f"{idx}. {user}", value=f"Pontos: {score}", inline=False)
        
        await ctx.send(embed=embed)

class FlagButton(discord.ui.Button):
    def __init__(self, label, correct_country, cog):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.correct_country = correct_country
        self.cog = cog
    
    async def callback(self, interaction: discord.Interaction):
        if self.label == self.correct_country:
            await interaction.response.send_message(f"✅ Parabéns! Você acertou: {self.correct_country}!", ephemeral=True)
            await self.cog.update_score(interaction.guild, str(interaction.user.id))
        else:
            await interaction.response.send_message(f"❌ Errou! A resposta correta era {self.correct_country}.", ephemeral=True)
        
        self.view.stop()

async def setup(bot):
    await bot.add_cog(GuessTheFlag(bot))
