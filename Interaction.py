import random
from Statistics import log_event

import botGifs
from fnmatch import fnmatch
import traceback
import pathlib
import json
import logging
import sqlite3

import discord
from discord.ext import commands, tasks
from discord import Option

from GlobalVariables import bot, on_log
import DBManager

database_name = 'Elliot.sqlite'
database_path = pathlib.Path(f'Storage/{database_name}')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addFilter(on_log)

class Interaction(commands.Cog, name='Interactions'):

    def __init__(self):
        DBManager.ensure_table_exists('interactions')

    #region Commands

    @commands.command(name="hug", description="Hugs a user!")
    async def hug_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=HugInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="hug", description="Hugs a user!")
    async def hug_slash(self, ctx, user:Option(discord.Member, description='User to hug', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HugInteraction(ctx, args).run_and_get_response())

    @commands.command(name="kiss", description="Kiss a user!")
    async def kiss_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=KissInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="kiss", description="Kiss a user!")
    async def kiss_slash(self, ctx, user:Option(discord.Member, description='User to kiss', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=KissInteraction(ctx, args).run_and_get_response())

    @commands.command(name="punch", description="Punch a user!")
    async def punch_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=PunchInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="punch", description="Punch a user!")
    async def punch_slash(self, ctx, user:Option(discord.Member, description='User to punch', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PunchInteraction(ctx, args).run_and_get_response())

    @commands.command(name="kill", description="Kills a user!")
    async def kill_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=KillInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="kill", description="Kills a user!")
    async def kill_slash(self, ctx, user:Option(discord.Member, description='User to kill', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=KillInteraction(ctx, args).run_and_get_response())

    @commands.command(name="handhold", description="Handholds a user!")
    async def handhold_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=HandholdInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="handhold", description="Handholds a user!")
    async def handhold_slash(self, ctx, user:Option(discord.Member, description='User to handhold', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HandholdInteraction(ctx, args).run_and_get_response())

    @commands.command(name="love", description="Loves a user!")
    async def love_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=LoveInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="love", description="Loves a user!")
    async def love_slash(self, ctx, user:Option(discord.Member, description='User to love', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=LoveInteraction(ctx, args).run_and_get_response())

    @commands.command(name="cuddle", description="Cuddles a user!")
    async def cuddle_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=CuddleInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="cuddle", description="Cuddles a user!")
    async def cuddle_slash(self, ctx, user:Option(discord.Member, description='User to cuddle', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=CuddleInteraction(ctx, args).run_and_get_response())

    @commands.command(name="pat", description="Pats a user!")
    async def pat_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=PatInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="pat", description="Pats a user!")
    async def pat_slash(self, ctx, user:Option(discord.Member, description='User to pat', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PatInteraction(ctx, args).run_and_get_response())

    @commands.command(name="peck", description="Pecks a user!")
    async def peck_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=PeckInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="peck", description="Pecks a user!")
    async def peck_slash(self, ctx, user:Option(discord.Member, description='User to peck', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PeckInteraction(ctx, args).run_and_get_response())

    @commands.command(name="chase", description="Chases a user!")
    async def chase_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=ChaseInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="chase", description="Chases a user!")
    async def chase_slash(self, ctx, user:Option(discord.Member, description='User to chase', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=ChaseInteraction(ctx, args).run_and_get_response())

    @commands.command(name="boop", description="Boops a user!")
    async def boop_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=BoopInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="boop", description="Boops a user!")
    async def boop_slash(self, ctx, user:Option(discord.Member, description='User to boop', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BoopInteraction(ctx, args).run_and_get_response())

    @commands.command(name="bonk", description="Bonks a user!")
    async def bonk_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=BonkInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="bonk", description="Bonks a user!")
    async def bonk_slash(self, ctx, user:Option(discord.Member, description='User to bonk', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BonkInteraction(ctx, args).run_and_get_response())

    @commands.command(name="run", description="Run!")
    async def run_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=RunInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="run", description="Run!")
    async def run_slash(self, ctx, user:Option(discord.Member, description='User to run at', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=RunInteraction(ctx, args).run_and_get_response())

    @commands.command(name="die", description="*Dies*")
    async def die_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=DieInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="die", description="*Dies*")
    async def die_slash(self, ctx, user:Option(discord.Member, description='User to wish death upon', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=DieInteraction(ctx, args).run_and_get_response())

    @commands.command(name="dance", description="Dance!")
    async def dance_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=DanceInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="dance", description="Dance!")
    async def dance_slash(self, ctx, user:Option(discord.Member, description='User to dance with', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=DanceInteraction(ctx, args).run_and_get_response())

    @commands.command(name="lurk", description="Lurk")
    async def lurk_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=LurkInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="lurk", description="Lurk")
    async def lurk_slash(self, ctx, user:Option(discord.Member, description='User to watch', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=LurkInteraction(ctx, args).run_and_get_response())

    @commands.command(name="pout", description="Pout")
    async def pout_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=PoutInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="pout", description="Pout")
    async def pout_slash(self, ctx, user:Option(discord.Member, description='User to pout at', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PoutInteraction(ctx, args).run_and_get_response())

    @commands.command(name="eat", description="Eat some food")
    async def eat_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=EatInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="eat", description="Eat some food")
    async def eat_slash(self, ctx, user:Option(discord.Member, description='User to eat', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=EatInteraction(ctx, args).run_and_get_response())

    @commands.command(name="cry", description="When you want to cry :(")
    async def cry_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=CryInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="cry", description="When you want to cry :(")
    async def cry_slash(self, ctx, user:Option(discord.Member, description='User to cry for', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=CryInteraction(ctx, args).run_and_get_response())

    @commands.command(name="blush", description="Blush")
    async def blush_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=BlushInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="blush", description="Blush")
    async def blush_slash(self, ctx, user:Option(discord.Member, description='User that made you blush', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BlushInteraction(ctx, args).run_and_get_response())

    @commands.command(name="hide", description="Hide")
    async def hide_prefix(self, ctx, *args):
        log_event('prefix_command', ctx=ctx)
        await ctx.reply(embed=HideInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="hide", description="Hide")
    async def hide_slash(self, ctx, user:Option(discord.Member, description='User to hide from', required=False), message:Option(str, description='Message to include', required=False)):
        log_event('slash_command', ctx=ctx)
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HideInteraction(ctx, args).run_and_get_response())

    #endregion



