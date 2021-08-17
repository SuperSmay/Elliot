import pathlib
import asyncio
import datetime
import discord

from discord import embeds, message
from globalVariables import client, bumpChannel

bumpTasksEnabled = True

bumpReminderTasks = {
    811369107181666343 : False
}
#Run on bot startup
async def startBumpReminderTask(guild):
    #Get channel
    channel = await client.fetch_channel(bumpChannel[guild.id])
    #Find last "bump success" message
    def bumpMessageCheck(message):
        return (message.author.id == 302050872383242240 and "Bump done :thumbsup:" in message.embeds[0].description)

    def predicate(message):
        return (message.author.id == client.user.id and "Bump the server" in message.embeds[0].description)

    bumpMessage = await channel.history(limit=50).find(bumpMessageCheck)

    #Get time since last bump message
    timeSinceBump = datetime.datetime.utcnow() - bumpMessage.created_at

    #Get time unitl next bump
    timeUntilBump = datetime.timedelta(hours= 2) - timeSinceBump

    bumpRemindMessage = await channel.history(limit=50).find(predicate)

    #print(f"bumpRemindMessage.created_at - bumpMessage.created_at ({bumpRemindMessage.created_at} - {bumpMessage.created_at} = {bumpRemindMessage.created_at - bumpMessage.created_at}")

    if (bumpRemindMessage.created_at - bumpMessage.created_at).total_seconds() > 0: 
        bumpReminderTasks[guild.id] = False
        return

    
    
    #Start async task waiting for time until next bump
    client.loop.create_task(bumpReminderTask(timeUntilBump.total_seconds(), guild))


#Make bump message
def getReminderEmbed(guild):
    embed = discord.Embed(title= "⋅•⋅⊰∙∘☽ Its bump time! ☾∘∙⊱⋅•⋅ <:be:876937712135983203><:ta:876937712022745119>", description= "Bump the server with `!d bump`!", color= 7528669)
    embed.set_thumbnail(url=client.user.avatar_url)
    return embed

#Async tasks
async def bumpReminderTask(waitTime, guild):
    channel = await client.fetch_channel(bumpChannel[guild.id])
    TEMPUser = await client.fetch_user(243759220057571328)
    await TEMPUser.send(f"Bump reminder in {waitTime} seconds")
    await TEMPUser.send("Reminder looks like:", embed= getReminderEmbed(guild))
    #await channel.send("Time until bump: " + str(waitTime) + "seconds")
    await asyncio.sleep(waitTime)
    #await channel.send(embed= getReminderEmbed(guild))
    bumpReminderTasks[guild.id] = False

async def backgroundReminderRestarter(guild):
    if guild.id not in bumpReminderTasks.keys(): return
    if guild.id not in bumpChannel.keys(): return
    print(f"Bump reminder task starter started for guild {guild.name}")
    while bumpTasksEnabled == True:
        if not bumpReminderTasks[guild.id]:
            await startBumpReminderTask(guild)
            bumpReminderTasks[guild.id] = True
        await asyncio.sleep(600)
