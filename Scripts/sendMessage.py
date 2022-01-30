import discord
from pathlib import Path

tokenFile = open(Path('token'), 'r')
TOKEN = tokenFile.read()

bot = discord.Bot()

@bot.event
async def on_message(message: discord.Message):
    if (message.author.id == 243759220057571328 and message.content.startswith('elisay')):
        await message.delete()
        await message.channel.send(message.content.removeprefix('elisay'))


bot.run(token=TOKEN)