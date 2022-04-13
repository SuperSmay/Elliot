#Bot
import asyncio
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
import Verify
from globalVariables import bot, joinChannel, last_start_time, unverifiedRole

logging.basicConfig()

use_dev_mode = pathlib.Path.exists(pathlib.Path('use-dev-mode')) and open(pathlib.Path('use-dev-mode'), 'r').read().lower() == 'true'

tokenFile = open(pathlib.Path('token'), 'r') if not use_dev_mode else open(pathlib.Path('token-dev'), 'r')
TOKEN = tokenFile.read()

@bot.event
async def on_ready():
  global last_start_time
  print("I love coffee")
  last_start_time = datetime.datetime.utcnow()
  async for guild in bot.fetch_guilds(limit=150):
    print(guild.name)
  
@bot.event
async def on_message(message: discord.Message):
  if message.author.bot: return
  if message.guild.id in unverifiedRole.keys() and unverifiedRole[message.guild.id] in [role.id for role in message.author.roles]:
    verify = Verify.Verify(member= message.author, message= message)
    await verify.checkVerifyStatus()

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
  await ctx.respond(embed=discord.Embed(description="ur a cutie 2 ;3"))

@bot.command(name="cutie", description="you are a cutie")
async def cutie(ctx):
  await ctx.reply(embed=discord.Embed(description="ur a cutie 2 ;3"), mention_author=False)

@bot.slash_command(name="leaderboard", description="Shows a leaderboard")
async def leaderboard(ctx, leaderboard:Option(str, description='Leaderboard to show', choices=[OptionChoice('Weekly top leaver time', 'weekly'), OptionChoice('Top 10 leaver times', 'leaver')], required=False, default='leaver')):
  if leaderboard == 'weekly':
    interaction = Leaderboard.weeklyTimeLeaderboard(ctx.author)
  elif leaderboard == 'leaver':
    interaction = Leaderboard.timeLeaderboard(ctx.author)
  embed = await interaction.getLeaderboardEmbed()
  await ctx.respond(embed=embed)

@bot.command(name="leaderboard", aliases=['leaverboard'], description="Shows a leaderboard")
async def leaderboard(ctx, leaderboard='leaver'):
  if leaderboard == 'weekly':
    interaction = Leaderboard.weeklyTimeLeaderboard(ctx.author)
  elif leaderboard == 'leaver':
    interaction = Leaderboard.timeLeaderboard(ctx.author)
  embed = await interaction.getLeaderboardEmbed()
  await ctx.reply(embed=embed, mention_author= False)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
  if payload.guild_id in unverifiedRole.keys() and unverifiedRole[payload.guild_id] in [role.id for role in payload.member.roles]:
    await asyncio.sleep(1)
    verify = Verify.Verify(member= await payload.member.guild.fetch_member(payload.member.id))
    await verify.checkVerifyStatus()


@bot.event
async def on_member_remove(user):
  leave = Join.Leave(user)
  await leave.send()
  timeSinceJoin = datetime.datetime.now(datetime.timezone.utc) - user.joined_at
  if timeSinceJoin.days == 0 and timeSinceJoin.seconds <= 360:
    leaderboard = Leaderboard.timeLeaderboard(user)
    leaderboard.setUserScore(round(timeSinceJoin.seconds + timeSinceJoin.microseconds/1000000, 2))
    leaderboard.setScoreOnLeaderboard()
    leaderboard.saveLeaderboard()
    if leaderboard.indexToAnnounce < 10 and leaderboard.annouce:
      channel = await bot.fetch_channel(joinChannel[user.guild.id])
      await channel.send(leaderboard.positionAnnoucenment())
    
    weeklyLeaderboard = Leaderboard.weeklyTimeLeaderboard(user)
    weeklyLeaderboard.setUserScore(round(timeSinceJoin.seconds + timeSinceJoin.microseconds/1000000, 2))
    weeklyLeaderboard.setScoreOnLeaderboard()
    weeklyLeaderboard.saveLeaderboard()
    if weeklyLeaderboard.indexToAnnounce < 1 and weeklyLeaderboard.annouce:
      channel = await bot.fetch_channel(joinChannel[user.guild.id])
      await channel.send(weeklyLeaderboard.positionAnnoucenment())
    

@bot.event
async def on_member_join(user):
  join = Join.Join(user)
  await join.send()
  scan = ImageScan.MemberScanner(user)
  await scan.scanMember()

bot.remove_command("help")

bot.add_cog(Interaction.Interaction())
bot.add_cog(BumpReminder.BumpReminder())
bot.add_cog(BotInfo.BotInfo())
bot.add_cog(Groovy.Groovy())
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
