#Bot
from re import M
import discord
from globalVariables import client, prefix, verifyChannel, unverifiedRole, joinChannel, musicPlayers
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

TOKEN = "ODg4OTY0ODM2NzE1ODE5MDA5.YUaXBQ.mD8g16yaJmWpjxl0NowGQCun_a0"
## Uno2 - "NzM2NDE4MDkwNjI3MjM1OTUx.Xxugyg.dBM5qCUAdp3F4ALd7dvqdRh7mHQ"
## Elliot - "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"
## Speakers - "ODg4OTY0ODM2NzE1ODE5MDA5.YUaXBQ.mD8g16yaJmWpjxl0NowGQCun_a0"



@client.event
async def on_ready():
  print("I love coffee")
  
  async for guild in client.fetch_guilds(limit=150):
    print(guild.name)
    client.loop.create_task(BumpReminder.backgroundReminderRestarter(guild))
  print("Starting VC loop")
  client.loop.create_task(Groovy.CheckLoop.loop())

@client.event
async def on_message(message: discord.Message):
  if message.author.bot:
    return
  if client.user.id != 888964836715819009 and message.channel.guild.id == 866160840037236736:
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
  elif message.content.lower().startswith(prefix + " playlist"):
    playlist = Groovy.Playlist(message)
    await playlist.send()
  elif message.content.lower().startswith(prefix + " play"):
    play = Groovy.Play(message)
    await message.reply(embed=await play.runCommand())
  elif message.content.lower().startswith(prefix + " skip"):
    skip = Groovy.Skip(message)
    await message.reply(embed=await skip.skip())
  elif message.content.lower().startswith(prefix + " pause"):
    pause = Groovy.Pause(message)
    await message.reply(embed=pause.pause())
  elif message.content.lower().startswith(prefix + " dc"):
    await message.channel.guild.voice_client.disconnect()
    del(musicPlayers[message.channel.guild.id])
  elif message.content.lower().startswith(prefix + " np"):
    np = Groovy.NowPlaying(message)
    await message.reply(embed=np.getNowPlayingEmbed())
  elif message.content.lower().startswith(prefix + " shuffle"):
    shuffle = Groovy.Shuffle(message)
    await message.reply(embed=shuffle.shuffle())
  


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