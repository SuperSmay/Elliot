import traceback
import math

import discord
from discord.ext import commands, tasks
import datetime

from globalVariables import bot, last_start_time, bot_version

class BotInfo(commands.Cog):
    def __init__(self):
        pass

    @commands.command(name='info', description='Show\'s some stats about Elliot')
    async def info_prefix(self, ctx):
        await ctx.reply(embed=self.run_and_get_response(), mention_author=False)

    @commands.slash_command(name='info', description='Show\'s some stats about Elliot')
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
        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name}\'s Stats ☾∘∙⊱⋅•⋅', description=f'Statistics for {bot.user.name}', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.add_field(name='Ping', value=f'{round(bot.latency*1000, 2)}ms')
        embed.add_field(name='Uptime', value=f'{self.parse_duration((datetime.datetime.utcnow() - last_start_time).total_seconds())}')
        embed.add_field(name='Version', value=f'v{bot_version}')
        embed.add_field(name='Commands', value=f'{len(bot.application_commands)}')
        embed.set_footer(text=f'{bot.user.name}#{bot.user.discriminator} - {bot.user.id}')
        return embed

    def parse_duration(self, duration):
        '''
        Converts a time, in seconds, to a string in the format hr:min:sec, or min:sec if less than one hour.
    
        @type  duration: int
        @param duration: The time, in seconds

        @rtype:   string
        @return:  The new time, hr:min:sec
        '''

        #Divides everything into hours, minutes, and seconds
        hours = math.floor(duration / 3600)
        temp_time = duration % 3600 #Modulo takes the remainder of division, leaving the remaining minutes after all hours are taken out
        minutes = math.floor(temp_time / 60)
        seconds = round(temp_time % 60)

        #Formats time into a readable string
        new_time = ""
        if hours > 0: #Adds hours to string if hours are available; else this will just be blank
            new_time += str(hours) + ":"
        else: #If there are no hours, the place still needs to be held
            new_time += "00:"

        if minutes > 0:
            if minutes < 10: #Adds a 0 to one-digit times
                new_time += "0" + str(minutes) + ":"
            else:
                new_time += str(minutes) +":"
        else: #If there are no minutes, the place still needs to be held
            new_time += "00:"

        if seconds > 0:
            if seconds < 10: #Adds a 0 to one-digit times
                new_time += "0" + str(seconds)
            else:
                new_time += str(seconds)
        else:
            new_time += "00"

        return new_time
