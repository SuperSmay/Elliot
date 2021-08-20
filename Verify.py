import discord
from discord import message
from globalVariables import unverifiedRole, ageRoleList, pronounRoleList, tooOldRole, verifiedRole, logChannel, roleChannel, client
import traceback

class Verify:

    def __init__(self, member, message= None):
        self.guild = member.guild
        self.member = member
        self.message = message

    async def verify(self):
        await self.member.remove_roles(self.guild.get_role(unverifiedRole[self.guild.id]), reason= 'Autoverify')
        await self.member.add_roles(self.guild.get_role(verifiedRole[self.guild.id]))
        await self.logAction(f"Autoverified {self.member.mention}")
        try: await self.member.send("You've been verified. Welcome to The Gayming Café!!")
        except discord.errors.Forbidden: await self.message.reply(content= f"You've been verified. Welcome to The Gayming Café!!", mention_author= False) 

    async def ageDeny(self):
        await self.member.send("Sorry, The Gayming Café has an age limit of 20. If you chose the 21+ role accidentally, feel free to join again.")
        await self.guild.kick(user= self.member, reason= "Autokick - Over age limit")
        await self.logAction(f"Autokicked {self.member.mention} - Over age limit")

    async def verifyInfo(self):
        await self.message.reply(f"To get verified, you must have at least one pronoun role and an age role, from <#{roleChannel[self.guild.id]}>. If you don't feel comfortable sharing your age or have other difficulties, feel free to DM any Manager or Barista, and they'll help you out!", mention_author= False)

    async def checkVerifyStatus(self):
        try:
            if unverifiedRole[self.guild.id] in [role.id for role in self.member.roles]:
                if self.isTooOld():
                    await self.ageDeny()
                elif self.hasPronounRole() and self.hasAgeRole():
                    await self.verify()
                elif self.message != None and "verify" in self.message.content or "verified" in self.message.content or "help" in self.message.content:
                    await self.verifyInfo()
        except:
            if self.message == None:
                traceback.print_exc()
                return
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\31415\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nMessage: {self.message.content}"
            await self.message.reply(content= f"An error occured. If you're seeing this it means <@243759220057571328> is a big dummy. If you can reproduce this message DM reproduction steps to <@243759220057571328>", mention_author= False) 
            smay = await client.fetch_user()
            smay.send(f"An error occured.\nMessage link: https://discord.com/channels/{self.message.guild.id}/{self.message.channel.id}/{self.message.id}\n```{error}```")
            traceback.print_exc()
            return

    async def logAction(self, action):
        channel = self.guild.get_channel(logChannel[self.guild.id])
        embed = discord.Embed(title= 'Automatic action taken', description= action)
        await channel.send(embed= embed)

    def hasAgeRole(self):
        for roleID in ageRoleList[self.guild.id]:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def hasPronounRole(self):
        for roleID in pronounRoleList[self.guild.id]:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def isTooOld(self):
        if tooOldRole[self.guild.id] in [role.id for role in self.member.roles]:
            return True
        return False

    