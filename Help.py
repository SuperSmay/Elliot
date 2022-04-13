import traceback
import math

import discord
from discord.ext import commands

from globalVariables import bot
from discord import Option, SlashCommand

class Help(commands.Cog):
    def __init__(self):
        self.ITEMS_PER_PAGE = 5
        self.NUM_COGS = 1 #Starts at 1 to include this cog
        for i in bot.cogs:
            if len(bot.cogs.get(i).get_commands()) > 0:
                self.NUM_COGS += 1
        self.MAX_PAGES = math.floor(self.NUM_COGS / self.ITEMS_PER_PAGE)

    @commands.command(name='help', description='A full list of commands for Elliot')
    async def help_prefix(self, ctx, *args):
        await ctx.reply(embed=self.run_and_get_response(args), mention_author=False)

    @commands.slash_command(name='help', description='A full list of commands for Elliot')
    async def help_slash(self, ctx, command:Option(str, description='Which command to provide details for or the page number to display', required=False)):
        args = []
        if command != None: args += command.split(' ')
        await ctx.respond(embed=self.run_and_get_response(args))

    def run_and_get_response(self, args):  #Replys with the embed or an error
        try:
            if (len(args) == 0): #No arguments
                return self.full_help()
            elif args[0].isnumeric() or args[0][1:].isnumeric(): #Page number given
                if int(args[0]) >= 1 and int(args[0]) <= self.MAX_PAGES + 1: #Argument is a single integer between 1 and the amount of pages there are
                    return self.full_help(int(args[0]) - 1)
                else: #Invalid page
                    return discord.Embed(description=f'`{args[0]}` is not a valid page between 1 and {self.MAX_PAGES + 1}.')
            else: #Argument is the name of a command
                return self.command_help(args)
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\Smay\\Dropbox\\AmesBot", "bot")
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return embed

    def full_help(self, page: int = 0):
        self.page = page

        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name} Commands ☾∘∙⊱⋅•⋅', description=f'An exhaustive list of {bot.user.name}\'s commands.\ntype `eli help <command>` or `/help <command` for more information on a specific command.', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        cog_items = set() #Contains each command within a cog, so that non-cog commands may be gathered later

        #For each grouping of commands
        index = 0
        for i in bot.cogs:
            commands = bot.cogs.get(i).get_commands() #Gets the commands for that group
            if not (len(commands) == 0): #Some groups have no commands (namely, the BumpReminder cog); therefore, no group should be displayed
                if math.floor(index / self.ITEMS_PER_PAGE) == self.page: #If current cog should be displayed on this page
                    items = set() #A set of the command names, so that duplicates are removed (each name is added twice because both the normal commands and slash commands are accounted for)
                    for j in commands:
                        items.add(j.qualified_name)
                        cog_items.add(j.qualified_name)
                    display = ', '.join(sorted(items)) #Takes the set and puts them into a string that can be displayed
                    embed.add_field(name=i, value=display)
                else:
                    for j in commands:
                        cog_items.add(j.qualified_name)
                index += 1

        #For commands not grouped under a cog
        if math.floor(self.NUM_COGS / self.ITEMS_PER_PAGE) == self.page: #Misc should be displayed on this page
            items = set()
            for i in bot.application_commands:
                if not i.qualified_name in cog_items:
                    items.add(i.qualified_name)

            display = ', '.join(sorted(items)) #Takes the set and puts them into a string that can be displayed
            embed.add_field(name="Misc", value=display)
        
        embed.set_footer(text=f'Page {self.page + 1} of {self.MAX_PAGES + 1}')
        return embed

    def command_help(self, args):
        command = ' '.join(args)

        #Searches for the command, making sure it exists
        contains_item = False
        for i in bot.application_commands:
            if (str(i) == command) and type(i) == SlashCommand:
                contains_item = True
                commandInfo = i
                
        #Command was not found
        if not contains_item:
            embed = discord.Embed(description=f'`{command}` is not a known command.')
            return embed

        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {command.replace(command[0], command[0].upper())} ☾∘∙⊱⋅•⋅', description=f'{commandInfo.description}\n`<>` = required\t`[]` = optional', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        #Adds brackets to indicate whether each parameter is optional or not and combines them into a string
        options = ''
        for i in commandInfo.options:
            if i.required:
                separator = ['<', '>']
            else:
                separator = ['[', ']']
            options = (f'{options} {separator[0]}{i.name}={i.description.lower()}{separator[1]}')

        info = f'`/{command}{options}`'

        embed.add_field(name='Usage', value=info)
        return embed
