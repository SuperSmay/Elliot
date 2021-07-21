#Bot
from operator import invert
import discord
from globalVariables import client, prefix, verifyChannel, unverifiedRole
from activeMessages import activeMessages
import Interaction
import datetime
import Leaderboard
import Verify
import Join
import Shop

TOKEN = "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"
## Uno2 - "NzM2NDE4MDkwNjI3MjM1OTUx.Xxugyg.dBM5qCUAdp3F4ALd7dvqdRh7mHQ"



@client.event
async def on_ready():
  print("I love coffee")
  
  async for guild in client.fetch_guilds(limit=150):
    print(guild.name)

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
    interaction = Leaderboard.FetchLeaderboard(message)
    await interaction.send()
  elif message.content.lower().startswith(prefix + " shop"):
    shop = Shop.Shop(message)
    await shop.send()
  elif message.content.lower().startswith(prefix + " inv"):
    inventory = Shop.Inventory(message)
    await inventory.send()
  elif message.content.lower().startswith(prefix + " bal"):
    balance = Shop.Balance(message)
    await balance.send()


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
    leaderboard = Leaderboard.timeLeaderboard(timeSinceJoin, user)
    await leaderboard.scoreSubmit()

@client.event
async def on_member_join(user):
  join = Join.Join(user)
  await join.send()

@client.event
async def on_raw_reaction_add(payload):  #When reaction added
    emoji = payload.emoji  #Get emoji from the reaction payload
    channel = await client.fetch_channel(payload.channel_id)  #Get channel from the reaction payload
    message = await channel.fetch_message(payload.message_id)  #Get message from the reaction payload
    user = await client.fetch_user(payload.user_id)  #Get user from the reaction payload
    if message.id in activeMessages.keys():
      await activeMessages[message.id].onReact(emoji, user)

    

client.run(TOKEN)