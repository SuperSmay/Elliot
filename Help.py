import traceback

import discord
from discord.ext import commands

from globalVariables import bot

class Help(commands.Cog):
    def __init__(self):
        self.page = 0
        self.maxPages = 0

    @commands.command(name='help', description='A full list of commands for Elliot')
    async def info_prefix(self, ctx):
        await ctx.reply(embed=self.run_and_get_response(), mention_author=False)

    @commands.slash_command(name='help', description='A full list of commands for Elliot')
    async def info_slash(self, ctx):
        await ctx.respond(embed=self.run_and_get_response())

    def run_and_get_response(self):  #Replys with the embed or an error
        try:
            return self.embed()
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\Smay\\Dropbox\\AmesBot", "bot")
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return embed

    def embed(self):
        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name} Commands ☾∘∙⊱⋅•⋅', description=f'An exhaustive list of {bot.user.name}\'s commands', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        for i in bot.cogs:
            items = ''
            commands = bot.cogs.get(i).get_commands()
            for j in commands:
                items = f'{items}, {j.qualified_name}'
            items.removesuffix(',')
            embed.add_field(name=i, value=items)

        embed.add_field(name='Commands', value=f'{len(bot.application_commands)}')
        embed.set_footer(text=f'Page {self.page} of {self.maxPages}')
        return embed
