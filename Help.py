import traceback
import math

import discord
from discord.ext import commands

from globalVariables import bot, prefix
from discord import Option, SlashCommand, SlashCommandGroup

class Help(commands.Cog, name='Help'):
    def __init__(self):
        pass

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
                if int(args[0]) >= 1 and int(args[0]) <= self.max_pages + 1: #Argument is a single integer between 1 and the amount of pages there are
                    return self.full_help(int(args[0]) - 1)
                else: #Invalid page
                    return discord.Embed(description=f'`{args[0]}` is not a valid page between 1 and {self.max_pages + 1}.')
            else: #Argument is the name of a command
                return self.command_help(args)
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\Smay\\Dropbox\\AmesBot", "bot")
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return embed

    def calculate_pages(self):
        '''Resets the cog count and max pages for help page calculation'''
        self.ITEMS_PER_PAGE = 4
        self.num_cogs = 0
        for i in bot.cogs:
            if len(bot.cogs.get(i).get_commands()) / 2 >= 4:
                self.num_cogs += 1
        self.max_pages = math.floor(self.num_cogs / self.ITEMS_PER_PAGE)

    def full_help(self, page: int = 0):
        '''
        Displays a full help page about a every command the bot has

        Parameters
        ---------
        `page`: int = 0
            The page number the user requested. Is formatted as an index starting at 0.
        '''
        self.calculate_pages()
        self.page = page

        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name} Commands ☾∘∙⊱⋅•⋅', description=f'An exhaustive list of {bot.user.name}\'s commands.\ntype `{prefix}help <command>` or `/help <command>` for more information on a specific command.', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        cog_items = set() #Contains each command within a cog, so that non-cog commands may be gathered later

        #For each grouping of commands
        index = 0
        for i in bot.cogs:
            commands = bot.cogs.get(i).get_commands() #Gets the commands for that group
            if (len(commands) / 2 >= 4): #Some groups have no commands (namely, the BumpReminder cog); therefore, no group should be displayed
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
        if math.floor(self.num_cogs / self.ITEMS_PER_PAGE) == self.page: #Misc should be displayed on this page
            items = set()
            for i in bot.application_commands:
                if not i.qualified_name in cog_items:
                    items.add(i.qualified_name)

            display = ', '.join(sorted(items)) #Takes the set and puts them into a string that can be displayed
            embed.add_field(name="Misc", value=display)
        
        embed.set_footer(text=f'{len(bot.application_commands)} commands   |   Page {self.page + 1} of {self.max_pages + 1}')
        return embed

    def command_help(self, args):
        '''
        Displays a help page about a specific requested command

        Parameters
        ---------
        `args`: tuple
            The information the user provided after running the help command, split by spaces and stored in a tuple
        '''
        command = ' '.join(args)

        #Searches for the command, making sure it exists
        contains_item = False
        for i in bot.application_commands:
            if len(args) > 1: #User is looking for subcommands
                if (type(i) == SlashCommandGroup) and str(i) == args[0]: #i has subcommands and is the command group the user wants
                    commandInfo = self.search_for_subcommand(i, ' '.join(args))
                    if not str(commandInfo) == '':
                        contains_item = True
                        break
            else: #One word, either subcommand group or single command
                if (str(i) == command) and (type(i) == SlashCommand or type(i) == SlashCommandGroup):
                    contains_item = True
                    commandInfo = i
                    break
                
        #Command was not found
        if not contains_item:
            embed = discord.Embed(description=f'`{command}` is not a known command.')
            return embed

        #Creates embed info
        embed = discord.Embed(title=f'⋅•⋅⊰∙∘☽ {command.replace(command[0], command[0].upper(), 1)} ☾∘∙⊱⋅•⋅', description=f'{commandInfo.description}\n`<>` = required\t`[]` = optional', color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)

        if type(commandInfo) == SlashCommandGroup: #The command has subcommands
            info = '\n'.join(sorted(self.gather_subcommands(commandInfo))) 
        else: #No subcommands
            options = self.create_options(commandInfo)
            info = f'`/{command}{options}`'

        embed.add_field(name='Usage', value=info)
        return embed

    def gather_subcommands(self, group: SlashCommandGroup) -> list[str]:
        '''
        Recursively searches the given command and its subcommands, and adds them all to the list info

        Parameters
        ----------
        `group`: SlashCommandGroup
            The group to search for more commands in

        Returns
        -------
        A list containing each subcommand that was found as a string joined with its parameters
        '''
        info = []
        for subcommand in group.subcommands:
            if (type(subcommand) == SlashCommand):
                options = self.create_options(subcommand);
                info.append(f'`/{subcommand}{options}`')
            else:
                for i in self.gather_subcommands(subcommand):
                    info.append(i)
        return info

    def search_for_subcommand(self, group: SlashCommandGroup, key: str):
        '''
        Searches the given SlashCommandGroup for subcommands within key.

        Parameters
        ----------
        `group`: SlashCommandGroup
            The group to look for commands in
        `key`: str
            The reqested command as a string of the user's input

        Returns
        -------
        The SlashCommand found within group's subcommands, or an empty string otherwise
        '''
        item = ''
        for subcommand in group.subcommands:
            if (type(subcommand) == SlashCommand):
                if str(subcommand) == key:
                    item = subcommand
                    break
            else:
                item = self.search_for_subcommand(subcommand, key)
                if str(subcommand) in key and str(item) == '': #No subcommand was found, user just wants a general subgroup
                    return subcommand
        return item

    def create_options(self, command: SlashCommand = None) -> str:
        '''
        Adds brackets to indicate whether each parameter is optional or not and combines them into a string
        
        Parameters
        ----------
        `command`: Optional[SlashCommand]
            The command to gather options from

        Returns
        -------
        A String of the command, its parameters, and how each is expected to be used
        '''
        options = ''
        for i in command.options:
            if i.required:
                separator = ['<', '>']
            else:
                separator = ['[', ']']
            options = f'{options} {separator[0]}{i.name}={i.description.lower()}{separator[1]}'
        return options
