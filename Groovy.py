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

    async def play(self, url):
        player = await YTDLSource.from_url(YTDLSource, url, loop=client.loop, stream=True)
        guild = await self.guild()
        guild.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        self.currentPlayer = player

    async def guild(self):
        return await client.fetch_guild(self.guildID)
        
    

class MusicCommands:
    def __init__(self, message):
        self.message = message
        self.guild = message.guild
        self.channel = message.channel
        self.arguments = self.getArguments()

    def getArguments(self):
        argString = self.message.content[len(prefix) + len("play") + 1:].strip()  #Remove the prefix and interaction by cutting the string by the length of those two combined
        return argString.split(" ")

    def getURL(self):
        return self.arguments[0]

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

    async def play(self):
        if len(self.arguments) == 0: return await self.message.reply("You need to provide a URL to play")
        if not self.message.author.voice: return await self.message.reply("You need to join a vc")
        if self.guild.voice_client == None: await self.join()
        elif self.guild.voice_client.channel == await self.getVC(): pass
        elif self.moveToNewVC(): await self.move()

        player = self.getPlayer()
        try:
            if self.guild.voice_client.is_playing: self.guild.voice_client.stop()
            await player.play(self.getURL())
            await self.send()
            traceback.print_exc()
        except:
            await self.message.reply(f"An error occured while playing the URL `{self.getURL()}`")

    def getEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.getPlayer().currentPlayer.title}")
        embed.color = 7528669
        return embed

    async def send(self):
        await self.message.reply(embed= self.getEmbed())

        









class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

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