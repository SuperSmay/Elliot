import random
import botGifs
from globalVariables import client, prefix
from fnmatch import fnmatch
import traceback
import pathlib
import json
import random

import discord

class BaseInteraction:

    def __init__(self, message, interaction):
        self.message = message
        self.interaction = interaction
        self.arguments = self.getArguments()
        self.nameList = []
        self.pingList = []
        self.includedMessage = ""
        self.footer = ""

    async def send(self):  #Replys with the embed or an error
        try: 
            await self.splitIntoNamesAndMessage()
            self.updateCounts()
            await self.message.reply(embed= self.embed(), mention_author= False)
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\31415\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nMessage: {self.message.content}\nInteraction: {self.interaction}\nArguments: {self.arguments}\nnameList: {self.nameList}\nincludedMessage: {self.includedMessage}"
            await self.message.reply(content= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps to <@243759220057571328> ```{error}```", mention_author= False) 
            traceback.print_exc()
            return
   
    def updateCounts(self):
        if len(self.pingList) > 0:
            for ping in self.pingList:
                ping = self.getIDFromPing(ping) 
                self.addReceiveCount(ping)
            self.addGiveCount()
    
    def getCountMessage(self):
        countMessage = f"{self.message.author.display_name} got tested {self.getReceiveCount(self.message.author.id)} times, and tested others {self.getGiveCount()} times." 
        countMessage = countMessage.replace(" 1 times", " once").replace("69", "69 hehe") if random.randint(0, 100) != 0 else countMessage.replace(" times", " **o**__n__c*é*")
        return countMessage

    def embed(self):  #Creates the embed to be sent
        embedToReturn = discord.Embed(title= self.getEmbedTitle(), description= self.includedMessage, color= self.getColor())
        embedToReturn.set_image(url= self.getImageURL())
        embedToReturn.set_footer(text= f"{self.getCountMessage()} {self.footer}" )
        return embedToReturn

    def getEmbedTitle(self):  #Gets the title of the embed from noPingTitle and pingTitle
        if len(self.nameList) == 0:
            return self.noPingTitle()
        return self.pingTitle()

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.message.author.display_name}"

    def pingTitle(self):  #The title to use if there are pings
        return f"{self.message.author.display_name} --> {self.getJoinedNames()}"

    def getJoinedNames(self):  #Joins all the names used into a nice string
        if len(self.nameList) < 2:
            return self.nameList[0]
        elif len(self.nameList) == 2:
            return f"{self.nameList[0]} and {self.nameList[1]}"
        else: 
            return ", ".join(self.nameList[:-1]) + ", and " + self.nameList[-1]

    async def checkIfPingIsValid(self, ping):  #Check if the first ping is valid for the guild
        if fnmatch(ping, "<@*>"):
            if self.getIDFromPing(ping) in [user.id for user in self.message.channel.members]:
                return True
        return False

    async def splitIntoNamesAndMessage(self):  #Splits the arugments into the nameList and included message and stores them in the class variables

        async def getUserPings(self):
            pingIndex = 0
            pingList = []
            while pingIndex < len(self.arguments) and fnmatch(self.arguments[pingIndex], "<@*>"):
                if fnmatch(self.arguments[pingIndex], f"<@*{self.message.author.id}>"):  #If the user that sent the message pinged themselves, skip adding it to the ping list
                    del self.arguments[pingIndex]
                elif not await self.checkIfPingIsValid(self.arguments[pingIndex]):  #If there is a user pinged that can't see the current channel, then skip adding it to the ping list and tell the user that it was ignored in the embed footer
                    del self.arguments[pingIndex]
                    self.footer = "One or more of the users you mentioned cannot see this channel or aren't in this server, so they were ignored"
                else:
                    pingList.append(self.arguments[pingIndex])
                    del self.arguments[pingIndex]
            self.pingList = pingList
            return pingList

        async def getUserNames(self):
            userList = [await self.message.guild.fetch_member(self.getIDFromPing(ping)) for ping in await getUserPings(self)]
            self.nameList = [user.display_name for user in userList]

        def getIncludedMessage(self):
            self.includedMessage = " ".join(self.arguments)

        await getUserNames(self)
        getIncludedMessage(self)  
    
    def getColor(self):
        return random.choice(botGifs.colors)

    def getArguments(self):
        argString = self.message.content[len(prefix) + len(self.interaction) + 1:].strip()  #Remove the prefix and interaction by cutting the string by the length of those two combined
        return argString.split(" ")

    def getIDFromPing(self, ping):
        id = ping.replace("<", "").replace(">", "").replace("@", "").replace("!", "").replace("&", "")
        return int(id)

    def getImageURL(self):  #Gets the image for the embed from noPingImage and pingImage
        if len(self.nameList) == 0:
            return self.noPingImage()
        return self.pingImage()

    def noPingImage(self):
        return "https://images-ext-2.discordapp.net/external/T2EiRPQoyjtgufZFuk9sUh5CpvjdZHD9fMx2r2iFwv4/https/c.tenor.com/RRG7pXMcSloAAAAM/sad-anime.gif"

    def pingImage(self):
        return "https://images-ext-1.discordapp.net/external/jdZsQ2YnpjXowNPa42l7p52SKfc-iddn1YlpN_BXt3M/https/c.tenor.com/UhcyGsGpLNIAAAAM/hug-anime.gif"
    
    def getGiveCount(self):
        path = pathlib.Path(f"InteractionCount/{self.message.author.id}")
        if path.exists():
            file = open(path, "r")
            countDict = json.load(file)
            file.close()
            if self.interaction in countDict.keys():
                return countDict[self.interaction]["give"]
        return 0
    
    def addGiveCount(self):
        path = pathlib.Path(f"InteractionCount/{self.message.author.id}")
        if path.exists():
            file = open(path, "r")
            countDict = json.load(file)
            file.close()
            if self.interaction in countDict.keys():
                countDict[self.interaction]["give"] += 1
            else:
                countDict[self.interaction] = {"give" : 0, "receive" : 0}
                countDict[self.interaction]["give"] += 1
            file = open(path, "w")
            json.dump(countDict, file)
            file.close()
            return countDict[self.interaction]["give"]
        else:
            countDict = {}
            countDict[self.interaction] = {"give" : 0, "receive" : 0}
            countDict[self.interaction]["give"] += 1
            file = open(path, "w+")
            json.dump(countDict, file)
            file.close()
            return countDict[self.interaction]["give"]

    def getReceiveCount(self, userID):
        path = pathlib.Path(f"InteractionCount/{userID}")
        if path.exists():
            file = open(path, "r")
            countDict = json.load(file)
            file.close()
            if self.interaction in countDict.keys():
                return countDict[self.interaction]["receive"]
        return 0
    
    def addReceiveCount(self, userID):
        path = pathlib.Path(f"InteractionCount/{userID}")
        if path.exists():
            file = open(path, "r")
            countDict = json.load(file)
            file.close()
            if self.interaction in countDict.keys():
                countDict[self.interaction]["receive"] += 1
            else:
                countDict[self.interaction] = {"give" : 0, "receive" : 0}
                countDict[self.interaction]["receive"] += 1
            file = open(path, "w")
            json.dump(countDict, file)
            file.close()
            return countDict[self.interaction]["receive"]
        else:
            countDict = {}
            countDict[self.interaction] = {"give" : 0, "receive" : 0}
            countDict[self.interaction]["receive"] += 1
            file = open(path, "w+")
            json.dump(countDict, file)
            file.close()
            return countDict[self.interaction]["receive"]

class HugInteraction(BaseInteraction):

    def noPingTitle(self):  #The title to use if no pings are provided
        return f"{self.message.author.display_name} wants a hug..."

    def pingTitle(self):  #The title to use if there are pings
        return f"{self.message.author.display_name} is hugging {self.getJoinedNames()}"

    def noPingImage(self):
        return random.choice(botGifs.selfHugGif)

    def pingImage(self):
        return random.choice(botGifs.hugGif)

    def getCountMessage(self):
        countMessage = f"{self.message.author.display_name} got hugged {self.getReceiveCount(self.message.author.id)} times, and hugged others {self.getGiveCount()} times." 
        countMessage = countMessage.replace("1 times", "once")
        return countMessage
