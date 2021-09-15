#Bot
import discord
from discord import embeds
from discord import message
from discord import channel
from globalVariables import client, prefix, verifyChannel, unverifiedRole, joinChannel
from activeMessages import activeMessages
import Interaction
import datetime
import Leaderboard
import Verify
import Join
import Shop
import traceback
import ImageScan
import BumpReminder
import Groovy

TOKEN = "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"
## Uno2 - "NzM2NDE4MDkwNjI3MjM1OTUx.Xxugyg.dBM5qCUAdp3F4ALd7dvqdRh7mHQ"



@client.event
async def on_ready():
  print("I love coffee")
  
  async for guild in client.fetch_guilds(limit=150):
    print(guild.name)
    client.loop.create_task(BumpReminder.backgroundReminderRestarter(guild))

  #channel = await client.fetch_channel(866160840037236739)
  #message = await channel.fetch_message(876938127636316242)
  #vc = await client.fetch_channel(866160840037236740)
  #await Groovy.Music.join(channel.guild, vc)
  #await Groovy.Music.stream(message, "https://www.youtube.com/watch?v=W2TE0DjdNqI")

@client.event
async def on_message(message: discord.Message):
  if message.author.bot:
    return
  elif message.content.lower().startswith(prefix + " cutie"):
    await message.channel.send("ur a cutie 2 ;3")
  elif message.content.lower().startswith(prefix + " hug"):
    interaction = Interaction.HugInteraction(message, "hug")
    await interaction.send()
  elif message.content.lower().startswith(prefix + " test"):
    interaction = Interaction.BaseInteraction(message, "test")
    await interaction.send()
  elif message.content.lower().startswith(prefix + " leaverboard") or message.content.lower().startswith(prefix + " leaderboard"):
    if len(message.content.split(" ")) > 2 and message.content.split(" ")[2].startswith("week"):
      interaction = Leaderboard.weeklyTimeLeaderboard(message.author)
    else:
      interaction = Leaderboard.timeLeaderboard(message.author)
    await message.reply(embed= await interaction.getLeaderboardEmbed(), mention_author= False)
  elif message.content.lower().startswith(prefix + " shop"):
    shop = Shop.Shop(message)
    await shop.send()
  elif message.content.lower().startswith(prefix + " inv"):
    inventory = Shop.InventoryMessage(message)
    await inventory.send()
  elif message.content.lower().startswith(prefix + " bal"):
    balance = Shop.BalanceMessage(message)
    await balance.send()
  elif message.content.lower().startswith(prefix + " play"):
    play = Groovy.Play(message)
    await play.attemptPlay()
  elif message.content.lower().startswith(prefix + " skip"):
    skip = Groovy.Skip(message)
    skip.skip()
    await skip.send()
  elif message.content.lower().startswith(prefix + " playlist"):
    playlist = Groovy.Playlist(message)
    await playlist.send()
  


  elif unverifiedRole[message.guild.id] in [role.id for role in message.author.roles]:
    verify = Verify.Verify(member= message.author, message= message)
    await verify.checkVerifyStatus()

  if str(client.user.id) in message.content.lower():
    await message.add_reaction("<a:ping:866475995317534740>")

  


@client.event
async def on_member_remove(user):
  leave = Join.Leave(user)
  await leave.send()
  timeSinceJoin = datetime.datetime.utcnow() - user.joined_at
  if timeSinceJoin.days == 0 and timeSinceJoin.seconds <= 360:
    leaderboard = Leaderboard.timeLeaderboard(user)
    leaderboard.setUserScore(round(timeSinceJoin.seconds + timeSinceJoin.microseconds/1000000, 2))
    leaderboard.setScoreOnLeaderboard()
    leaderboard.saveLeaderboard()
    if leaderboard.indexToAnnounce < 10 and leaderboard.annouce:
      channel = await client.fetch_channel(joinChannel[user.guild.id])
      await channel.send(leaderboard.positionAnnoucenment())
    
    weeklyLeaderboard = Leaderboard.weeklyTimeLeaderboard(user)
    weeklyLeaderboard.setUserScore(round(timeSinceJoin.seconds + timeSinceJoin.microseconds/1000000, 2))
    weeklyLeaderboard.setScoreOnLeaderboard()
    weeklyLeaderboard.saveLeaderboard()
    if weeklyLeaderboard.indexToAnnounce < 1 and weeklyLeaderboard.annouce:
      channel = await client.fetch_channel(joinChannel[user.guild.id])
      await channel.send(weeklyLeaderboard.positionAnnoucenment())
    

@client.event
async def on_member_join(user):
  join = Join.Join(user)
  await join.send()
  scan = ImageScan.MemberScanner(user)
  await scan.scanMember()

@client.event
async def on_raw_reaction_add(payload):  #When reaction added
  try:
    emoji = payload.emoji  #Get emoji from the reaction payload
    channel = await client.fetch_channel(payload.channel_id)  #Get channel from the reaction payload
    message = await channel.fetch_message(payload.message_id)  #Get message from the reaction payload
    user = await client.fetch_user(payload.user_id)  #Get user from the reaction payload
    if message.id in activeMessages.keys():
      await activeMessages[message.id].onReact(emoji, user)
  except:
    traceback.print_exc()
    print(emoji, "Channel:", payload.channel_id, "Message:", payload.message_id)

    

client.run(TOKEN)