def update_columns(name_list: list[str]):
    '''
        Adds any missing columns to the interactoins table based on the input list

        Parameters:
            - `name_list`: list[str]; A list of column names
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            columns = cur.execute(f'PRAGMA table_info(interactions)').fetchall()
            columns_list = [column[1] for column in columns]
            for col_name in name_list:
                if f'{col_name}_give' in columns_list:
                    pass
                else:
                    execution_string_give = f"ALTER TABLE interactions ADD {col_name}_give INTEGER DEFAULT 0"
                    cur.execute(execution_string_give)
                    logger.info(f'Created new table column {col_name=} of type=int')
                
                if f'{col_name}_receive' in columns_list:
                    pass
                else:
                    execution_string_receive = f"ALTER TABLE interactions ADD {col_name}_receive INTEGER DEFAULT 0"
                    cur.execute(execution_string_receive)
                    logger.info(f'Created new table column {col_name=} of type=int')

    except Exception as e:
        logger.error(f'Failed to update interactions database columns', exc_info=True)
        raise e
    
class BaseInteraction():

    def __init__(self, ctx:commands.Context, args, interaction_name):
        self.ctx = ctx
        self.interaction_name = interaction_name
        self.arguments = list(args)
        self.name_list = []
        self.included_message = ""
        self.footer = ""

    def run_and_get_response(self):  #Runs command and returns the embed or an error
        try:
            user_id_list, included_message = self.split_into_ids_and_message()
            self.update_counts(user_id_list)
            log_event('user_interaction', ctx=self.ctx)
            return self.embed(user_id_list, included_message)
        except Exception as e:
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328>") 
            logger.error('Interaction failed', exc_info=True)
            return embed
   
    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
            self.add_give_count(self.ctx.author.id)
    
    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got tested {self.get_receive_count(self.ctx.author.id)} times, and tested others {self.get_give_count()} times." 
        count_message = count_message.replace(" 1 times", " once").replace("69", "69 hehe") if random.randint(0, 20) != 0 else count_message.replace("1 times", "**o**__n__c*é*")
        return count_message

    def embed(self, user_id_list, included_message):  #Creates the embed to be sent
        name_list = [(self.ctx.guild.get_member(id)).display_name for id in user_id_list]
        embedToReturn = discord.Embed(title= self.get_embed_title(name_list), description= included_message, color= self.get_color())
        embedToReturn.set_image(url= self.get_image_url(name_list))
        embedToReturn.set_footer(text= f"{self.get_count_message()} {self.footer}" )
        return embedToReturn

    def get_embed_title(self, name_list):  #Gets the title of the embed from no_ping_title and ping_title
        if len(name_list) == 0:
            return self.no_ping_title()
        return self.ping_title(name_list)

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name}"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} --> {self.get_joined_names(name_list)}"

    def get_joined_names(self, name_list):  #Joins all the names used into a nice string
        if len(name_list) == 1:
            return name_list[0]
        elif len(name_list) == 2:
            return f"{name_list[0]} and {name_list[1]}"
        elif len(name_list) > 2: 
            return ", ".join(name_list[:-1]) + ", and " + name_list[-1]

    def check_if_ping(self, ping):  #Check if the first ping is valid for the guild
        if fnmatch(ping, "<@*>") and self.get_id_from_ping(ping) in [user.id for user in self.ctx.channel.members]: return True
        elif ping in [str(user.id) for user in self.ctx.channel.members]: return True
        elif len([user.id for user in self.ctx.channel.members]) == 1:  #If Intents.members is off for some reason or something else denies access to the channel member list then the bot's user is the only one found
            logger.warn(f'Could not get members for channel: {self.ctx.channel.id} in guild {self.ctx.guild.name}! Assuming user is valid and continuing')
            return True
        return False

    def split_into_ids_and_message(self):  #Splits the arugments into the name_list and included message and return them

        user_id_list = []
        message_list = []
        temp_args = self.arguments.copy()
        while 0 < len(temp_args):
            if fnmatch(temp_args[0], f"<@*{self.ctx.author.id}>") or temp_args[0] == str(self.ctx.author.id):  #If the user that sent the message pinged themselves, skip adding it to the ping list
                del temp_args[0]
            elif self.check_if_ping(temp_args[0]) and not self.get_id_from_ping(temp_args[0]) in user_id_list:  #If the argument is a ping or valid id of a user in the channel, and isn't already in the ID list, add it to the ID list
                user_id_list.append(self.get_id_from_ping(temp_args[0]))
                del temp_args[0]
            else:
                message_list.append(temp_args[0])
                del temp_args[0]

        included_message = " ".join(message_list)  #Message is everything left over joined back into a single string

        return user_id_list, included_message
    
    def get_color(self):
        return random.choice(botGifs.colors)

    def get_id_from_ping(self, ping):
        id = ping.replace("<", "").replace(">", "").replace("@", "").replace("!", "").replace("&", "")
        return int(id)

    def get_image_url(self, name_list):  #Gets the image for the embed from no_ping_image and ping_image
        if len(name_list) == 0:
            return self.no_ping_image()
        return self.ping_image()

    def no_ping_image(self):
        return "https://images-ext-2.discordapp.net/external/T2EiRPQoyjtgufZFuk9sUh5CpvjdZHD9fMx2r2iFwv4/https/c.tenor.com/RRG7pXMcSloAAAAM/sad-anime.gif"

    def ping_image(self):
        return "https://images-ext-1.discordapp.net/external/jdZsQ2YnpjXowNPa42l7p52SKfc-iddn1YlpN_BXt3M/https/c.tenor.com/UhcyGsGpLNIAAAAM/hug-anime.gif"
    
    def get_give_count(self, user_id):
        DBManager.update_columns('interactions', DBManager.global_database_path, {f'{self.interaction_name}_give': int}, defaults={f'{self.interaction_name}_give': 0})  #FIXME kinda inefficient but oh well
        if DBManager.is_row_known('interactions', DBManager.global_database_path, 'user_id', user_id):
            with sqlite3.connect(database_path) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                row = cur.execute(f"SELECT * FROM interactions WHERE user_id = {user_id}").fetchone()
                logger.info(f'Fetched give count for {self.interaction_name=} {user_id=}')
            count = row[f'{self.interaction_name}_give']
            return count
        return 0
    
    def add_give_count(self, user_id):
        DBManager.update_columns('interactions', DBManager.global_database_path, {f'{self.interaction_name}_give': int}, defaults={f'{self.interaction_name}_give': 0})
        if DBManager.is_row_known('interactions', DBManager.global_database_path, 'user_id', user_id):
            count = self.get_give_count(user_id)
            count += 1
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"UPDATE interactions SET {self.interaction_name}_give = (?) WHERE user_id = {user_id}", [count])
                logger.info(f'Changed interactions {self.interaction_name}_give to {count} for {user_id=}')
            return count
        else:
            DBManager.initialize_row('interactions', DBManager.global_database_path, 'user_id', user_id)
            self.add_give_count(user_id)

    def get_receive_count(self, user_id):
        DBManager.update_columns('interactions', DBManager.global_database_path, {f'{self.interaction_name}_receive': int}, defaults={f'{self.interaction_name}_receive': 0})
        if DBManager.is_row_known('interactions', DBManager.global_database_path, 'user_id', user_id):
            with sqlite3.connect(database_path) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                row = cur.execute(f"SELECT * FROM interactions WHERE user_id = {user_id}").fetchone()
                logger.info(f'Fetched give count for {self.interaction_name=} {user_id=}')
            count = row[f'{self.interaction_name}_receive']
            return count
        return 0
    
    def add_receive_count(self, user_id):
        DBManager.update_columns('interactions', DBManager.global_database_path, {f'{self.interaction_name}_receive': int}, defaults={f'{self.interaction_name}_receive': 0})
        if DBManager.is_row_known('interactions', DBManager.global_database_path, 'user_id', user_id):
            count = self.get_receive_count(user_id)
            count += 1
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"UPDATE interactions SET {self.interaction_name}_receive = (?) WHERE user_id = {user_id}", [count])
                logger.info(f'Changed interactions {self.interaction_name}_receive to {count} for {user_id=}')
            return count
        else:
            DBManager.initialize_row('interactions', DBManager.global_database_path, 'user_id', user_id)
            self.add_give_count(user_id)

#region Interaction classes
class HugInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'hug')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a hug..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is hugging {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.hugGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got hugged {self.get_receive_count(self.ctx.author.id)} times, and hugged others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class KissInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'kiss')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a kiss..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is kissing {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.kissGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got kissed {self.get_receive_count(self.ctx.author.id)} times, and kissed others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class PunchInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'punch')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a to punch something"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is punching {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.punchGif)

    def ping_image(self):
        return random.choice(botGifs.punchGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got punched {self.get_receive_count(self.ctx.author.id)} times, and punched others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class KillInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'kill')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to kill someone"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} killed {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.killGif)

    def ping_image(self):
        return random.choice(botGifs.killGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got killed {self.get_receive_count(self.ctx.author.id)} times, and killed others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class HandholdInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'handhold')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to hold someone's hand..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is holding {self.get_joined_names(name_list)}'s hand{'' if len(name_list) < 2 else 's'}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.handholdGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got thier hand held {self.get_receive_count(self.ctx.author.id)} times, and held others hands {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class LoveInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'love')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants love..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} loves {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.loveGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got loved {self.get_receive_count(self.ctx.author.id)} times, and loved others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class CuddleInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'cuddle')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to cuddle..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is cuddling {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.cuddleGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got cuddled with {self.get_receive_count(self.ctx.author.id)} times, and cuddled others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class PatInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'pat')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a pat..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is patting {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.patGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got pat {self.get_receive_count(self.ctx.author.id)} times, and patted others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class PeckInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'peck')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a peck..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} pecks {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.selfHugGif)

    def ping_image(self):
        return random.choice(botGifs.peckGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got pecked {self.get_receive_count(self.ctx.author.id)} times, and pecked others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class ChaseInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'chase')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is waiting for someone to chase..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is chasing {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.lurkGif)

    def ping_image(self):
        return random.choice(botGifs.chaseGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} was chased {self.get_receive_count(self.ctx.author.id)} times, and chased others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class BoopInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'boop')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is looking for someone to boop..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} booped {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.lurkGif)

    def ping_image(self):
        return random.choice(botGifs.boopGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got booped {self.get_receive_count(self.ctx.author.id)} times, and booped others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class BonkInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'bonk')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is looking for someone to bonk..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} bonked {self.get_joined_names(name_list)}!"

    def no_ping_image(self):
        return random.choice(botGifs.lurkGif)

    def ping_image(self):
        return random.choice(botGifs.bonkGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got bonked {self.get_receive_count(self.ctx.author.id)} times, and bonked others {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

class RunInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'run')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is running away!"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is running at {self.get_joined_names(name_list)}!"

    def no_ping_image(self):
        return random.choice(botGifs.runGif)

    def ping_image(self):
        return random.choice(botGifs.chaseGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} got ran at {self.get_receive_count(self.ctx.author.id)} times, and ran {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class DieInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'die')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} died :c"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} wants {self.get_joined_names(name_list)} to die :c"

    def no_ping_image(self):
        return random.choice(botGifs.dieGif)

    def ping_image(self):
        return random.choice(botGifs.dieGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} died {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class DanceInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'dance')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} danced around!"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is dancing with {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.danceGif)

    def ping_image(self):
        return random.choice(botGifs.danceGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} was danced with {self.get_receive_count(self.ctx.author.id)} times, and danced {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class LurkInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'lurk')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is lurking..."

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is watching {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.lurkGif)

    def ping_image(self):
        return random.choice(botGifs.lurkGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} was watched {self.get_receive_count(self.ctx.author.id)} times, and lurked {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class PoutInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'pout')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is pouting"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is pouting at {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.poutGif)

    def ping_image(self):
        return random.choice(botGifs.poutGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} was pouted at {self.get_receive_count(self.ctx.author.id)} times, and pouted {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class EatInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'eat')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is eating"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is eating {self.get_joined_names(name_list)}!"

    def no_ping_image(self):
        return random.choice(botGifs.eatGif)

    def ping_image(self):
        return random.choice(botGifs.eatGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} was eaten {self.get_receive_count(self.ctx.author.id)} times, and ate {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class CryInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'cry')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is crying :c"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is crying for {self.get_joined_names(name_list)} :c"

    def no_ping_image(self):
        return random.choice(botGifs.cryGif)

    def ping_image(self):
        return random.choice(botGifs.cryGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} cried {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class BlushInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'blush')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is blushing"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is blushing becuase of {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.blushGif)

    def ping_image(self):
        return random.choice(botGifs.blushGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} blushed {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

class HideInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'hide')

    def no_ping_title(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is hiding"

    def ping_title(self, name_list):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is hiding from {self.get_joined_names(name_list)}"

    def no_ping_image(self):
        return random.choice(botGifs.hideGif)

    def ping_image(self):
        return random.choice(botGifs.hideGif)

    def get_count_message(self):
        count_message = f"{self.ctx.author.display_name} hid {self.get_give_count(self.ctx.author.id)} times." 
        count_message = count_message.replace("1 times", "once")
        return count_message

    def update_counts(self, user_id_list):
        if len(user_id_list) > 0:
            for id in user_id_list:
                self.add_receive_count(id)
        self.add_give_count(self.ctx.author.id)

#endregion
