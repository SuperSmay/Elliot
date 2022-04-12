import traceback

import discord
from discord.ext import commands

from globalVariables import bot
from discord import Option, SlashCommand

class Help(commands.Cog):
    def __init__(self):
        self.page = 1
        self.maxPages = 1

    @commands.command(name='help', description='A full list of commands for Elliot')
    async def help_prefix(self, ctx, *args):
        await ctx.reply(embed=self.run_and_get_response(args), mention_author=False)

    @commands.slash_command(name='help', description='A full list of commands for Elliot')
    async def help_slash(self, ctx, command:Option(str, description='Which command to provide details for', required=False)):
        args = []
        if command != None: args += command.split(' ')
        await ctx.respond(embed=self.run_and_get_response(args))

    def run_and_get_response(self, args):  #Replys with the embed or an error
        try:
            if (len(args) == 0):
                return self.full_help()
            else:
                return self.command_help(args)
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\Smay\\Dropbox\\AmesBot", "bot")
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return embed

    def full_help(self):
        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name} Commands ☾∘∙⊱⋅•⋅', description=f'An exhaustive list of {bot.user.name}\'s commands.\ntype `eli help <command>` or `/help <command` for more information on a specific command.', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        #For each grouping of commands
        for i in bot.cogs:
            items = set()
            commands = bot.cogs.get(i).get_commands() #Gets the commands for that group
            if not (len(commands) == 0): #Some groups have no commands (namely, the BumpReminder cog); therefore, no group should be displayed
                #A set of the command names, so that duplicates are removed (each name is added twice because both the normal commands and slash commands are accounted for)
                for j in commands:
                    items.add(j.qualified_name)

                display = ', '.join(sorted(items)) #Takes the set and puts them into a string that can be displayed

                embed.add_field(name=i, value=display)

        embed.set_footer(text=f'Page {self.page} of {self.maxPages}')
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

        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {command} ☾∘∙⊱⋅•⋅', description=f'{commandInfo.description}\n`<>` = required\t`[]` = optional', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        options = ''
        for i in commandInfo.options:
            if i.required:
                separator = ['<', '>']
            else:
                separator = ['[', ']']
            options = (f'{options} {separator[0]}{i.name}{separator[1]}')

        info = f'`<eli {command}|/{command}>{options}`' #TODO add info

        embed.add_field(name='Usage', value=info)

        return embed
