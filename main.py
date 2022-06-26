# Bot
import datetime
import logging
import os
from time import sleep

from dotenv import load_dotenv
import discord
from discord.commands import Option, OptionChoice

from Statistics import log_event
from GlobalVariables import bot, last_start_time, on_log

logging.basicConfig()
logging.root.addFilter(on_log)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addFilter(on_log)

load_dotenv()

USE_DEV_MODE = os.environ.get('USE_DEV_MODE')

TOKEN = os.environ.get('BOT_TOKEN') if not USE_DEV_MODE else os.environ.get('DEV_TOKEN')

@bot.event
async def on_ready():
    global last_start_time
    logger.info("I love coffee")
    log_event('startup')
    last_start_time = datetime.datetime.utcnow()
    async for guild in bot.fetch_guilds(limit=150):
        logger.info(guild.name)


@bot.event
async def on_message(message: discord.Message):
    if message.author.id == bot.user.id:
        if hasattr(message.guild, 'id'):  # Ephemeral things
            log_event('message_send', modes=['global', 'guild'], id=message.guild.id)
    if message.author.bot:
        return
    if message.is_system():
        return
    if str(bot.user.id) in message.content:
        await message.add_reaction("<a:ping:866475995317534740>")

    await bot.process_commands(message)


@bot.event
async def on_message_edit(oldMessage, newMessage: discord.Message):
    if newMessage.author.bot:
        return
    if oldMessage.content == newMessage.content:
        return
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

# Admin bot internal commands
@bot.command(name="shutdown", description="Shutdown the bot")
async def shutdown(ctx):
    if ctx.author.id != bot.owner_id:
        return
    await ctx.reply(embed=discord.Embed(description="Closing up, have a nice day!"), mention_author=False)
    for cog in list(bot.cogs.keys()).copy():
        bot.remove_cog(cog)
        bot.loop.run_until_complete(await bot.close())

@bot.command(name="reload", description="Reloads all cogs")
async def reload(ctx):
    if ctx.author.id != bot.owner_id:
        return
    await ctx.reply(embed=discord.Embed(description="Reloading modules..."))
    failed = 0
    for extension in list(bot.extensions):
        try:
            bot.reload_extension(extension)
            logger.info(f"Reloaded module {extension}")
        except Exception:
            logger.error(f"Failed to reload module {extension}", exc_info=True)
            failed += 1
    else:
        await ctx.reply(embed=discord.Embed(description=f"Reloading modules complete. {failed} failed."))


bot.load_extension('BotInfo')
bot.load_extension('Interaction')
bot.load_extension('BumpReminder')
bot.load_extension('Groovy')
bot.load_extension('Settings')
bot.load_extension('Leaderboard')
bot.load_extension('Join')
bot.load_extension('Verify')
bot.load_extension('Levels')
bot.load_extension('Help')

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
    logger.info("Closing up, have a nice day!")
