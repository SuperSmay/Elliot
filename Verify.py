import discord
from Settings import fetch_setting
from globalVariables import bot
import traceback

class Verify:

    def __init__(self, member, message= None):
        self.guild = member.guild
        self.member = member
        self.message = message

    async def verify(self):
        unverifiedRole = fetch_setting(self.guild.id, 'unverified_role')
        verifiedRole = fetch_setting(self.guild.id, 'verified_role')
        welcomeChannel = fetch_setting(self.guild.id, 'welcome_channel')
        try:
            await self.member.remove_roles(self.guild.get_role(unverifiedRole), reason= 'Autoverify')
            await self.member.add_roles(self.guild.get_role(verifiedRole))
        except discord.errors.Forbidden:
            return
        try: await self.logAction(f"Autoverified {self.member.mention}")
        except AttributeError: pass  #I don't even know it just doesn't work sometimes
        try: await self.member.send("You've been verified. Welcome to The Gayming Café!!")
        except discord.errors.Forbidden: 
            if welcomeChannel is None: return
            await bot.get_channel(welcomeChannel).send(content= f"{self.member.mention}, you've been verified. Welcome to The Gayming Café!!") 

    async def ageDeny(self):
        try: await self.guild.kick(user= self.member, reason= "Autokick - Outside age range")
        except discord.errors.Forbidden: return
        try: await self.member.send(f"Sorry, you are not in the age range for {self.guild.name}. If you chose wrong age role accidentally, feel free to join again.")
        except discord.errors.Forbidden: pass
        try: await self.logAction(f"Autokicked {self.member.mention} - Outside age range")
        except AttributeError: pass

    async def verifyInfo(self):
        roleChannel = fetch_setting(self.guild.id, 'role_channel')
        await self.message.reply(f"To get verified, you must have at least one pronoun role and an age role{f', from <#{roleChannel}>' if roleChannel is not None else ''}. If you don't feel comfortable sharing your age or have other difficulties, feel free to DM a mod and they'll help you out!", mention_author= False)

    async def checkVerifyStatus(self):
        unverifiedRole = fetch_setting(self.guild.id, 'unverified_role')
        verifiedRole =  fetch_setting(self.guild.id, 'verified_role')
        if unverifiedRole is None or verifiedRole is None: return
        try:
            if unverifiedRole in [role.id for role in self.member.roles]:
                if self.isTooOld():
                    await self.ageDeny()
                elif self.isTooYoung():
                    await self.ageDeny()
                elif self.hasPronounRole() and self.hasAgeRole():
                    await self.verify()
                elif self.message != None and ("verify" in self.message.content or "verified" in self.message.content or "help" in self.message.content):
                    await self.verifyInfo()
        except Exception as e:
            if self.message == None:
                traceback.print_exc()
                return
            error = traceback.format_exc()
            error = error.replace("c:\\Users\\31415\\Dropbox\\AmesBot", "bot")
            error += f"\nVars:\nMessage: {self.message.content}"
            await self.message.reply(content= f"An error occured. If you're seeing this it means <@243759220057571328> is a big dummy. If you can reproduce this message DM reproduction steps to <@243759220057571328>", mention_author= False) 
            smay = await bot.fetch_user(243759220057571328)
            await smay.send(f"An error occured.\nMessage link: https://discord.com/channels/{self.message.guild.id}/{self.message.channel.id}/{self.message.id}\n```{error}```")
            traceback.print_exc()
            return

    async def logAction(self, action):
        channel_id = fetch_setting(self.guild.id, 'log_channel')
        if channel_id is None: return
        channel = self.guild.get_channel(channel_id)
        embed = discord.Embed(title= 'Automatic action taken', description= action)
        await channel.send(embed= embed)

    def hasAgeRole(self):
        ageRoleList = fetch_setting(self.guild.id, 'age_role_list')
        for roleID in ageRoleList:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def hasPronounRole(self):
        pronounRoleList = fetch_setting(self.guild.id, 'pronoun_role_list')
        for roleID in pronounRoleList:
            if roleID in [role.id for role in self.member.roles]:
                return True
        return False

    def isTooYoung(self):
        tooYoungRole = fetch_setting(self.guild.id, 'too_young_role')
        if tooYoungRole in [role.id for role in self.member.roles]:
            return True
        return False

    def isTooOld(self):
        tooOldRole = fetch_setting(self.guild.id, 'too_old_role')
        if tooOldRole in [role.id for role in self.member.roles]:
            return True
        return False

    
