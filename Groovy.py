import asyncio
from json import load
import traceback
import discord
import youtube_dl

from globalVariables import client, musicPlayers, prefix

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdlFormatOptions = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpegOptions = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdlFormatOptions)

class MusicPlayer:

    def __init__(self, message):
        self.guildID = message.guild.id
        self.playlist = []
        self.currentlyPlaying = None
        self.currentPlayer = None
        musicPlayers[self.guildID] = self

    def play(self):
        guild = client.get_guild(self.guildID)
        player = YTDLSource.from_url(YTDLSource, self.playlist[0], loop=client.loop, stream=True)
        if guild.voice_client.is_playing: guild.voice_client.stop()
        guild.voice_client.play(player, after=self.afterPlay)
        del(self.playlist[0])
        self.currentPlayer = player

    def afterPlay(self, e):
        if len(self.playlist) > 0:
            self.play()
        else:
            guild = client.get_guild(self.guildID)
            guild.voice_client.stop()
        if e != None:
            print(f"Exception occured: {e}")

    # async def guild(self):
    #     return await client.fetch_guild(self.guildID)
        
    

class MusicCommand:
    def __init__(self, message):
        self.message = message
        self.guild = message.guild
        self.channel = message.channel
        self.player = self.getPlayer()

    async def getVC(self):
        return self.message.author.voice.channel

    def getPlayer(self):
        if self.guild.id in musicPlayers.keys(): return musicPlayers[self.guild.id]
        else: return MusicPlayer(self.message)

    async def join(self):
        await (await self.getVC()).connect()

    async def move(self):
        await self.guild.voice_client.move_to(await self.getVC)

    def moveToNewVC(self):
        return True
        
class Play(MusicCommand):

    async def getData(self):
        url = self.getArguments()[0]
        data = await client.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return data

    def getArguments(self):
        argString = self.message.content[len(prefix) + len("play") + 1:].strip()  #Remove the prefix and interaction by cutting the string by the length of those two combined
        return argString.split(" ")

    def loadPlaylist(self, data):
        pass

    async def attemptPlay(self):

        if len(self.getArguments()) == 0: 
            if len(self.player.playlist) == 0: return await self.message.reply("You need to provide a URL to play")
            else: self.player.play()
        if not self.message.author.voice: return await self.message.reply("You need to join a vc")
        if self.guild.voice_client == None: await self.join()
        elif self.guild.voice_client.channel == await self.getVC(): pass
        elif self.moveToNewVC(): await self.move()
        try:
            self.data = await self.getData()
            if "entries" not in self.data: 
                self.player.playlist.insert(0, self.data)
                if not self.guild.voice_client.is_playing:
                    self.player.play()
                    await self.message.reply(embed= self.getNowPlayingEmbed())
                else:
                    await self.message.reply(embed= self.getPlayingNextEmbed())
            else:
                for entry in self.data["entries"]:
                    self.player.playlist.append(entry)
                self.player.play()
                await self.message.reply(embed= self.getPlaylistEmbed(len(self.data["entries"])))
                await self.channel.send(embed= self.getNowPlayingEmbed())
        except:
            traceback.print_exc()
            await self.message.reply(f"An error occured while playing the URL `{self.getArguments()[0]}`")

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed

    def getPlayingNextEmbed(self):
        embed = discord.Embed(title="Playing Next", description= f"{self.player.playlist[0]['title']}")
        embed.color = 7528669
        return embed

    def getPlaylistEmbed(self, length):
        embed = discord.Embed(description= f"Added {length} tracks")
        embed.color = 7528669
        return embed

class Skip(MusicCommand):

    async def skip(self):
        player = YTDLSource.from_url(YTDLSource, self.player.playlist[0], loop=client.loop, stream=True)
        del(self.player.playlist[0])
        self.player.currentPlayer = player
        self.guild.voice_client.source = player
        await self.channel.send(embed= self.getNowPlayingEmbed())

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed

    








class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, data, volume=0.5):
        #source = discord.FFmpegPCMAudio(data['url'], **ffmpegOptions)
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    def from_url(cls, data, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        #data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        #print(data)
        #if 'entries' in data:
            # take first item from a playlist
            #data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        source = discord.FFmpegPCMAudio(filename, **ffmpegOptions)
        return cls(source, data=data)



class Music:

    async def join(guild, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if guild.voice_client is not None:
            return await guild.voice_client.move_to(channel)

        await channel.connect()

    async def yt(message, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with message.channel.typing():
            player = await YTDLSource.from_url(YTDLSource, url, loop=client.loop)
            message.guild.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await message.reply(f'Now playing: {player.title}')

    async def stream(message, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with message.channel.typing():
            player = await YTDLSource.from_url(YTDLSource, url, loop=client.loop, stream=True)
            message.guild.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await message.reply(f'Now playing: {player.title}')