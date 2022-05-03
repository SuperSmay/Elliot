import json
import pathlib
from typing import List
import discord
import math
from globalVariables import bot, numberEmoteList
import time


class Leaderboard:

    def __init__(self, user, type = "default"):
        #Options
        self.type = type
        self.overwriteOldScore = False
        self.leaderboardName = "default"


        self.annouce = False
        self.indexToAnnounce = 0
        self.user = user
        self.score = 0
        self.lowerScoreBetter = False
        self.leaderboard = self.getLeaderboard()


    #Get leaderboard 
    def getLeaderboard(self) -> List:
        path = pathlib.Path(f"Leaderboard/{self.user.guild.id}/{self.type}")
        if path.exists():
            leaderboard = self.loadLeaderboard(path)
        else:
            print('Leaderboard does not exist, creating new leaderboard...')
            leaderboard = self.createNewLeaderboard(path)
        return leaderboard

    #Load leaderboard
    def loadLeaderboard(self, path):
        file = open(path, "r")
        leaderboard = json.load(file)
        file.close()
        return leaderboard

    #Create file for leaderboard
    def createNewLeaderboard(self, path):
        folderPath = path.parent
        print(folderPath)
        if not folderPath.exists():
            folderPath.mkdir()
        file = open(path, "w+")
        leaderboard = self.getEmptyLeaderboard()
        json.dump(leaderboard, file)
        file.close()
        return leaderboard

    def setUserScore(self, score):
        self.score = score

    def getUserScore(self):
        for entry in self.leaderboard:
            if entry["userID"] == self.user.id: return entry["score"]
        return 0

    def addUserScore(self, score):
        self.score = self.getUserScore() + score

    def userBetterThanIndex(self, index):
        return (self.score > self.leaderboard[index]["score"] and not self.lowerScoreBetter) or (self.score < self.leaderboard[index]["score"] and self.lowerScoreBetter)
    
    def getIndexToInsert(self):
        index = 0
        while index < len(self.leaderboard):
            if self.userBetterThanIndex(index):
                return index
            index += 1
        return index

    #make comparison dictionary
    def entryDict(self):
        return {
            "userID" : self.user.id,
            "score" : self.score
        }

    def userOnLeaderboard(self):
        for entry in self.leaderboard:
            if entry["userID"] == self.user.id: return True
        return False

    def getUserIndexOnLeaderboard(self):
        index = 0
        while index < len(self.leaderboard):
            if self.leaderboard[index]["userID"] == self.user.id: return index
            index += 1
        return -1

    #Edit 
    def setScoreOnLeaderboard(self):
        if self.userOnLeaderboard() and ((self.getUserScore() < self.score and not self.lowerScoreBetter) or (self.getUserScore() > self.score and self.lowerScoreBetter) or self.overwriteOldScore):
            self.indexToAnnounce = self.getIndexToInsert()
            del self.leaderboard[(self.getUserIndexOnLeaderboard())]
            self.leaderboard.insert(self.getIndexToInsert(), self.entryDict())
            self.annouce = True
        elif not self.userOnLeaderboard():
            self.indexToAnnounce = self.getIndexToInsert()
            self.leaderboard.insert(self.getIndexToInsert(), self.entryDict())
            self.annouce = True
    
    #save
    def saveLeaderboard(self):
        path = pathlib.Path(f"Leaderboard/{self.user.guild.id}/{self.type}")
        file = open(path, "w")
        json.dump(self.leaderboard, file)
        file.close()
