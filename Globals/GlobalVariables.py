import discord
from discord.ext import commands
import datetime
from logging import LogRecord
from Extensions.Settings import fetch_setting
from Extensions.Statistics import log_event
import traceback

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

bot_version = '0.5.8'

last_start_time = datetime.datetime.utcnow()

numberEmoteList = [
            "<:gh_1:987463424550260746>",
            "<:gh_2:987463465159495751>",
            "<:gh_3:987463611939176568>",
            "<:gh_4:987463615273635860>",
            "<:gh_5:987463637755125850>",
            "<:gh_6:987463688934023269>",
            "<:gh_7:987463694399193169>",
            "<:gh_8:987463723457335306>",
            "<:gh_9:987463751794053211>",
            "<:gh_10:987463816554102914>"
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
    505116146467602432,
    810676381154803743
]

