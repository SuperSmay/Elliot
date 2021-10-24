import asyncio
import datetime
import discord

from globalVariables import bot, bumpChannel, bumpRole

bumpTasksEnabled = True

bumpReminderTasks = {
    811369107181666343 : False
}
#Run on bot startup
async def startBumpReminderTask(guild):

    #Find last "bump success" message
    def bumpMessageCheck(message):
        return (message.author.id == 302050872383242240 and hasattr(message, 'embeds') and "Bump done! :thumbsup:" in message.embeds[0].description)

    def bumpRemindCheck(message):
        return (message.author.id == bot.user.id and hasattr(message, 'embeds') and "Bump the server" in message.embeds[0].description)

    bumpMessage = await getMessage(guild, bumpMessageCheck)
    #print("Bump message found")

    if bumpMessage == None:
        print("Bump message was empty, reminding now")
        bot.loop.create_task(bumpReminderTask(0, guild))
        return

    #Get time since last bump message
    timeSinceBump = datetime.datetime.utcnow() - bumpMessage.created_at
    print(f"Time since bump is {timeSinceBump}")

    #Get time unitl next bump
    timeUntilBump = datetime.timedelta(hours= 2) - timeSinceBump
    #print(f"Time until bump us {timeUntilBump}")

    bumpRemindMessage = await getMessage(guild, bumpRemindCheck)
    #print("Got bump remind message")

    #print(f"bumpRemindMessage.created_at - bumpMessage.created_at ({bumpRemindMessage.created_at} - {bumpMessage.created_at} = {bumpRemindMessage.created_at - bumpMessage.created_at}")

    if bumpRemindMessage != None and (bumpRemindMessage.created_at - bumpMessage.created_at).total_seconds() > 0: 
        print(f"Cancelling remind task and waiting because reminder was sent after last bump success")
        bumpReminderTasks[guild.id] = False
        return

    
    #print("Creating new reminder sender task...")
    #Start async task waiting for time until next bump
    bot.loop.create_task(bumpReminderTask(timeUntilBump.total_seconds(), guild))
    #print("Reminder sender task created")


async def getMessage(guild, search):

    #Get channel
    channel = await bot.fetch_channel(bumpChannel[guild.id])

    message = await channel.history(limit=50).find(search)
    
    if message == None:
        message = await channel.history(limit=150).find(search)

    if message == None:
        message = await channel.history(limit=1500).find(search)

    if message == None:
        message = await channel.history(limit=None).find(search)

    return message

#Make bump message
def getReminderEmbed():
    embed = discord.Embed(title= "⋅•⋅⊰∙∘☽ Its bump time! ☾∘∙⊱⋅•⋅ <:be:876937712135983203><:ta:876937712022745119>", description= "Bump the server with `!d bump`!", color= 7528669)
    embed.set_thumbnail(url=bot.user.avatar.url)
    return embed

#Async tasks
async def bumpReminderTask(waitTime, guild):
    id = guild.id
    #print(f"Bump reminder sender: Sleeping for {waitTime} seconds...")
    await asyncio.sleep(waitTime)
    #print("Bump reminder sender: Waking from sleep")
    #print("Bump reminder sender: Getting channel")
    channel = await bot.fetch_channel(bumpChannel[id])
    #print("Bump reminder sender: Channel got")
    #TEMPUser = await client.fetch_user(243759220057571328)
    #await TEMPUser.send(embed= getReminderEmbed(guild))
    await channel.send(embed= getReminderEmbed(), content= f"<@&{bumpRole[id]}>")
    #print("Bump reminder sender: Sending reminder")
    bumpReminderTasks[id] = False
    #print("Bump reminder sender: task running set to False")

async def backgroundReminderRestarter(guild):
    if guild.id not in bumpReminderTasks.keys(): return
    if guild.id not in bumpChannel.keys(): return
    print(f"Bump reminder task starter started for guild {guild.name}")
    while bumpTasksEnabled == True:
        #print("Attempting reminder task start...")
        if not bumpReminderTasks[guild.id]:
            bumpReminderTasks[guild.id] = True
            await startBumpReminderTask(guild)
            #print('New reminder task started')
        await asyncio.sleep(600)
