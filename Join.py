import datetime
import logging
import random
from Settings import fetch_setting
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Join(commands.Cog, name='Join'):
  
    @commands.Cog.listener()
    async def on_member_remove(self, user):
        leave = LeaveMessager(user)
        await leave.send()
            

    @commands.Cog.listener()
    async def on_member_join(self, user):
        join = JoinMessager(user)
        await join.send()



class JoinMessager(commands.Cog, name='Join'):
    def __init__(self, member):
        self.member: discord.Member = member
        self.guild = member.guild

    async def get_message(self):
        cafe_join_message_list = [
            f"Welcome to {self.guild.name}, <@{self.member.id}>!!",
            f":0 Hello there <@{self.member.id}>, welcome to {self.guild.name}!",
            f"{self.guild.name} has a new customer! Welcome, <@{self.member.id}>!",
            f"🔔 \*Ding ding\* 🔔 <@{self.member.id}> just entered {self.guild.name}!",
            f"Hi <@{self.member.id}>, we hope you enjoy your time here at {self.guild.name}!"
        ]
        cafe_rp_message_list = [
            f"Seat yourself anywhere you'd like!",
            f"There are some free tables to the left if you'd like to sit down!",
            f"Feel free to sit down anywhere you like!",
            f"There are drinks up front and free tables in the back!"
        ]
        return f"<:join:868675783026180097> {random.choice(cafe_join_message_list)} {random.choice(cafe_rp_message_list)}"


    def get_member_count(self):
        memberCount = 0
        bot_role_id = fetch_setting(self.guild.id, 'bot_role')
        for member in self.guild.members:
            if not bot_role_id in [role.id for role in member.roles]:
                memberCount += 1
        return memberCount


    async def send(self):
        #if self.member.id == 812156805244911647: return  #Ignore alt
        channel_id = fetch_setting(self.guild.id, 'welcome_channel')
        if channel_id is None: return
        try: channel = self.guild.get_channel(channel_id)
        except Exception as e: 
            logger.warn('Failed to get channel for join message', exc_info=e)
            return
        await channel.send(f"{await self.get_message()}")
        await channel.send(f"`There are now {self.get_member_count()} customers here at {self.guild.name}.`")
        await self.log()
        logger.info('Join/Leave message sent')

    async def log(self):
        channel_id = fetch_setting(self.guild.id, 'log_channel')
        if channel_id is None: return
        channel = self.guild.get_channel(channel_id)
        embed = discord.Embed(title= "Member joined", description= f"User is {self.member.mention}", color= 15672122)
        embed.set_author(name= self.member.display_name, url= self.member.avatar.url if hasattr(self.member.avatar, 'url') else 'https://cdn.discordapp.com/embed/avatars/1.png')
        embed.set_footer(text= f"ID: {self.member.id}")
        embed.set_thumbnail(url= self.member.avatar.url if hasattr(self.member.avatar, 'url') else 'https://cdn.discordapp.com/embed/avatars/1.png')
        await channel.send(embed= embed)
class LeaveMessager(JoinMessager):

    async def get_message(self):
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
        try:
            ban_list = [ban.user for ban in await self.member.guild.bans().flatten()]
            if self.member in ban_list:
                return True
        except discord.Forbidden:
            logger.info(f'Missing access to guild bans for {self.member.guild.name}')
        return False

    async def log(self):
        channel_id = fetch_setting(self.guild.id, 'log_channel')
        if channel_id is None: return
        channel = self.guild.get_channel(channel_id)
        embed = discord.Embed(title= "Member leave", description= f"User is {self.member.mention}", color= 15672122)
        embed.set_author(name= self.member.display_name, url= self.member.avatar.url if hasattr(self.member.avatar, 'url') else 'https://cdn.discordapp.com/embed/avatars/1.png')
        embed.set_footer(text= f"ID: {self.member.id}")
        embed.set_thumbnail(url= self.member.avatar.url if hasattr(self.member.avatar, 'url') else 'https://cdn.discordapp.com/embed/avatars/1.png')
        await channel.send(embed= embed)
