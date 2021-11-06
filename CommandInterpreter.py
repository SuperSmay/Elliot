import Groovy
import discord
import traceback
from globalVariables import bot


async def playCommand(ctx, input):  #Runs the play command and returns a response embed
    embeds=[]
    try: 
        if len(input) == 0:  #If the input is empty, just unpause the music
            command = Groovy.MusicCommand(ctx)
            await command.player.pause(ctx)
            return
        play = Groovy.Play(ctx, input)
        play.player.channelID = ctx.channel.id
        exitCode = await play.setupVC()
        if exitCode=='joinedVoice' or exitCode=='noChange': pass
        elif exitCode=='userNotInVoice': return [discord.Embed(description="You need to join a vc")]
        elif exitCode=='movedToNewVoice': embeds.append(discord.Embed(description="Switched to your voice chat"))
        elif exitCode=='alreadyPlayingInOtherVoice': return [discord.Embed(description="Sorry, I'm already playing music elsewhere in this server")]
        loadDict = play.parseInput(play.input)
        count = await play.addUnloadedSongs(loadDict)
        bot.loop.create_task(play.player.loadingLoop())
        embed = discord.Embed(description= f'Adding {count} items...')
        embed.color = 7528669
        embeds.append(embed)

        for embed in embeds:
            try: await ctx.reply(embed=embed)
            except: await ctx.send(embed=embed)

    except:
        traceback.print_exc()
        embed = discord.Embed(description= f'An error occured')
        embeds.append(embed)

        for embed in embeds:
            try: await ctx.reply(embed=embed)
            except: await ctx.send(embed=embed)


    
