import Groovy
import discord
import traceback
import datetime
from globalVariables import bot


async def playCommand(ctx, input):  #Runs the play command and returns a response embed
    embeds=[]
    print(f"Start command at {datetime.datetime.now()}")
    try: 
        if len(input) == 0:  #If the input is empty, just unpause the music
            pause = Groovy.Pause(ctx)
            return [pause.pause()]
        print(f"Check for pause at {datetime.datetime.now()}")
        play = Groovy.Play(ctx, input)
        print(f"Create play object at {datetime.datetime.now()}")
        exitCode = await play.setupVC()
        print(f"VC setup complete at {datetime.datetime.now()}")
        if exitCode=='joinedVoice' or exitCode=='noChange': pass
        elif exitCode=='userNotInVoice': return [discord.Embed(description="You need to join a vc")]
        elif exitCode=='movedToNewVoice': embeds.append(discord.Embed(description="Switched to your voice chat"))
        elif exitCode=='alreadyPlayingInOtherVoice': return [discord.Embed(description="I'm already playing music elsewhere")]
        print(f"VC exit code parsed at {datetime.datetime.now()}")
        loadDict = play.parseInput(play.input)
        print(f"Loaddict created at {datetime.datetime.now()}")
        count = await play.addUnloadedSongs(loadDict)
        print(f"Unloaded songs added at {datetime.datetime.now()}")
        bot.loop.create_task(play.player.loadingLoop())
        print(f"Loading loop started at {datetime.datetime.now()}")
        embed = discord.Embed(description= f'Successfully added {count} items')
        embed.color = 7528669
        embeds.append(embed)

        return embeds

    except:
        traceback.print_exc()
        embed = discord.Embed(description= f'An error occured')
        embeds.append(embed)

        return embeds

