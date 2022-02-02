import random

import botGifs
from fnmatch import fnmatch
import traceback
import pathlib
import json

import discord
from discord.ext import commands, tasks
from discord.commands import Option, slash_command, context

import asyncio

from globalVariables import bot, prefix


class Interaction(commands.Cog):

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

    @commands.command(name="hug", description="Hugs a user!")
    async def hug_prefix(self, ctx, *args):
        await ctx.reply(embed=HugInteraction(ctx, args).run_and_get_response(), mention_author=False)

    @slash_command(name="hug", description="Hugs a user!")
    async def hug_slash(self, ctx, user:Option(discord.Member, description='User to hug', required=False), message:Option(str, description='Message to include', required=False)):
        args = []
        if user != None: args.append(user.mention)
        if message != None: args += message.split(' ')
        await ctx.respond(embed=HugInteraction(ctx, args).run_and_get_response())

    

class BaseInteraction():

    def __init__(self, ctx:commands.Context, args, interactionName):
        self.ctx = ctx
        self.interactionName = interactionName
        self.arguments = args
        self.nameList = []
        self.includedMessage = ""
        self.footer = ""

        self.interactionDict = (bot.get_cog('Interaction')).interactionDict

    def run_and_get_response(self):  #Replys with the embed or an error
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
        return False

    def splitIntoIDsAndMessage(self):  #Splits the arugments into the nameList and included message and stores them in the class variables

        userIDList = []
        messageList = []
        tempArgs = list(self.arguments)
        while 0 < len(tempArgs):
            if fnmatch(tempArgs[0], f"<@*{self.ctx.author.id}>") or tempArgs[0] == str(self.ctx.author.id):  #If the user that sent the message pinged themselves, skip adding it to the ping list
                del tempArgs[0]
            elif self.checkIfPingOrID(tempArgs[0]) and not self.getIDFromPing(tempArgs[0]) in userIDList:  #If the argument is a ping or valid id of a user in the channel, and isn't already in the ID list, add it to the ID list
                userIDList.append(self.getIDFromPing(tempArgs[0]))
                del tempArgs[0]
            else:
                messageList.append(tempArgs[0])
                del tempArgs[0]

        includedMessage = " ".join(messageList)

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
