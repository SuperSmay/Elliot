import discord
from pathlib import Path

tokenFile = open(Path('token'), 'r')
TOKEN = tokenFile.read()

bot = discord.Bot()

@bot.event
async def on_message(message: discord.Message):
    if (message.guild == None):
        if ('14' in message.content or '15' in message.content or '16' in message.content or '17' in message.content or '18' in message.content or '19' in message.content or '20' in message.content):
            print('In age range')
        else:
            print('Not in age range')


bot.run(token=TOKEN)