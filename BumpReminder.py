import asyncio
import datetime
import traceback
import discord

from discord.ext import commands, tasks

from globalVariables import bot
from Settings import fetch_setting


class BumpReminder(commands.Cog, name='Bump Reminder'):

    def __init__(self):
        self.bump_reminder_tasks = {}
        self.bump_reminder_starter.start()

    #Run on bot startup
    async def bump_task_start(self, guild):

        #Find last "bump success" message
        def bump_message_check(message):
            return (message.author.id == 302050872383242240 and hasattr(message, 'embeds') and "Bump done!" in message.embeds[0].description)

        def bump_remind_check(message):
            return (message.author.id == bot.user.id and hasattr(message, 'embeds') and "Bump the server" in message.embeds[0].description)

        bump_message = await self.get_message(guild, bump_message_check)

        if bump_message == None:
            print("Bump message was empty, reminding now")
            bot.loop.create_task(self.bump_reminder_task(0, guild.id))
            return

        time_since_bump = datetime.datetime.now(datetime.timezone.utc) - bump_message.created_at
        print(f"Time since bump is {time_since_bump}")

        time_until_bump = datetime.timedelta(hours= 2) - time_since_bump

        bump_remind_message = await self.get_message(guild, bump_remind_check)

        if bump_remind_message is None:
            time_since_bump_remind = -1
        else:
            time_since_bump_remind = datetime.datetime.now(datetime.timezone.utc) - bump_remind_message.created_at

        if bump_remind_message != None and (bump_remind_message.created_at - bump_message.created_at).total_seconds() > 0 and not time_since_bump_remind.total_seconds() > 7200: 
            print(f"Cancelling remind task and waiting because reminder was sent after last bump success and within two hours")
            self.bump_reminder_tasks[guild.id] = False
            return

        #Start async task waiting for time until next bump
        bot.loop.create_task(self.bump_reminder_task(time_until_bump.total_seconds(), guild.id))
        self.bump_reminder_tasks[guild.id] = True


    async def get_message(self, guild, search):

        #Get channel
        channel = await bot.fetch_channel(fetch_setting(guild.id, 'bump_channel'))

        message = await channel.history(limit=50).find(search)
        
        if message == None:
            message = await channel.history(limit=150).find(search)

        if message == None:
            message = await channel.history(limit=1500).find(search)

        if message == None:
            print(f'Could not find bump message within 1500 messages for {guild.name}/{channel.name}')

        return message

    #Make bump message
    def get_reminder_embed(self):
        embed = discord.Embed(title= "⋅•⋅⊰∙∘☽ Its bump time! ☾∘∙⊱⋅•⋅", description= "Bump the server with `/bump`!", color= 7528669)
        embed.set_thumbnail(url=bot.user.avatar.url)
        return embed

    #Async tasks
    async def bump_reminder_task(self, waitTime, guild_id):
        if waitTime < 0: waitTime = 0
        await asyncio.sleep(waitTime)  #Sleep for waitTime seconds
        #...zzz...
        bump_channel_id = fetch_setting(guild_id, 'bump_channel')
        bump_role_id = fetch_setting(guild_id, 'bump_role')
        channel = await bot.fetch_channel(bump_channel_id)  #Get channel
        await channel.send(embed= self.get_reminder_embed(), content= f"<@&{bump_role_id}>" if bump_role_id is not None else '')  #Send reminder
        self.bump_reminder_tasks[guild_id] = False  #Set task running to False

    @tasks.loop(minutes=15)
    async def bump_reminder_starter(self):
        # print("Attempting reminder task start...")
        try:
            async for guild in bot.fetch_guilds():
                if fetch_setting(guild.id, 'bump_channel') is None: continue
                if guild.id not in self.bump_reminder_tasks.keys(): self.bump_reminder_tasks[guild.id] = False
                if not self.bump_reminder_tasks[guild.id]:
                    try:
                        await self.bump_task_start(guild)  #Start new task
                        print(f"Bump reminder task started for guild {guild.name}")
                    except discord.errors.Forbidden:
                        pass
                    except Exception as e:
                        print(f'Reminder task failed to start for {guild.name}.\n{e}')  #If something goes wrong, just wait and try restarting again later
        except Exception as e:
            print(f'Reminder task starter has failed. Trying again in 15 minutes. {e}')  #If something goes wrong, just wait and try restarting again later
            traceback.print_exc()

    @bump_reminder_starter.before_loop
    async def before_bump(self):
        print('Starting bump loop...')
        await bot.wait_until_ready()
