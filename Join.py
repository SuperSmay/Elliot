import random
from globalVariables import welcomeChannel, botRole

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
        return f"{random.choice(joinMessageList)} {random.choice(rolePlayMessageList)}"


    def getMemberCount(self):
        memberCount = 0
        for member in self.guild.members:
            if not botRole[self.guild.id] in [role.id for role in member.roles]:
                memberCount += 1
        return memberCount


    async def send(self):
        channel = self.guild.get_channel(welcomeChannel[self.guild.id])
        await channel.send(f"{await self.getMessage()}\nThere are now {self.getMemberCount()} customers in {self.guild.name}")

class Leave(Join):

    async def getMessage(self):
        joinMessageList = [
            f"I hope you enjoyed your time at {self.guild.name}, <@{self.member.id}>. Goodbye!",
            f"So long <@{self.member.id}>. I hope you had fun at {self.guild.name}!",
            f"<@{self.member.id}> has exited {self.guild.name}.",
            f":c <@{self.member.id}> just left {self.guild.name}.",
            f"Sadly, <@{self.member.id}> left {self.guild.name}!"
        ]
        banMessageList = [
            f"<@{self.member.id}> was a nasty Karen and won't be missed. Goodbye!",
            f"<@{self.member.id}> has been banned from returning to {self.guild.name}.",
            f"<@{self.member.id}> had to be removed from {self.guild.name}.",
            f"The managers had to speak with <@{self.member.id}>. Needless to say, it didn't go well for <@{self.member.id}>."
        ]
        if await self.checkIfBanned(): return random.choice(banMessageList)
        return random.choice(joinMessageList)

    async def checkIfBanned(self):
        if self.member in [ban.user for ban in await self.member.guild.bans()]:
            return True
        return False
