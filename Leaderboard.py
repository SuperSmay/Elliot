import json
import pathlib
import discord
from discord import embeds
from globalVariables import client, numberEmoteList, joinChannel
import time



class timeLeaderboard:

    def __init__(self, timeDelta, user):
        self.time = round(timeDelta.seconds + timeDelta.microseconds/1000000, 2)
        self.user = user        
        self.leaderboard = self.getLeaderboard()
        self.index = self.getIndex()
        self.leaderboardType = "leaveTime"

    def getIndex(self):
        if self.user.id == 812156805244911647:
            return 10
        index = 0
        while index < len(self.leaderboard[self.leaderboardType]):
            if self.leaderboard[self.leaderboardType][index]["time"] > self.time:
                return index
            index += 1
        return index

    def getLeaderboard(self):
        path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")
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

    async def scoreSubmit(self):
        if self.index < 10:
            channel = await client.fetch_channel(joinChannel[self.user.guild.id])
            await channel.send(self.getHighscoreMessage())
            self.saveLeaderboard()
            
    def saveLeaderboard(self):
        self.leaderboard[self.leaderboardType].insert(self.index, {"time" : self.time, "userID" : self.user.id})
        self.leaderboard[self.leaderboardType] = self.leaderboard[self.leaderboardType][:10]

        path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")

        file = open(path, "w")
        json.dump(self.leaderboard, file)
        file.close()

    def getHighscoreMessage(self):
        if self.index == 0:
            placement = "a __new record__"
        elif self.index == 1:
            placement = "2nd place"
        elif self.index == 2:
            placement = "3rd place"
        else:
            placement = f"{self.index + 1}th place"
        return f"Congratulations <@{self.user.id}>! You just got **{placement}** for fastest leaver with a time of **{self.time}** seconds!!"


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
            entry = f"{(await client.fetch_user(self.leaderboard['weeklyLeaveTime'][0]['userID'])).name} - {self.leaderboard['weeklyLeaveTime'][0]['time']} seconds"
            embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{self.message.guild.name}'s 7 Day Top Leaver☾∘∙⊱⋅•⋅", description= entry, color= 7528669)
            embed.set_thumbnail(url=client.user.avatar_url)
        else:
            leadboardList = [f"{self.getPositionNumber(self.leaderboard['leaveTime'].index(position))} - {(await client.fetch_user(position['userID'])).name} - {position['time']} seconds" for position in self.leaderboard["leaveTime"]]
            embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{self.message.guild.name}'s Leaver Leaderboard☾∘∙⊱⋅•⋅", color= 7528669)
            embed.add_field(name= "**Leaderboard**", value= "\n".join(leadboardList))
            embed.set_thumbnail(url=client.user.avatar_url)
            return embed

    def getPositionNumber(self, index):
        return numberEmoteList[index]

    async def send(self):
        await self.message.reply(embed= await self.getLeaderboardEmbed(), mention_author= False)

class weeklyTimeLeaderboard(timeLeaderboard):

    def __init__(self, timeDelta, user):
        self.time = round(timeDelta.seconds + timeDelta.microseconds/1000000, 2)
        self.user = user        
        self.leaderboard = self.getLeaderboard()
        self.index = self.getIndex()
        self.leaderboardType = "weeklyLeaveTime"
        try: self.leaderboard["weeklyLeaveTime"]
        except: self.leaderboard["weeklyLeaveTime"] = [{"time" : None, "userID" : None, "epochSeconds" : 0}]

    async def scoreSubmit(self):
        if time.time() - self.leaderboard[self.leaderboardType]["epochSeconds"] > 604800:
            channel = await client.fetch_channel(joinChannel[self.user.guild.id])
            await channel.send(self.getHighscoreMessage())
            self.saveLeaderboard()
        elif self.index == 0:
            channel = await client.fetch_channel(joinChannel[self.user.guild.id])
            await channel.send(self.getHighscoreMessage())
            self.saveLeaderboard()
            
    def saveLeaderboard(self, force = False):
        if force:
            self.leaderboard[self.leaderboardType][0] = {"time" : self.time, "userID" : self.user.id, "epochSeconds" : time.time()}
        else:
            self.leaderboard[self.leaderboardType].insert(self.index, {"time" : self.time, "userID" : self.user.id, "epochSeconds" : time.time()})
        self.leaderboard[self.leaderboardType] = self.leaderboard[self.leaderboardType][0]

        path = pathlib.Path(f"Leaderboard/{self.user.guild.id}")

        file = open(path, "w")
        json.dump(self.leaderboard, file)
        file.close()

    def getIndex(self):
        index = 0
        while index < len(self.leaderboard[self.leaderboardType]):
            if self.leaderboard[self.leaderboardType][index]["time"] > self.time:
                return index
            index += 1
        return index

    def getHighscoreMessage(self):
        if self.index == 0:
            return f"Congratulations <@{self.user.id}>! You just got a new 7 day record for fastest leaver with a time of **{self.time}** seconds!!"