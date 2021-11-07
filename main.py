#Bot
import discord
from globalVariables import bot, unverifiedRole, joinChannel
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

tokenFile = open(Path('token'), 'r')
TOKEN = tokenFile.read()

commands = [
    discord.ApplicationCommand(
        name="cutie",
        description="youre a cutie"
    ),
    discord.ApplicationCommand(
        name="hug",
        description="Hugs a user!",
        options= 
        [
          discord.ApplicationCommandOption(
            name="user",
            type=discord.ApplicationCommandOptionType.user,
            required=False,
            description='User to hug'
            ),
          discord.ApplicationCommandOption(
            name="message",
            type=discord.ApplicationCommandOptionType.string,
            required=False,
            description='Messsage to include'
            )
        ]
    ),
    discord.ApplicationCommand(
        name="leaderboard",
        description="Shows a leaderboard",
        options= 
        [
          discord.ApplicationCommandOption(
            name="leaderboard",
            type=discord.ApplicationCommandOptionType.string,
            required=True,
            description='Which leaderboard to show',
            )
        ]
    ),
    discord.ApplicationCommand(
        name="play",
        description="Play a song in your voice channel",
        options= 
        [
          discord.ApplicationCommandOption(
            name="input",
            type=discord.ApplicationCommandOptionType.string,
            required=True,
            description='A link or search term'
            )
        ]
    ),
    discord.ApplicationCommand(
        name="search",
        description="Search youtube for something to play",
        options= 
        [
          discord.ApplicationCommandOption(
            name="input",
            type=discord.ApplicationCommandOptionType.string,
            required=True,
            description='A search term'
            )
        ]
    ),
    discord.ApplicationCommand(
        name="add",
        description="Adds a song to the queue",
        options= 
        [
          discord.ApplicationCommandOption(
            name="input",
            type=discord.ApplicationCommandOptionType.string,
            required=True,
            description='A link or search term'
            )
        ]
    ),
    discord.ApplicationCommand(
        name="pause",
        description="Pause the music"
    ),
    discord.ApplicationCommand(
        name="playlist",
        description="Shows the current playlist"
    ),
    discord.ApplicationCommand(
        name="skip",
        description="Skips the song"
    ),
    discord.ApplicationCommand(
        name="disconnect",
        description="Leave the vc"
    ),
    discord.ApplicationCommand(
        name="nowplaying",
        description="Show the now playing song"
    ),
    discord.ApplicationCommand(
        name="shuffle",
        description="Toggle shuffle mode"
    )
]
commands[2].options[0].choices = [discord.ApplicationCommandOptionChoice(
                name='Leaver speed',
                value='leaver'
              ),
              discord.ApplicationCommandOptionChoice(
                name='Weekly leaver speed',
                value='weekly'
              )
            ]
@bot.event
async def on_ready():
  print("I love coffee")
  
  async for guild in bot.fetch_guilds(limit=150):
    print(guild.name)
    bot.loop.create_task(BumpReminder.backgroundReminderRestarter(guild))
  print("Starting VC loop")
  bot.loop.create_task(Groovy.CheckLoop.loop())
  await bot.register_application_commands(commands=commands)

@bot.event
async def on_message(message: discord.Message):
  if message.author.bot: return
  if message.guild.id in unverifiedRole.keys() and unverifiedRole[message.guild.id] in [role.id for role in message.author.roles]:
    verify = Verify.Verify(member= message.author, message= message)
    await verify.checkVerifyStatus()

  if str(bot.user.id) in message.content:
    await message.add_reaction("<a:ping:866475995317534740>")
  await bot.process_commands(message)

@bot.command(add_slash_command=False, name="cutie", description="you are a cutie")
async def cutie(ctx):
  print(f"Cutie command started at {datetime.datetime.now()}")
  await ctx.send(embed=discord.Embed(description="ur a cutie 2 ;3"))
  print(f"Cutie command complete at {datetime.datetime.now()}")

@bot.command(add_slash_command=False, name="hug", description="Hugs a user!")
async def hug(ctx, *args, user=None, message=None):
  if user != None: ctx.args.append(user)
  print(message)
  if message != None: ctx.args += message.split(' ')
  interaction = Interaction.HugInteraction(ctx, "hug")
  await interaction.send()

@bot.command(add_slash_command=False, name="leaderboard", aliases=['leaverboard'], description="Shows a leaderboard")
async def leaderboard(ctx, leaderboard='leaver'):
  if leaderboard == 'weekly':
    interaction = Leaderboard.weeklyTimeLeaderboard(ctx.author)
  elif leaderboard == 'leaver':
    interaction = Leaderboard.timeLeaderboard(ctx.author)
  embed = await interaction.getLeaderboardEmbed()
  try: await ctx.reply(embed=embed, mention_author= False)
  except: await ctx.send(embed=embed)

@bot.command(add_slash_command=False, name="play", aliases=['p'], description="Plays a song/playlist from Youtube/Spotify")
async def play(ctx, input = '', *moreWords):
  input += ' '.join(moreWords).strip()
  embeds = await CommandInterpreter.playCommand(ctx, input)
  for embed in embeds:
    try: await ctx.reply(embed=embed, mention_author= False)
    except: await ctx.send(embed=embed)

@bot.command(add_slash_command=False, name="add", aliases=['a'], description="Adds a song/playlist to the queue from Youtube/Spotify")
async def add(ctx, input = '', *moreWords):
  input += ' '.join(moreWords).strip()
  embeds = await CommandInterpreter.addCommand(ctx, input)
  for embed in embeds:
    try: await ctx.reply(embed=embed, mention_author= False)
    except: await ctx.send(embed=embed)

@bot.command(add_slash_command=False, name="playlist", aliases=['pl'], description="Shows the current playlist")
async def playlist(ctx):
  playlist = Groovy.Playlist(ctx)
  await playlist.send()

@bot.command(add_slash_command=False, name="skip", aliases=['s'], description="Skips the song")
async def skip(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.skip(ctx)

@bot.command(add_slash_command=False, name="pause", description="Pause the music")
async def pause(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.pause(ctx)

@bot.command(add_slash_command=False, aliases=['dc'], description="Leave the vc")
async def disconnect(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.disconnect(ctx)

@bot.command(add_slash_command=False, name="nowplaying", aliases=['np'], description="Show the now playing song")
async def np(ctx):
  np = Groovy.NowPlaying(ctx)
  try: await ctx.reply(embed=np.getNowPlayingEmbed())
  except: await ctx.send(embed=np.getNowPlayingEmbed())

@bot.command(add_slash_command=False, name="shuffle", aliases=['sh'], description="Toggle shuffle mode")
async def shuffle(ctx):
  command = Groovy.MusicCommand(ctx)
  await command.player.toggleShuffle(ctx)

@bot.command(add_slash_command=False, name="search", description="Search youtube for something to play")
async def play(ctx, input = '', *moreWords):
  input = (input + ' ' + ' '.join(moreWords)).strip()
  embeds = await CommandInterpreter.searchCommand(ctx, input)
  for embed in embeds:
    try: await ctx.reply(embed=embed, mention_author= False)
    except: await ctx.send(embed=embed)


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

bot.run(TOKEN)