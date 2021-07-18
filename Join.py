import random
from globalVariables import welcomeChannel, botRole

class Join:
    def __init__(self, member):
        self.member = member
        self.guild = member.guild

    def getJoinMessage(self):
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
        await channel.send(f"{self.getJoinMessage()}\nThere are now {self.getMemberCount()} customers in {self.guild.name}!")