#Bot
import pathlib
from time import sleep
import discord
from discord.commands import Option
from discord.commands import OptionChoice
from globalVariables import bot, unverifiedRole, joinChannel
import globalFiles
import Interaction
import datetime
from pathlib import Path
import Leaderboard
import Verify
import Join
import asyncio
import ImageScan
import BumpReminder
import Groovy
import CommandInterpreter

use_dev_mode = pathlib.Path.exists(Path('use-dev-mode')) and open(Path('use-dev-mode'), 'r').read().lower() == 'true'

tokenFile = open(Path('token'), 'r') if not use_dev_mode else open(Path('token-dev'), 'r')
TOKEN = tokenFile.read()

@bot.event
async def on_ready():
  print("I love coffee")
  
  async for guild in bot.fetch_guilds(limit=150):
    print(guild.name)
    bot.loop.create_task(BumpReminder.backgroundReminderRestarter(guild))
  print("Starting VC Loop...")
  bot.loop.create_task(Groovy.CheckLoop.loop())
  print("Starting File Save Loop...")
  bot.loop.create_task(globalFiles.saveLoop())
  
@bot.event
async def on_message(message: discord.Message):
  if message.author.bot: return
  if message.guild.id in unverifiedRole.keys() and unverifiedRole[message.guild.id] in [role.id for role in message.author.roles]:
    verify = Verify.Verify(member= message.author, message= message)
    await verify.checkVerifyStatus()

  if str(bot.user.id) in message.content:
    await message.add_reaction("<a:ping:866475995317534740>")

  if (message.content.lower().startswith('scoot.boot()')):
    embeds = await CommandInterpreter.joinCommand(await bot.get_context(message))
    for embed in embeds:
      await message.reply(embed=embed, mention_author= False)

  if(message.content.lower() == 'save' and message.author.id == 243759220057571328):  #Jank af keyboard inturrupt ""fix""
    globalFiles.save()

  await bot.process_commands(message)

@bot.event
async def on_message_edit(oldMessage, newMessage: discord.Message):
  if newMessage.author.bot: return
  await bot.process_commands(newMessage)

@bot.slash_command(name="cutie", description="you are a cutie")
async def cutie(ctx):
  await ctx.respond(embed=discord.Embed(description="ur a cutie 2 ;3"))

@bot.command(name="cutie", description="you are a cutie")
async def cutie(ctx):
  await ctx.reply(embed=discord.Embed(description="ur a cutie 2 ;3"), mention_author=False)

@bot.slash_command(name="hug", description="Hugs a user!")
async def hug(ctx, user:Option(discord.Member, description='User to hug', required=False), message:Option(str, description='Message to include', required=False)):
  args = []
  if user != None: args.append(user.mention)
  if message != None: args += message.split(' ')
  interaction = Interaction.HugInteraction(ctx, args, "hug")
  for embed in await interaction.run():
    await ctx.respond(embed=embed)

@bot.command(name="hug", description="Hugs a user!")
async def hug(ctx, *args):
  interaction = Interaction.HugInteraction(ctx, list(args), "hug")
  for embed in await interaction.run():
    await ctx.reply(embed=embed, mention_author=False)

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

@bot.slash_command(name="play", description="Plays a song/playlist from Youtube/Spotify")
async def play(ctx, input:Option(str, description='A link or search term', required=False, default='')):
  await ctx.defer()
  embeds = await CommandInterpreter.playCommand(ctx, input)
  for embed in embeds:
    await ctx.respond(embed=embed)

@bot.command(name="play", aliases=['p'], description="Plays a song/playlist from Youtube/Spotify")
async def play(ctx, input = '', *moreWords):
  input = input + ' ' + ' '.join(moreWords).strip()
  embeds = await CommandInterpreter.playCommand(ctx, input)
  for embed in embeds:
    await ctx.reply(embed=embed, mention_author= False)

@bot.slash_command(name="add", description="Adds a song/playlist to the queue from Youtube/Spotify")
async def add(ctx, input:Option(str, description='A link or search term', required=False, default='')):
  await ctx.defer()
  embeds = await CommandInterpreter.addCommand(ctx, input)
  for embed in embeds:
    await ctx.respond(embed=embed)