###
    

    #Get empty leaderboard
    def getEmptyLeaderboard(self):
        return []


    #Message to send
    def positionAnnoucenment(self):
        return f"Congratulations <@{self.user.id}>! You just got **{self.placement()}** on the {self.leaderboardName} leaderboard with a score of **{self.score}**!!"

    def placement(self):
        index = self.getUserIndexOnLeaderboard()
        if index == 0:
            placement = "a __new record__"
        
        elif index % 10 == 1:
            placement = f"{index + 1}nd place"
        elif index % 10 == 2:
            placement = f"{index + 1}rd place"
        else:
            placement = f"{index + 1}th place"
        if index == 11:
            placement = "12th place"
        if index == 12:
            placement = "13th place"
        return placement

    #Create leaderboard
    async def getLeaderboardEmbed(self, pageIndex = 0):
        embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{self.user.guild.name}'s {self.leaderboardName} Leaderboard☾∘∙⊱⋅•⋅", color= 7528669)
        embed.add_field(name= "**Leaderboard**", value= self.leaderboardString(await self.leaderboardList(pageIndex)))
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text=f'Page {pageIndex + 1} of {math.ceil(len(self.leaderboard) / 10)}')
        return embed

    def getPositionNumber(self, index):
        try: return numberEmoteList[index]
        except: return numberEmoteList[9]

        #List of users
    async def leaderboardList(self, pageIndex):
        leaderboardList = [f"{self.getPositionNumber(self.leaderboard.index(position))} - {(await bot.fetch_user(position['userID'])).name} - {position['score']} seconds" for position in self.leaderboard[pageIndex * 10:(pageIndex + 1) * 10]]
        return leaderboardList[:10]

    def leaderboardString(self, leaderboardList):
        if len(leaderboardList) == 0:
            return "This leaderboard is empty"
        return "\n".join(leaderboardList)

    #message for specific user

        #Create message to send if they are


class timeLeaderboard(Leaderboard):
    def __init__(self, user):
        super().__init__(user, "leaveTime")
        self.leaderboardName = "Leaver"
        self.lowerScoreBetter = True

    def positionAnnoucenment(self):
        return f"Congratulations <@{self.user.id}>! You just got **{self.placement()}** for fastest leaver with a time of **{self.score}** seconds!!"


class weeklyTimeLeaderboard(Leaderboard):
    def __init__(self, user):
        super().__init__(user, "weeklyLeaveTime")
        self.leaderboardName = "7 day leaver"
        self.lowerScoreBetter = True

    def entryDict(self):
        return {
            "userID" : self.user.id,
            "score" : self.score,
            "joinTime" : time.time()
        }

    def setScoreOnLeaderboard(self):
        if len(self.leaderboard) == 0 or time.time() - self.leaderboard[0]["joinTime"] > 604800 or self.score < self.leaderboard[0]["score"]:
            self.leaderboard = [self.entryDict()]
            self.annouce = True

    def positionAnnoucenment(self):
        return f"Congratulations <@{self.user.id}>! You just got **{self.placement()}** for fastest 7 day leaver with a time of **{self.score}** seconds!!"




# class timeLeaderboard:

#     def __init__(self, timeDelta, user):
#         self.time = round(timeDelta.seconds + timeDelta.microseconds/1000000, 2)
#         self.user = user        
#         self.leaderboardType = "leaveTime"
#         self.leaderboard = self.getLeaderboard()
#         self.index = self.getIndex()
        
#     def getIndex(self):
#         index = 0
#         while index < len(self.leaderboard[self.leaderboardType]):
#             if self.leaderboard[self.leaderboardType][index]["time"] > self.time:
#                 return index
#             index += 1
#         return index

#     def getLeaderboard(self):
#         path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")
#         if pathlib.Path.exists(path):
#             file = open(path, "r")
#             leaderboard = json.load(file)
#             file.close()
#         else:
#             leaderboard = {"leaveTime" : [], "weeklyLeaveTime" : []}
#             file = open(path, "w+")
#             json.dump(leaderboard, file)
#             file.close()
#         return leaderboard

#     async def scoreSubmit(self):
#         #if self.user.id == 812156805244911647: return  #Ignore alt
#         if self.index < 10:
#             channel = await client.fetch_channel(joinChannel[self.user.guild.id])
#             await channel.send(self.getHighscoreMessage())
#             self.saveLeaderboard()
            
#     def saveLeaderboard(self):
#         self.leaderboard[self.leaderboardType].insert(self.index, {"time" : self.time, "userID" : self.user.id})
#         self.leaderboard[self.leaderboardType] = self.leaderboard[self.leaderboardType][:10]

#         path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")

#         file = open(path, "w")
#         json.dump(self.leaderboard, file)
#         file.close()

#     def getHighscoreMessage(self):
#         if self.index == 0:
#             placement = "a __new record__"
#         elif self.index == 1:
#             placement = "2nd place"
#         elif self.index == 2:
#             placement = "3rd place"
#         else:
#             placement = f"{self.index + 1}th place"
#         return f"Congratulations <@{self.user.id}>! You just got **{placement}** for fastest leaver with a time of **{self.time}** seconds!!"


