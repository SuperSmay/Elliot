#Bot
import discord
import botGifs
import random

TOKEN = "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"

client = discord.Client()

prefix = "eli"

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
    messageList = message.content.lower().split()
    if len(messageList) >= 3:
      await message.channel.send(f"{message.author.name} is hugging {messageList[2]} {randoHug()}")
    else:
      await message.channel.send(f"{message.author.name} wants a hug... {randoSelfHug()}")



def randoHug():
  return random.choice(botGifs.hugGif)

def randoSelfHug():
  return random.choice(botGifs.selfHugGif)

#<@1234567890>


client.run(TOKEN)