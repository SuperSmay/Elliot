import json
import pathlib
import discord
from discord import embeds
from globalVariables import client

joinChannel = {
    811369107181666343 : 811386285876445184,
    764385563289452545 : 764385563813871618
    }

class timeLeaderboard:

    def __init__(self, timeDelta, user):
        self.time = round(timeDelta.seconds + timeDelta.microseconds/1000000, 2)
        self.user = user        
        self.leaderboard = self.getLeaderboard()
        self.index = self.getIndexInTopTen()

    def getIndexInTopTen(self):
        index = 0
        while index < len(self.leaderboard["leaveTime"]):
            if self.leaderboard["leaveTime"][index]["time"] > self.time:
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
            leaderboard = {"leaveTime" : []}
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
        self.leaderboard["leaveTime"].insert(self.index, {"time" : self.time, "userID" : self.user.id})
        self.leaderboard["leaveTime"] = self.leaderboard["leaveTime"][:9]

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
            placement = f"{self.index}th place"
        return f"Congratulations <@{self.user.id}>! You just got **{placement}** for fastest leaver with a time of **{self.time}** seconds!!"


class FetchLeaderboard:
    def __init__(self, message):
        self.message = message
        self.leaderboard = self.getLeaderboard()

    def getLeaderboard(self):
        path = pathlib.Path(f"Leaderboard/{self.message.guild.id}")
        if pathlib.Path.exists(path):
            file = open(path, "r")
            leaderboard = json.load(file)
            file.close()
        else:
            leaderboard = {"leaveTime" : []}
            file = open(path, "w+")
            json.dump(leaderboard, file)
            file.close()
        return leaderboard
    
    def getLeaderboardEmbed(self):
        leadboardList = [f"{self.leaderboard['leaveTime'].index(position) + 1} - <@{position['userID']}> - {position['time']} seconds" for position in self.leaderboard["leaveTime"]]
        embed = discord.Embed(title= f"{self.message.guild.name}'s Leaver Leaderboard", color= 7528669)
        embed.add_field(name= "**Leaderboard**", value= "\n".join(leadboardList))
        embed.set_thumbnail(url=client.user.avatar_url)
        return embed

    async def send(self):
        await self.message.reply(embed= self.getLeaderboardEmbed(), mention_author= False)

