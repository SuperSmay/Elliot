import discord
from globalVariables import unverifiedRole, ageRoleList, pronounRoleList, tooOldRole, verifiedRole, logChannel, roleChannel
import traceback

class Verify:

    def __init__(self, message):
        self.member = message.author
        self.message = message

    async def verify(self):
        await self.member.remove_roles(self.message.guild.get_role(unverifiedRole[self.message.guild.id]), reason= 'Autoverify')
        await self.member.add_roles(self.message.guild.get_role(verifiedRole[self.message.guild.id]))
        await self.logAction(f"Autoverified {self.message.author.mention}")
        await self.member.send("You've been verified. Welcome to The Gayming Café!!")

    async def ageDeny(self):
        await self.member.send("Sorry, The Gayming Café has an age limit of 19. If you chose the 20+ role accidentally, feel free to join again.")
        await self.message.guild.kick(user= self.member, reason= "Autokick - Over age limit")
        await self.logAction(f"Autokicked {self.message.author.mention} - Over age limit")

    async def verifyInfo(self):
        await self.message.reply(f"To get verified, you must have at least one pronoun role and an age role, from <#{roleChannel[self.message.guild.id]}>. If you don't feel comfortable sharing your age or have other difficulties, feel free to DM any Manager or Barista, and they'll help you out!", mention_author= False)

    async def checkVerifyStatus(self):
        try:
            if unverifiedRole[self.message.guild.id] in [role.id for role in self.member.roles]:
                if self.hasPronounRole() and self.hasAgeRole():
                    await self.verify()
                elif self.isTooOld():
                    await self.ageDeny()
                elif "verify" in self.message.content or "verified" in self.message.content or "help" in self.message.content:
                    await self.verifyInfo()
        except:
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\31415\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nMessage: {self.message.content}"
            await self.message.reply(content= f"An error occured. If you can reproduce this message, DM a screenshot and reproduction steps To <@243759220057571328> ```{error}```", mention_author= False) 
            traceback.print_exc()
            return

    async def logAction(self, action):
        channel = self.message.guild.get_channel(logChannel[self.message.guild.id])
        embed = discord.Embed(title= 'Automatic action taken', description= action)
        await channel.send(embed= embed)

    def hasAgeRole(self):
        for roleID in ageRoleList[self.message.guild.id]:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def hasPronounRole(self):
        for roleID in pronounRoleList[self.message.guild.id]:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def isTooOld(self):
        if tooOldRole[self.message.guild.id] in [role.id for role in self.member.roles]:
            return True
        return False

    