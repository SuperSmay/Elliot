#Bot
import discord
import botGifs
import random
from globalVariables import client, prefix
import Interaction
import datetime
import Leaderboard

TOKEN = "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"
## Uno2 - "NzM2NDE4MDkwNjI3MjM1OTUx.Xxugyg.dBM5qCUAdp3F4ALd7dvqdRh7mHQ"




@client.event
async def on_ready():
  print("I love coffee")
  
  async for guild in client.fetch_guilds(limit=150):
    print(guild.name)

@client.event
async def on_message(message):
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

@client.event
async def on_member_remove(user):
  timeSinceJoin = datetime.datetime.utcnow() - user.joined_at
  if timeSinceJoin.days == 0 and timeSinceJoin.seconds <= 360:
    leaderboard = Leaderboard.timeLeaderboard(timeSinceJoin, user)
    await leaderboard.scoreSubmit()



client.run(TOKEN)