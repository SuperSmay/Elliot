import discord
from discord.ext import commands
import datetime
from logging import LogRecord
from Settings import fetch_setting
from Statistics import log_event

intents = discord.Intents().default()
intents.members = True
intents.voice_states = True
intents.message_content = True

def prefix(bot, message):
    prefix: str = fetch_setting(message.guild.id, 'prefix')
    return [prefix, prefix.capitalize(), bot.user.mention]

def on_log(record: LogRecord):

    if record.levelno > 30:

        async def send_error():
            user =  await bot.fetch_user(bot.owner_id)
            embed = discord.Embed(title='An error occurred', description=f'```{record.getMessage()}\n{record.pathname}\nLINE:{record.lineno}```')
            await user.send(embed=embed)

        bot.loop.create_task(send_error())

        log_event('error')

    return True

bot = commands.Bot(command_prefix=prefix, description="Robo Barista for The Gayming Café!", intents=intents, help_command=None, case_insensitive=True, strip_after_prefix=True)
bot.owner_id = 243759220057571328

bot_version = '0.5.5'

last_start_time = datetime.datetime.utcnow()

numberEmoteList = [
            "<:gh_1:856557384071512065>",
            "<:gh_2:856557978383155200>",
            "<:gh_3:856557993030189096>",
            "<:gh_4:856558007352950795>",
            "<:gh_5:856558030836990002>",
            "<:gh_6:856558055138394169>",
            "<:gh_7:856558070069723146>",
            "<:gh_8:856558533814124544>",
            "<:gh_9:856558551547510794>",
            "<:gh_10:856558568986771466>"
        ]


loadedInventories = {}

code_contributors = [
    243759220057571328,
    332653982470242314
]

gif_contributors = [
    253286336264536070,
    332653982470242314,
    456051303823441920,
    634097307327135750,
    505116146467602432
]

