import discord
from pathlib import Path

tokenFile = open(Path('token'), 'r')
TOKEN = tokenFile.read()

bot = discord.Bot()





@bot.event
async def on_message_edit(oldMessage, newMessage: discord.Message):
  if newMessage.author.bot: return
  print("ON MESSAGE EDIT")

bot.run(token=TOKEN)