class FetchLeaderboard:
    def __init__(self, message):
        self.message = message
        self.leaderboard = self.getLeaderboard()
        self.arguments = self.getArguments()

    def getArguments(self):
        return self.message.content.split(" ")[2:]

    def isWeekly(self):
        return len(self.arguments) > 0 and self.arguments[0].startswith("week")
    
    def getLeaderboard(self):
        path = pathlib.Path(f"Leaderboard/{self.message.guild.id}")
        if pathlib.Path.exists(path):
            file = open(path, "r")
            leaderboard = json.load(file)
            file.close()
        else:
            leaderboard = {"leaveTime" : [], "weeklyLeaveTime" : []}
            file = open(path, "w+")
            json.dump(leaderboard, file)
            file.close()
        return leaderboard
    
    async def getLeaderboardEmbed(self):
        if self.isWeekly():
            entry = f"**{(await bot.fetch_user(self.leaderboard['weeklyLeaveTime']['userID'])).name} - {self.leaderboard['weeklyLeaveTime']['time']} seconds**"
            embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{self.message.guild.name}'s 7 Day Top Leaver☾∘∙⊱⋅•⋅", description= entry, color= 7528669)
            embed.set_thumbnail(url=bot.user.avatar_url)
        else:
            leadboardList = [f"{self.getPositionNumber(self.leaderboard['leaveTime'].index(position))} - {(await bot.fetch_user(position['userID'])).name} - {position['time']} seconds" for position in self.leaderboard["leaveTime"]]
            embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{self.message.guild.name}'s Leaver Leaderboard☾∘∙⊱⋅•⋅", color= 7528669)
            embed.add_field(name= "**Leaderboard**", value= "\n".join(leadboardList))
            embed.set_thumbnail(url=bot.user.avatar_url)
        return embed

    def getPositionNumber(self, index):
        return numberEmoteList[index]

    async def send(self):
        await self.message.reply(embed= await self.getLeaderboardEmbed(), mention_author= False)

# class weeklyTimeLeaderboard:

#     def __init__(self, timeDelta, user):
#         self.time = round(timeDelta.seconds + timeDelta.microseconds/1000000, 2)
#         self.user = user        
#         self.leaderboard = self.getLeaderboard()
#         self.leaderboardType = "weeklyLeaveTime"
#         try: temp = self.leaderboard[self.leaderboardType]
#         except: self.leaderboard[self.leaderboardType] = {"time" : 0, "userID" : 0, "epochSeconds" : 0}

#     def getLeaderboard(self):
#         path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")
#         if pathlib.Path.exists(path):
#             file = open(path, "r")
#             leaderboard = json.load(file)
#             file.close()
#         else:
#             leaderboard = {"leaveTime" : [], "weeklyLeaveTime" : {}}
#             file = open(path, "w+")
#             json.dump(leaderboard, file)
#             file.close()
#         return leaderboard

#     async def scoreSubmit(self):
#         if self.user.id == 812156805244911647: return  #Ignore alt
#         if time.time() - self.leaderboard[self.leaderboardType]["epochSeconds"] > 604800:
#             channel = await client.fetch_channel(joinChannel[self.user.guild.id])
#             await channel.send(self.getHighscoreMessage())
#             self.saveLeaderboard(force= True)
#         elif self.time < self.leaderboard[self.leaderboardType]["time"]:
#             channel = await client.fetch_channel(joinChannel[self.user.guild.id])
#             await channel.send(self.getHighscoreMessage())
#             self.saveLeaderboard()
            
#     def saveLeaderboard(self, force = False):
#         if force:
#             self.leaderboard[self.leaderboardType] = {"time" : self.time, "userID" : self.user.id, "epochSeconds" : time.time()}
#         else:
#             self.leaderboard[self.leaderboardType] = {"time" : self.time, "userID" : self.user.id, "epochSeconds" : time.time()}

#         path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")

#         file = open(path, "w")
#         json.dump(self.leaderboard, file)
#         file.close()

#     def getHighscoreMessage(self):
#         return f"Congratulations <@{self.user.id}>! You just got a new 7 day record for fastest leaver with a time of **{self.time}** seconds!!"