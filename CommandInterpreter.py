import Groovy
import discord
import traceback
import datetime
from globalVariables import bot


async def playCommand(ctx, input):  #Runs the play command and returns a response embed
    embeds=[]
    try: 
        if len(input) == 0:  #If the input is empty, just unpause the music
            pause = Groovy.Pause(ctx)
            return [pause.pause()]
        play = Groovy.Play(ctx, input)
        exitCode = await play.setupVC()
        if exitCode=='joinedVoice' or exitCode=='noChange': pass
        elif exitCode=='userNotInVoice': return [discord.Embed(description="You need to join a vc")]
        elif exitCode=='movedToNewVoice': embeds.append(discord.Embed(description="Switched to your voice chat"))
        elif exitCode=='alreadyPlayingInOtherVoice': return [discord.Embed(description="I'm already playing music elsewhere")]
        loadDict = play.parseInput(play.input)
        count = await play.addUnloadedSongs(loadDict)
        bot.loop.create_task(play.player.loadingLoop(playCommandCallback))
        embed = discord.Embed(description= f'Adding {count} items...')
        embed.color = 7528669
        embeds.append(embed)

        return embeds

    except:
        traceback.print_exc()
        embed = discord.Embed(description= f'An error occured')
        embeds.append(embed)

        return embeds

async def playCommandCallback(player, count, title = None):
    if count == 1:
        embed = discord.Embed(description = f'Successfully added {title}')
        embed.color = 7528669
        channel = await bot.fetch_channel(player.channelID)
        await channel.send(embed=embed)
    elif count != 0:
        embed = discord.Embed(description = f'Successfully added {count} items')
        embed.color = 7528669
        channel = await bot.fetch_channel(player.channelID)
        await channel.send(embed=embed)
    
