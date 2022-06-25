import asyncio
from email import message
import logging
import traceback

import discord
from discord.ext import commands

from GlobalVariables import bot, on_log
from Settings import fetch_setting
from Statistics import log_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addFilter(on_log)

class Verify(commands.Cog):

    def __init__(self):
        ...

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if fetch_setting(payload.guild_id, 'verification_system') and fetch_setting(payload.guild_id, 'unverified_role') in [role.id for role in payload.member.roles]:
            await asyncio.sleep(1)  # Chill to let reaction role bots do their thing
            member = await payload.member.guild.fetch_member(payload.member.id)
            await self.check_verify_status(member)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.private:
            return
        if not hasattr(message.author, 'roles'):
            logger.warn('Member has no roles attr')
            logger.info(message.jump_url)
        if fetch_setting(message.guild.id, 'verification_system') and fetch_setting(message.guild.id, 'unverified_role') in [role.id for role in message.author.roles]:
            await self.check_verify_status(message.author, message)

    async def verify(self, member, message=None):
        unverified_role = fetch_setting(member.guild.id, 'unverified_role')
        verified_role = fetch_setting(member.guild.id, 'verified_role')
        welcome_channel = fetch_setting(member.guild.id, 'welcome_channel')
        try:
            await member.remove_roles(member.guild.get_role(unverified_role), reason= 'Autoverify')
            await member.add_roles(member.guild.get_role(verified_role))
        except discord.errors.Forbidden:
            logger.warn('Role permissions missing')
            if message is None: 
                welcome_channel.send('I do not have role edit permission for verification!')
            else:
                await message.reply('I do not have role edit permission for verification!', mention_author=False)
            return
        logger.info(f'Verified user {member} on guild {member.guild.name}')
        log_event('user_verified', modes=['global', 'guild'], id=member.guild.id)
        try: await self.log_action(message, f"Autoverified {member.mention}")
        except AttributeError: pass  # I don't even know it just doesn't work sometimes
        try: await member.send("You've been verified. Welcome to The Gayming Café!!")
        except discord.errors.Forbidden: 
            if welcome_channel is None: return
            await bot.get_channel(welcome_channel).send(content= f"{member.mention}, you've been verified. Welcome to The Gayming Café!!") 

    async def age_deny(self, member):
        try: await member.guild.kick(user= member, reason= "Autokick - Outside age range")
        except discord.errors.Forbidden: return
        try: await member.send(f"Sorry, you are not in the age range for {member.guild.name}. If you chose wrong age role accidentally, feel free to join again.")
        except discord.errors.Forbidden: pass
        try: await self.log_action(f"Autokicked {member.mention} - Outside age range", member)
        except AttributeError: pass

    async def verify_info(self, message):
        role_channel = fetch_setting(message.guild.id, 'role_channel')
        await message.reply(f"To get verified, you must have at least one pronoun role and an age role{f', from <#{role_channel}>' if role_channel is not None else ''}. If you don't feel comfortable sharing your age or have other difficulties, feel free to DM a mod and they'll help you out!", mention_author= False)

    async def check_verify_status(self, member: discord.Member, message: discord.Message=None):
        unverified_role = fetch_setting(member.guild.id, 'unverified_role')
        verified_role =  fetch_setting(member.guild.id, 'verified_role')
        if unverified_role is None or verified_role is None: return
        try:
            if unverified_role in [role.id for role in member.roles]:
                if self.is_too_old(member):
                    await self.age_deny(member)
                elif self.is_too_young(member):
                    await self.age_deny(member)
                elif self.has_pronoun_role(member) and self.has_age_role(member):
                    await self.verify(member, message)
                elif message != None and ("verify" in message.content or "verified" in message.content or "help" in message.content):
                    await self.verify_info(message)
        except Exception as e:
            logger.error('Verification check failed', exc_info=True)
            if message != None:
                await message.reply(content="A verification error has occurred.")

    async def log_action(self, member, action):
        channel_id = fetch_setting(member.guild.id, 'log_channel')
        if channel_id is None: return
        channel = member.guild.get_channel(channel_id)
        embed = discord.Embed(title= 'Automatic action taken', description= action)
        await channel.send(embed= embed)

    def has_age_role(self, member):
        age_role_list = fetch_setting(member.guild.id, 'age_role_list')
        for role_id in age_role_list:
            if role_id in [role.id for role in member.roles]:
                return True
        return False

    def has_pronoun_role(self, member):
        pronoun_role_list = fetch_setting(member.guild.id, 'pronoun_role_list')
        for role_id in pronoun_role_list:
            if role_id in [role.id for role in member.roles]:
                return True
        return False

    def is_too_young(self, member):
        too_young_role = fetch_setting(member.guild.id, 'too_young_role')
        if too_young_role in [role.id for role in member.roles]:
            return True
        return False

    def is_too_old(self, member):
        too_old_role = fetch_setting(member.guild.id, 'too_old_role')
        if too_old_role in [role.id for role in member.roles]:
            return True
        return False

    
