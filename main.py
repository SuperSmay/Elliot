#Bot
import datetime
import logging
import pathlib
from time import sleep

import discord
from discord.commands import Option, OptionChoice

import BotInfo
import Help
import BumpReminder
import Groovy
import ImageScan
import Interaction
import Join
import Leaderboard
import Settings
import Verify
from Settings import fetch_setting
from Statistics import log_event
from GlobalVariables import bot, last_start_time, on_log

logging.basicConfig()
logging.root.addFilter(on_log)

use_dev_mode = pathlib.Path.exists(pathlib.Path('use-dev-mode')) and open(pathlib.Path('use-dev-mode'), 'r').read().lower() == 'true'

tokenFile = open(pathlib.Path('token'), 'r') if not use_dev_mode else open(pathlib.Path('token-dev'), 'r')
TOKEN = tokenFile.read()

@bot.event
async def on_ready():
  global last_start_time
  print("I love coffee")
  log_event('startup')
  last_start_time = datetime.datetime.utcnow()
  async for guild in bot.fetch_guilds(limit=150):
    print(guild.name)
  
@bot.event
async def on_message(message: discord.Message):
  if message.author.id == bot.user.id: 
    if hasattr(message.guild, 'id'):  # Ephemeral things
      log_event('message_send', modes=['global', 'guild'], id=message.guild.id)
  if message.author.bot: return
  if str(bot.user.id) in message.content:
    await message.add_reaction("<a:ping:866475995317534740>")

  await bot.process_commands(message)




@bot.event
async def on_message_edit(oldMessage, newMessage: discord.Message):
  if newMessage.author.bot: return
  if oldMessage.content == newMessage.content: return
  print("ON MESSAGE EDIT")
  await bot.process_commands(newMessage)

@bot.slash_command(name="cutie", description="you are a cutie")
async def cutie(ctx):
  log_event('slash_command', ctx=ctx)
  log_event('cutie_command', ctx=ctx)
  await ctx.respond(embed=discord.Embed(description="ur a cutie 2 ;3"))

@bot.command(name="cutie", description="you are a cutie")
async def cutie(ctx):
  log_event('prefix_command', ctx=ctx)
  log_event('cutie_command', ctx=ctx)
  await ctx.reply(embed=discord.Embed(description="ur a cutie 2 ;3"), mention_author=False)

    

@bot.event
async def on_member_join(user):
  scan = ImageScan.MemberScanner(user)
  await scan.scanMember()

bot.add_cog(Interaction.Interaction())
bot.add_cog(BumpReminder.BumpReminder())
bot.add_cog(BotInfo.BotInfo())
bot.add_cog(Groovy.Groovy())
bot.add_cog(Settings.Settings())
bot.add_cog(Leaderboard.Leaderboard())
bot.add_cog(Join.Join())
bot.add_cog(Verify.Verify())
bot.add_cog(Help.Help())

try:
    bot.loop.run_until_complete(bot.start(token=TOKEN))
except KeyboardInterrupt:
    for cog in list(bot.cogs.keys()).copy():
      bot.remove_cog(cog)
    bot.loop.run_until_complete(bot.close())
    
    # cancel all tasks lingering
finally:
    bot.loop.close()
    sleep(1)
    print("Closing up, have a nice day!")
