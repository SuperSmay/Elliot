# Cool Bot
import datetime
import logging
import os
from time import sleep

import pathlib
from dotenv import load_dotenv
import discord
from discord.commands import Option, OptionChoice

from Extensions.Statistics import log_event
from Globals.GlobalVariables import bot, last_start_time, on_log

logging.basicConfig()
logging.root.addFilter(on_log)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addFilter(on_log)

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
async def on_message_edit(old_message, new_message: discord.Message):
    if new_message.author.bot:
        return
    if old_message.content == new_message.content:
        return
    await bot.process_commands(new_message)


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



def main():

    load_dotenv(pathlib.Path('Globals/.env'))

    USE_DEV_MODE = os.environ.get('USE_DEV_MODE').lower() == 'true'

    TOKEN = os.environ.get('BOT_TOKEN') if not USE_DEV_MODE else os.environ.get('DEV_TOKEN')

    bot.load_extension('Extensions.BotInfo')
    bot.load_extension('Extensions.Interaction')
    bot.load_extension('Extensions.BumpReminder')
    bot.load_extension('Extensions.Groovy')
    bot.load_extension('Extensions.Settings')
    bot.load_extension('Extensions.Leaderboard')
    bot.load_extension('Extensions.Join')
    bot.load_extension('Extensions.Verify')
    bot.load_extension('Extensions.Levels')
    # bot.load_extension('Extensions.Birthdays')
    bot.load_extension('Extensions.Help')

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

if __name__ == '__main__':
    main()
