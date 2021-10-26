import random

import discord
from globalVariables import welcomeChannel, botRole, logChannel

class Join:
    def __init__(self, member):
        self.member = member
        self.guild = member.guild

    async def getMessage(self):
        joinMessageList = [
            f"Welcome to {self.guild.name}, <@{self.member.id}>!!",
            f":0 Hello there <@{self.member.id}>, welcome to {self.guild.name}!",
            f"{self.guild.name} has a new customer! Welcome, <@{self.member.id}>!",
            f"🔔 \*Ding ding\* 🔔 <@{self.member.id}> just entered {self.guild.name}!",
            f"Hi <@{self.member.id}>, we hope you enjoy your time here at {self.guild.name}!"
        ]
        rolePlayMessageList = [
            f"Seat yourself anywhere you'd like!",
            f"There are some free tables to the left if you'd like to sit down!",
            f"Feel free to sit down anywhere you like!",
            f"There are drinks up front and free tables in the back!"
        ]
        return f"<:join:868675783026180097> {random.choice(joinMessageList)} {random.choice(rolePlayMessageList)}"


    def getMemberCount(self):
        memberCount = 0
        for member in self.guild.members:
            if not botRole[self.guild.id] in [role.id for role in member.roles]:
                memberCount += 1
        return memberCount


    async def send(self):
        if self.member.id == 812156805244911647: return  #Ignore alt
        try: channel = self.guild.get_channel(welcomeChannel[self.guild.id])
        except: return
        await channel.send(f"{await self.getMessage()}")
        await channel.send(f"`There are now {self.getMemberCount()} customers here at {self.guild.name}.`")
        await self.log()

    async def log(self):
        channel = self.guild.get_channel(logChannel[self.guild.id])
        embed = discord.Embed(title= "Member joined", description= f"User is {self.member.mention}", color= 15672122)
        embed.set_author(name= self.member.display_name, url= self.member.avatar.url)
        embed.set_footer(text= f"ID: {self.member.id}")
        embed.set_thumbnail(url= self.member.avatar.url)
        await channel.send(embed= embed)
class Leave(Join):

    async def getMessage(self):
        joinMessageList = [
            f"I hope you enjoyed your time at {self.guild.name}, {self.member.display_name}. Goodbye!",
            f"So long {self.member.display_name}. I hope you had fun at {self.guild.name}!",
            f"{self.member.display_name} has exited {self.guild.name}.",
            f":c {self.member.display_name} just left {self.guild.name}.",
            f"Sadly, {self.member.display_name} left {self.guild.name}!"
        ]
        banMessageList = [
            f"{self.member.display_name} was a nasty Karen and won't be missed. Goodbye!",
            f"{self.member.display_name} has been banned from returning to {self.guild.name}.",
            f"{self.member.display_name} had to be removed from {self.guild.name}.",
            f"The managers had to speak with {self.member.display_name}. Needless to say, it didn't go well for {self.member.display_name}."
        ]
        if await self.checkIfBanned(): return f"<:x_:868676514995118130> {random.choice(banMessageList)}"
        return f"<:leave:868675783302975538> {random.choice(joinMessageList)}"

    async def checkIfBanned(self):
        if self.member in [ban.user for ban in await self.member.guild.bans()]:
            return True
        return False

    async def log(self):
        channel = self.guild.get_channel(logChannel[self.guild.id])
        embed = discord.Embed(title= "Member leave", description= f"User is {self.member.mention}", color= 15672122)
        embed.set_author(name= self.member.display_name, url= self.member.avatar.url)
        embed.set_footer(text= f"ID: {self.member.id}")
        embed.set_thumbnail(url= self.member.avatar.url)
        await channel.send(embed= embed)
