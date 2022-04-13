import random

import botGifs
from fnmatch import fnmatch
import traceback
import pathlib
import json

import discord
from discord.ext import commands, tasks
from discord import Option

from globalVariables import bot


class Interaction(commands.Cog, name='Interactions'):

    def __init__(self):
        self.interactionFile = pathlib.Path('interactionCountDict')
        self.interactionDict = json.load(open(self.interactionFile, 'r'))

        print("Starting File Save Loop...")
        self.save_interaction_file.start()

    def cog_unload(self):
        self.save_interaction_file.cancel()

    def saveFile(self, file):
        open_file = open(file, 'w')
        json.dump(self.interactionDict, open_file)
        open_file.close()

    @tasks.loop(minutes=30)
    async def save_interaction_file(self):
        self.saveFile(self.interactionFile)
        print("Interaction file saved.")

    @save_interaction_file.after_loop
    async def interaction_loop_cancelled(self):
        if self.save_interaction_file.is_being_cancelled():
            self.saveFile(self.interactionFile)

    #region Commands

    @commands.command(name="hug", description="Hugs a user!")
    async def hug_prefix(self, ctx, *args):
        await ctx.reply(embed=HugInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="hug", description="Hugs a user!")
    async def hug_slash(self, ctx, user:Option(discord.Member, description='User to hug', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HugInteraction(ctx, args).run_and_get_response())

    @commands.command(name="kiss", description="Kiss a user!")
    async def kiss_prefix(self, ctx, *args):
        await ctx.reply(embed=KissInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="kiss", description="Kiss a user!")
    async def kiss_slash(self, ctx, user:Option(discord.Member, description='User to kiss', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=KissInteraction(ctx, args).run_and_get_response())

    @commands.command(name="punch", description="Punch a user!")
    async def punch_prefix(self, ctx, *args):
        await ctx.reply(embed=PunchInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="punch", description="Punch a user!")
    async def punch_slash(self, ctx, user:Option(discord.Member, description='User to punch', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PunchInteraction(ctx, args).run_and_get_response())

    @commands.command(name="kill", description="Kills a user!")
    async def kill_prefix(self, ctx, *args):
        await ctx.reply(embed=KillInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="kill", description="Kills a user!")
    async def kill_slash(self, ctx, user:Option(discord.Member, description='User to kill', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=KillInteraction(ctx, args).run_and_get_response())

    @commands.command(name="handhold", description="Handholds a user!")
    async def handhold_prefix(self, ctx, *args):
        await ctx.reply(embed=HandholdInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="handhold", description="Handholds a user!")
    async def handhold_slash(self, ctx, user:Option(discord.Member, description='User to handhold', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HandholdInteraction(ctx, args).run_and_get_response())

    @commands.command(name="love", description="Loves a user!")
    async def love_prefix(self, ctx, *args):
        await ctx.reply(embed=LoveInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="love", description="Loves a user!")
    async def love_slash(self, ctx, user:Option(discord.Member, description='User to love', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=LoveInteraction(ctx, args).run_and_get_response())

    @commands.command(name="cuddle", description="Cuddles a user!")
    async def cuddle_prefix(self, ctx, *args):
        await ctx.reply(embed=CuddleInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="cuddle", description="Cuddles a user!")
    async def cuddle_slash(self, ctx, user:Option(discord.Member, description='User to cuddle', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=CuddleInteraction(ctx, args).run_and_get_response())

    @commands.command(name="pat", description="Pats a user!")
    async def pat_prefix(self, ctx, *args):
        await ctx.reply(embed=PatInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="pat", description="Pats a user!")
    async def pat_slash(self, ctx, user:Option(discord.Member, description='User to pat', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PatInteraction(ctx, args).run_and_get_response())

    @commands.command(name="peck", description="Pecks a user!")
    async def peck_prefix(self, ctx, *args):
        await ctx.reply(embed=PeckInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="peck", description="Pecks a user!")
    async def peck_slash(self, ctx, user:Option(discord.Member, description='User to peck', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PeckInteraction(ctx, args).run_and_get_response())

    @commands.command(name="chase", description="Chases a user!")
    async def chase_prefix(self, ctx, *args):
        await ctx.reply(embed=ChaseInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="chase", description="Chases a user!")
    async def chase_slash(self, ctx, user:Option(discord.Member, description='User to chase', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=ChaseInteraction(ctx, args).run_and_get_response())

    @commands.command(name="boop", description="Boops a user!")
    async def boop_prefix(self, ctx, *args):
        await ctx.reply(embed=BoopInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="boop", description="Boops a user!")
    async def boop_slash(self, ctx, user:Option(discord.Member, description='User to boop', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BoopInteraction(ctx, args).run_and_get_response())

    @commands.command(name="bonk", description="Bonks a user!")
    async def bonk_prefix(self, ctx, *args):
        await ctx.reply(embed=BonkInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="bonk", description="Bonks a user!")
    async def bonk_slash(self, ctx, user:Option(discord.Member, description='User to bonk', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BonkInteraction(ctx, args).run_and_get_response())

    @commands.command(name="run", description="Run!")
    async def run_prefix(self, ctx, *args):
        await ctx.reply(embed=RunInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="run", description="Run!")
    async def run_slash(self, ctx, user:Option(discord.Member, description='User to run at', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=RunInteraction(ctx, args).run_and_get_response())

    @commands.command(name="die", description="*Dies*")
    async def die_prefix(self, ctx, *args):
        await ctx.reply(embed=DieInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="die", description="*Dies*")
    async def die_slash(self, ctx, user:Option(discord.Member, description='User to wish death upon', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=DieInteraction(ctx, args).run_and_get_response())

    @commands.command(name="dance", description="Dance!")
    async def dance_prefix(self, ctx, *args):
        await ctx.reply(embed=DanceInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="dance", description="Dance!")
    async def dance_slash(self, ctx, user:Option(discord.Member, description='User to dance with', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=DanceInteraction(ctx, args).run_and_get_response())

    @commands.command(name="lurk", description="Lurk")
    async def lurk_prefix(self, ctx, *args):
        await ctx.reply(embed=LurkInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="lurk", description="Lurk")
    async def lurk_slash(self, ctx, user:Option(discord.Member, description='User to watch', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=LurkInteraction(ctx, args).run_and_get_response())

    @commands.command(name="pout", description="Pout")
    async def pout_prefix(self, ctx, *args):
        await ctx.reply(embed=PoutInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="pout", description="Pout")
    async def pout_slash(self, ctx, user:Option(discord.Member, description='User to pout at', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=PoutInteraction(ctx, args).run_and_get_response())

    @commands.command(name="eat", description="Eat some food")
    async def eat_prefix(self, ctx, *args):
        await ctx.reply(embed=EatInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="eat", description="Eat some food")
    async def eat_slash(self, ctx, user:Option(discord.Member, description='User to eat', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=EatInteraction(ctx, args).run_and_get_response())

    @commands.command(name="cry", description="When you want to cry :(")
    async def cry_prefix(self, ctx, *args):
        await ctx.reply(embed=CryInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="cry", description="When you want to cry :(")
    async def cry_slash(self, ctx, user:Option(discord.Member, description='User to cry for', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=CryInteraction(ctx, args).run_and_get_response())

    @commands.command(name="blush", description="Blush")
    async def blush_prefix(self, ctx, *args):
        await ctx.reply(embed=BlushInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="blush", description="Blush")
    async def blush_slash(self, ctx, user:Option(discord.Member, description='User that made you blush', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=BlushInteraction(ctx, args).run_and_get_response())

    @commands.command(name="hide", description="Hide")
    async def hide_prefix(self, ctx, *args):
        await ctx.reply(embed=HideInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @commands.slash_command(name="hide", description="Hide")
    async def hide_slash(self, ctx, user:Option(discord.Member, description='User to hide from', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HideInteraction(ctx, args).run_and_get_response())

    #endregion
    
class BaseInteraction():

    def __init__(self, ctx:commands.Context, args, interactionName):
        self.ctx = ctx
        self.interactionName = interactionName
        self.arguments = list(args)
        self.nameList = []
        self.includedMessage = ""
        self.footer = ""

        self.interactionDict = (bot.get_cog('Interactions')).interactionDict

    def run_and_get_response(self):  #Runs command and returns the embed or an error
        try:
            userIDList, includedMessage = self.splitIntoIDsAndMessage()
            self.updateCounts(userIDList)
            return self.embed(userIDList, includedMessage)
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\Smay\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nInteraction: {self.interactionName}\nArguments: {self.arguments}\nnameList: {self.nameList}\nincludedMessage: {self.includedMessage}"
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return embed
   
    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
            self.addGiveCount(self.ctx.author.id)
    
    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got tested {self.getReceiveCount(self.ctx.author.id)} times, and tested others {self.getGiveCount()} times." 
        countMessage = countMessage.replace(" 1 times", " once").replace("69", "69 hehe") if random.randint(0, 20) != 0 else countMessage.replace("1 times", "**o**__n__c*é*")
        return countMessage

    def embed(self, userIDList, includedMessage):  #Creates the embed to be sent
        nameList = [(self.ctx.guild.get_member(id)).display_name for id in userIDList]
        embedToReturn = discord.Embed(title= self.getEmbedTitle(nameList), description= includedMessage, color= self.getColor())
        embedToReturn.set_image(url= self.getImageURL(nameList))
        embedToReturn.set_footer(text= f"{self.getCountMessage()} {self.footer}" )
        return embedToReturn

    def getEmbedTitle(self, nameList):  #Gets the title of the embed from noPingTitle and pingTitle
        if len(nameList) == 0:
            return self.noPingTitle()
        return self.pingTitle(nameList)

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name}"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} --> {self.getJoinedNames(nameList)}"

    def getJoinedNames(self, nameList):  #Joins all the names used into a nice string
        if len(nameList) == 1:
            return nameList[0]
        elif len(nameList) == 2:
            return f"{nameList[0]} and {nameList[1]}"
        elif len(nameList) > 2: 
            return ", ".join(nameList[:-1]) + ", and " + nameList[-1]

    def checkIfPingOrID(self, ping):  #Check if the first ping is valid for the guild
        if fnmatch(ping, "<@*>") and self.getIDFromPing(ping) in [user.id for user in self.ctx.channel.members]: return True
        elif ping in [str(user.id) for user in self.ctx.channel.members]: return True
        elif len([user.id for user in self.ctx.channel.members]) == 1:  #If Intents.members is off for some reason or something else denies access to the channel member list then the bot's user is the only one found
            print(f'Could not get members for channel: {self.ctx.channel.id} in guild {self.ctx.guild.name}! Assuming user is valid and continuing')
            return True
        return False

    def splitIntoIDsAndMessage(self):  #Splits the arugments into the nameList and included message and return them

        userIDList = []
        messageList = []
        tempArgs = self.arguments.copy()
        while 0 < len(tempArgs):
            if fnmatch(tempArgs[0], f"<@*{self.ctx.author.id}>") or tempArgs[0] == str(self.ctx.author.id):  #If the user that sent the message pinged themselves, skip adding it to the ping list
                del tempArgs[0]
            elif self.checkIfPingOrID(tempArgs[0]) and not self.getIDFromPing(tempArgs[0]) in userIDList:  #If the argument is a ping or valid id of a user in the channel, and isn't already in the ID list, add it to the ID list
                userIDList.append(self.getIDFromPing(tempArgs[0]))
                del tempArgs[0]
            else:
                messageList.append(tempArgs[0])
                del tempArgs[0]

        includedMessage = " ".join(messageList)  #Message is everything left over joined back into a single string

        return userIDList, includedMessage
    
    def getColor(self):
        return random.choice(botGifs.colors)

    def getIDFromPing(self, ping):
        id = ping.replace("<", "").replace(">", "").replace("@", "").replace("!", "").replace("&", "")
        return int(id)

    def getImageURL(self, nameList):  #Gets the image for the embed from noPingImage and pingImage
        if len(nameList) == 0:
            return self.noPingImage()
        return self.pingImage()

    def noPingImage(self):
        return "https://images-ext-2.discordapp.net/external/T2EiRPQoyjtgufZFuk9sUh5CpvjdZHD9fMx2r2iFwv4/https/c.tenor.com/RRG7pXMcSloAAAAM/sad-anime.gif"

    def pingImage(self):
        return "https://images-ext-1.discordapp.net/external/jdZsQ2YnpjXowNPa42l7p52SKfc-iddn1YlpN_BXt3M/https/c.tenor.com/UhcyGsGpLNIAAAAM/hug-anime.gif"
    
    def getGiveCount(self, userID):
        if str(userID) in self.interactionDict.keys():
            countDict = self.interactionDict[str(userID)]
            if self.interactionName in countDict.keys():
                return countDict[self.interactionName]["give"]
        return 0
    
    def addGiveCount(self, userID):
        if str(userID) in self.interactionDict.keys():
            countDict = self.interactionDict[str(userID)]
            if self.interactionName in countDict.keys():
                countDict[self.interactionName]["give"] += 1
            else:
                countDict[self.interactionName] = {"give" : 0, "receive" : 0}
                countDict[self.interactionName]["give"] += 1
            return countDict[self.interactionName]["give"]
        else:
            countDict = {}
            self.interactionDict[str(userID)] = countDict
            countDict[self.interactionName] = {"give" : 0, "receive" : 0}
            countDict[self.interactionName]["give"] += 1
            return countDict[self.interactionName]["give"]

    def getReceiveCount(self, userID):
        if str(userID) in self.interactionDict.keys():
            countDict = self.interactionDict[str(userID)]
            if self.interactionName in countDict.keys():
                return countDict[self.interactionName]["receive"]
        return 0
    
    def addReceiveCount(self, userID):
        if str(userID) in self.interactionDict.keys():
            countDict = self.interactionDict[str(userID)]
            if self.interactionName in countDict.keys():
                countDict[self.interactionName]["receive"] += 1
            else:
                countDict[self.interactionName] = {"give" : 0, "receive" : 0}
                countDict[self.interactionName]["receive"] += 1
            return countDict[self.interactionName]["receive"]
        else:
            countDict = {}
            self.interactionDict[str(userID)] = countDict
            countDict[self.interactionName] = {"give" : 0, "receive" : 0}
            countDict[self.interactionName]["receive"] += 1
            return countDict[self.interactionName]["receive"]

#region Interaction classes
class HugInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'hug')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a hug..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is hugging {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.hugGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got hugged {self.getReceiveCount(self.ctx.author.id)} times, and hugged others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class KissInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'kiss')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a kiss..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is kissing {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.kissGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got kissed {self.getReceiveCount(self.ctx.author.id)} times, and kissed others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class PunchInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'punch')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a to punch something"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is punching {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.punchGif)

    def pingImage(self):
        return random.choice(botGifs.punchGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got punched {self.getReceiveCount(self.ctx.author.id)} times, and punched others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class KillInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'kill')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to kill someone"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} killed {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.killGif)

    def pingImage(self):
        return random.choice(botGifs.killGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got killed {self.getReceiveCount(self.ctx.author.id)} times, and killed others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class HandholdInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'handhold')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to hold someone's hand..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is holding {self.getJoinedNames(nameList)}'s hand{'' if len(nameList) < 2 else 's'}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.handholdGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got thier hand held {self.getReceiveCount(self.ctx.author.id)} times, and held others hands {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class LoveInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'love')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants love..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} loves {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.loveGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got loved {self.getReceiveCount(self.ctx.author.id)} times, and loved others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class CuddleInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'cuddle')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants to cuddle..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is cuddling {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.cuddleGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got cuddled with {self.getReceiveCount(self.ctx.author.id)} times, and cuddled others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class PatInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'pat')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a pat..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is patting {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.patGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got pat {self.getReceiveCount(self.ctx.author.id)} times, and patted others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class PeckInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'peck')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} wants a peck..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} pecks {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.peckGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got pecked {self.getReceiveCount(self.ctx.author.id)} times, and pecked others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class ChaseInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'chase')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is waiting for someone to chase..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is chasing {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.lurkGif)

    def pingImage(self):
        return random.choice(botGifs.chaseGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} was chased {self.getReceiveCount(self.ctx.author.id)} times, and chased others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class BoopInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'boop')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is looking for someone to boop..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} booped {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.lurkGif)

    def pingImage(self):
        return random.choice(botGifs.boopGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got booped {self.getReceiveCount(self.ctx.author.id)} times, and booped others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class BonkInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'bonk')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is looking for someone to bonk..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} bonked {self.getJoinedNames(nameList)}!"

    def noPingImage(self):
        return random.choice(botGifs.lurkGif)

    def pingImage(self):
        return random.choice(botGifs.bonkGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got bonked {self.getReceiveCount(self.ctx.author.id)} times, and bonked others {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

class RunInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'run')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is running away!"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is running at {self.getJoinedNames(nameList)}!"

    def noPingImage(self):
        return random.choice(botGifs.runGif)

    def pingImage(self):
        return random.choice(botGifs.chaseGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got ran at {self.getReceiveCount(self.ctx.author.id)} times, and ran {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class DieInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'die')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} died :c"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} wants {self.getJoinedNames(nameList)} to die :c"

    def noPingImage(self):
        return random.choice(botGifs.dieGif)

    def pingImage(self):
        return random.choice(botGifs.dieGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} died {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class DanceInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'dance')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} danced around!"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is dancing with {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.danceGif)

    def pingImage(self):
        return random.choice(botGifs.danceGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} was danced with {self.getReceiveCount(self.ctx.author.id)} times, and danced {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class LurkInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'lurk')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is lurking..."

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is watching {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.lurkGif)

    def pingImage(self):
        return random.choice(botGifs.lurkGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} was watched {self.getReceiveCount(self.ctx.author.id)} times, and lurked {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class PoutInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'pout')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is pouting"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is pouting at {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.poutGif)

    def pingImage(self):
        return random.choice(botGifs.poutGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} was pouted at {self.getReceiveCount(self.ctx.author.id)} times, and pouted {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class EatInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'eat')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is eating"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is eating {self.getJoinedNames(nameList)}!"

    def noPingImage(self):
        return random.choice(botGifs.eatGif)

    def pingImage(self):
        return random.choice(botGifs.eatGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} was eaten {self.getReceiveCount(self.ctx.author.id)} times, and ate {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class CryInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'cry')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is crying :c"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is crying for {self.getJoinedNames(nameList)} :c"

    def noPingImage(self):
        return random.choice(botGifs.cryGif)

    def pingImage(self):
        return random.choice(botGifs.cryGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} cried {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class BlushInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'blush')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is blushing"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is blushing becuase of {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.blushGif)

    def pingImage(self):
        return random.choice(botGifs.blushGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} blushed {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

class HideInteraction(BaseInteraction):

    def __init__(self, ctx: commands.Context, args):
        super().__init__(ctx, args, 'hide')

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.ctx.author.display_name} is hiding"

    def pingTitle(self, nameList):  #The title to use if there are pings
        return f"{self.ctx.author.display_name} is hiding from {self.getJoinedNames(nameList)}"

    def noPingImage(self):
        return random.choice(botGifs.hideGif)

    def pingImage(self):
        return random.choice(botGifs.hideGif)

    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} hid {self.getGiveCount(self.ctx.author.id)} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage

    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
        self.addGiveCount(self.ctx.author.id)

#endregion
