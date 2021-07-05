#Bot
import discord
import botGifs
import random
from globalVariables import client, prefix
import Interaction

TOKEN =   "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"





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




def randoHug():
  return random.choice(botGifs.hugGif)

def randoSelfHug():
  return random.choice(botGifs.selfHugGif)

async def hugEmbed(message):
  messageList = message.content.lower().split()
  user2Name = await client.fetch_user(messageList[2].replace("<", "").replace(">", "").replace("@", "").replace("!", ""))
  embed= discord.Embed(title=f"{message.author.name} is hugging {user2Name.name}", color=embColors())
  embed.set_image(url=randoHug())
  return embed

def selfHugEmbed(message):
  embed= discord.Embed(title=f"{message.author.name} wants a hug...", color=embColors())
  embed.set_image(url=randoHug())
  return embed

def embColors():
  return random.choice(botGifs.colors)




















#<@1234567890>


client.run(TOKEN)