@bot.command(name="add", aliases=['a'], description="Adds a song/playlist to the queue from Youtube/Spotify")
async def add(ctx, input = '', *moreWords):
  input = input + ' ' + ' '.join(moreWords).strip()
  embeds = await CommandInterpreter.addCommand(ctx, input)
  for embed in embeds:
    await ctx.reply(embed=embed, mention_author= False)

@bot.slash_command(name="playlist", description="Shows the current playlist")
async def playlist(ctx):
  await ctx.defer()
  playlist = Groovy.Playlist(ctx)
  await ctx.respond(playlist.run())

@bot.command(name="playlist", aliases=['pl'], description="Shows the current playlist")
async def playlist(ctx):
  playlist = Groovy.Playlist(ctx)
  await ctx.reply(playlist.run(),  mention_author=False)

@bot.slash_command(name="skip", description="Skips the song")
async def skip(ctx):
  await ctx.defer()
  command = Groovy.Skip(ctx)
  await ctx.respond(embed=await command.skip())

@bot.command(name="skip", aliases=['s'], description="Skips the song")
async def skip(ctx):
  command = Groovy.Skip(ctx)
  await ctx.reply(embed=await command.skip(), mention_author=False)

@bot.slash_command(name="pause", description="Pause/Unpause the music")
async def pause(ctx):
  command = Groovy.Pause(ctx)
  await ctx.respond(embed=await command.pause())

@bot.command(name="pause", description="Pause/Unpause the music")
async def pause(ctx):
  command = Groovy.Pause(ctx)
  await ctx.reply(embed=await command.pause(), mention_author=False)

@bot.slash_command(name='disconnect', description="Leave the vc")
async def disconnect(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.disconnect(ctx)

@bot.command(aliases=['dc'], description="Leave the vc")
async def disconnect(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.disconnect(ctx)

@bot.slash_command(name="nowplaying", description="Show the now playing song")
async def np(ctx):
  await ctx.defer()
  np = Groovy.NowPlaying(ctx)
  await ctx.respond(embed=np.getNowPlayingEmbed())

@bot.command(name="nowplaying", aliases=['np'], description="Show the now playing song")
async def np(ctx):
  np = Groovy.NowPlaying(ctx)
  await ctx.reply(embed=np.getNowPlayingEmbed(), mention_author=False)

@bot.slash_command(name="shuffle", description="Toggle shuffle mode")
async def shuffle(ctx):
  await ctx.defer()
  command = Groovy.Shuffle(ctx)
  await ctx.respond(embed=await command.shuffle())

@bot.command(name="shuffle", aliases=['sh'], description="Toggle shuffle mode")
async def shuffle(ctx):
  command = Groovy.Shuffle(ctx)
  await ctx.reply(embed=await command.shuffle(), mention_author=False)

@bot.slash_command(name="search", description="Search youtube for something to play")
async def play(ctx, input:Option(str, description='Search term', required=True)):
  await ctx.defer()
  embeds = await CommandInterpreter.searchCommand(ctx, input)
  for embed in embeds:
    await ctx.respond(embed=embed)

@bot.command(name="search", description="Search youtube for something to play")
async def play(ctx, input = '', *moreWords):
  input = (input + ' ' + ' '.join(moreWords)).strip()
  embeds = await CommandInterpreter.searchCommand(ctx, input)
  for embed in embeds:
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

# @bot.event
# async def on_raw_reaction_add(payload):  #When reaction added
#   try:
#     emoji = payload.emoji  #Get emoji from the reaction payload
#     channel = await bot.fetch_channel(payload.channel_id)  #Get channel from the reaction payload
#     message = await channel.fetch_message(payload.message_id)  #Get message from the reaction payload
#     user = await bot.fetch_user(payload.user_id)  #Get user from the reaction payload
#     if message.id in activeMessages.keys():
#       await activeMessages[message.id].onReact(emoji, user)
#   except:
#     traceback.print_exc()
#     print(emoji, "Channel:", payload.channel_id, "Message:", payload.message_id)

try:
    bot.loop.run_until_complete(bot.start(token=TOKEN))
except KeyboardInterrupt:
    bot.loop.run_until_complete(bot.close())
    globalFiles.save()
    
    # cancel all tasks lingering
finally:
    bot.loop.close()
    sleep(1)
    print("Closing up, have a nice day!")