import random

import botGifs
from fnmatch import fnmatch
import traceback
import pathlib
import json

import discord
import discord.ext.commands

from globalFiles import interactionDict

class BaseInteraction:

    def __init__(self, ctx:discord.ext.commands.Context, args, interaction):
        self.ctx = ctx
        self.interaction = interaction
        self.arguments = args
        self.nameList = []
        self.includedMessage = ""
        self.footer = ""

    async def run(self):  #Replys with the embed or an error
        try:
            userIDList, includedMessage = self.splitIntoIDsAndMessage()
            self.updateCounts(userIDList)
            return [await self.embed(userIDList, includedMessage)]
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\31415\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nInteraction: {self.interaction}\nArguments: {self.arguments}\nnameList: {self.nameList}\nincludedMessage: {self.includedMessage}"
            embed = discord.Embed(description= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```") 
            traceback.print_exc()
            return [embed]
   
    def updateCounts(self, userIDList):
        if len(userIDList) > 0:
            for id in userIDList:
                self.addReceiveCount(id)
            self.addGiveCount(self.ctx.author.id)
    
    def getCountMessage(self):
        countMessage = f"{self.ctx.author.display_name} got tested {self.getReceiveCount(self.ctx.author.id)} times, and tested others {self.getGiveCount()} times." 
        countMessage = countMessage.replace(" 1 times", " once").replace("69", "69 hehe") if random.randint(0, 20) != 0 else countMessage.replace("1 times", "**o**__n__c*é*")
        return countMessage

    async def embed(self, userIDList, includedMessage):  #Creates the embed to be sent
        nameList = [(await self.ctx.guild.fetch_member(id)).display_name for id in userIDList]
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
        if len(nameList) < 2:
            return nameList[0]
        elif len(nameList) == 2:
            return f"{nameList[0]} and {nameList[1]}"
        else: 
            return ", ".join(nameList[:-1]) + ", and " + nameList[-1]

    def checkIfPingOrID(self, ping):  #Check if the first ping is valid for the guild
        if fnmatch(ping, "<@*>") and self.getIDFromPing(ping) in [user.id for user in self.ctx.channel.members]: return True
        elif ping in [str(user.id) for user in self.ctx.channel.members]: return True
        return False

    def splitIntoIDsAndMessage(self):  #Splits the arugments into the nameList and included message and stores them in the class variables

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
        if str(userID) in interactionDict.keys():
            countDict = interactionDict[str(userID)]
            if self.interaction in countDict.keys():
                return countDict[self.interaction]["give"]
        return 0
    
    def addGiveCount(self, userID):
        if str(userID) in interactionDict.keys():
            countDict = interactionDict[str(userID)]
            if self.interaction in countDict.keys():
                countDict[self.interaction]["give"] += 1
            else:
                countDict[self.interaction] = {"give" : 0, "receive" : 0}
                countDict[self.interaction]["give"] += 1
            return countDict[self.interaction]["give"]
        else:
            countDict = {}
            countDict[self.interaction] = {"give" : 0, "receive" : 0}
            countDict[self.interaction]["give"] += 1
            return countDict[self.interaction]["give"]

    def getReceiveCount(self, userID):
        if str(userID) in interactionDict.keys():
            countDict = interactionDict[str(userID)]
            if self.interaction in countDict.keys():
                return countDict[self.interaction]["receive"]
        return 0
    
    def addReceiveCount(self, userID):
        if str(userID) in interactionDict.keys():
            countDict = interactionDict[str(userID)]
            if self.interaction in countDict.keys():
                countDict[self.interaction]["receive"] += 1
            else:
                countDict[self.interaction] = {"give" : 0, "receive" : 0}
                countDict[self.interaction]["receive"] += 1
            return countDict[self.interaction]["receive"]
        else:
            countDict = {}
            countDict[self.interaction] = {"give" : 0, "receive" : 0}
            countDict[self.interaction]["receive"] += 1
            return countDict[self.interaction]["receive"]

class HugInteraction(BaseInteraction):

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
