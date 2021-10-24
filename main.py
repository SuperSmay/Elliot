#Bot
import discord
from globalVariables import bot, prefix, unverifiedRole, joinChannel, musicPlayers
from activeMessages import activeMessages
import Interaction
import datetime
import Leaderboard
import Verify
import Join
import Shop
import traceback
import ImageScan
import BumpReminder
import Groovy

TOKEN = "ODg4OTY0ODM2NzE1ODE5MDA5.YUaXBQ.mD8g16yaJmWpjxl0NowGQCun_a0"
## Uno2 - "NzM2NDE4MDkwNjI3MjM1OTUx.Xxugyg.dBM5qCUAdp3F4ALd7dvqdRh7mHQ"
## Elliot - "ODQyOTkwODM4NDg1MDkwMzA2.YJ9WZQ.DnjiA1kxmS4YvErwNdWy7Vsfho0"
## Speakers - "ODg4OTY0ODM2NzE1ODE5MDA5.YUaXBQ.mD8g16yaJmWpjxl0NowGQCun_a0"

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

@bot.command(add_slash_command=False, name="cutie", description="you are a cutie")
async def cutie(ctx):
  await ctx.send("ur a cutie 2 ;3")

@bot.command(add_slash_command=False, name="hug", description="Hugs a user!")
async def hug(ctx, *args, user=None, message=None):
  if user != None: ctx.args.append(user)
  print(message)
  if message != None: ctx.args += message.split(' ')
  interaction = Interaction.HugInteraction(ctx, "hug")
  await interaction.send()

@bot.command(add_slash_command=False, name="leaderboard", description="Shows a leaderboard")
async def leaverboard(ctx, leaderboard='leaver'):
  if leaderboard == 'weekly':
    interaction = Leaderboard.weeklyTimeLeaderboard(ctx.author)
  elif leaderboard == 'leaver':
    interaction = Leaderboard.timeLeaderboard(ctx.author)
  try: await ctx.reply(embed= await interaction.getLeaderboardEmbed(), mention_author= False)
  except: await ctx.send(embed= await interaction.getLeaderboardEmbed())

@bot.command(add_slash_command=False, name="play", description="Plays a song/playlist from Youtube/Spotify")
async def play(ctx, input):
  play = Groovy.Play(ctx, input)
  try: await ctx.reply(embed=await play.runCommand())
  except: await ctx.send(embed=await play.runCommand())

@bot.command(add_slash_command=False, name="playlist", description="Shows the current playlist")
async def playlist(ctx):
  playlist = Groovy.Playlist(ctx)
  await playlist.send()

@bot.command(add_slash_command=False, name="skip", description="Skips the song")
async def skip(ctx):
    skip = Groovy.Skip(ctx)
    try: await ctx.reply(embed=await skip.skip())
    except: await ctx.send(embed=await skip.skip())

@bot.command(add_slash_command=False, name="pause", description="Pause the music")
async def pause(ctx):
  pause = Groovy.Pause(ctx)
  try: await ctx.reply(embed=await pause.pause())
  except: await ctx.send(embed=await pause.pause())

@bot.command(add_slash_command=False, name="disconnect", description="Leave the vc")
async def disconnect(ctx):
  await ctx.guild.voice_client.disconnect()
  del(musicPlayers[ctx.guild.id])

@bot.command(add_slash_command=False, name="now playing", description="Show the now playing song")
async def np(ctx):
  np = Groovy.NowPlaying(ctx)
  try: await ctx.reply(embed=np.getNowPlayingEmbed())
  except: await ctx.send(embed=np.getNowPlayingEmbed())

@bot.command(add_slash_command=False, name="shuffle", description="Toggle shuffle mode")
async def cutie(ctx):
  shuffle = Groovy.Shuffle(ctx)
  try: await ctx.reply(embed=shuffle.shuffle())
  except: await ctx.send(embed=shuffle.shuffle())


@bot.event
async def on_message(message: discord.Message):
  if message.author.bot: return
  if message.guild.id in unverifiedRole.keys() and unverifiedRole[message.guild.id] in [role.id for role in message.author.roles]:
    verify = Verify.Verify(member= message.author, message= message)
    await verify.checkVerifyStatus()

  if str(bot.user.id) in message.content:
    await message.add_reaction("<a:ping:866475995317534740>")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
  if payload.guild_id in unverifiedRole.keys() and unverifiedRole[payload.guild_id] in [role.id for role in payload.member.roles]:
    verify = Verify.Verify(member= payload.member)
    await verify.checkVerifyStatus()


@bot.event
async def on_member_remove(user):
  leave = Join.Leave(user)
  await leave.send()
  timeSinceJoin = datetime.datetime.utcnow() - user.joined_at
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