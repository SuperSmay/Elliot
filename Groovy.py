import asyncio
from json import load
import random
import traceback
import discord
from discord import embeds
from discord.player import AudioSource
import youtube_dl
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse

from globalVariables import client, musicPlayers, prefix

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdlFormatOptions = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

ffmpegOptions = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = youtube_dl.YoutubeDL(ytdlFormatOptions)

class MusicPlayer:

    def __init__(self, message):
        self.guildID = message.guild.id
        self.playlist = []
        self.currentlyPlaying = None
        self.currentPlayer = None
        self.shuffle = False
        self.unloadedURLs = []
        musicPlayers[self.guildID] = self

    def playNextItem(self):
        index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
        guild = client.get_guild(self.guildID)
        player = YTDLSource.from_url(YTDLSource, self.playlist[index], loop=client.loop, stream=True)
        del(self.playlist[index])
        if guild.voice_client.is_playing: guild.voice_client.stop()
        guild.voice_client.play(player, after=self.afterPlay)
        self.currentPlayer = player

    def afterPlay(self, e):
        if len(self.playlist) > 0:
            self.playNextItem()
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

    def __init__(self, message):
        super().__init__(message)

    def loadInput(self):
        input = self.message.content[len(prefix) + len("play") + 1:].strip()
        try:
            linkList = self.parseInput(input)
            self.player.unloadedURLs += linkList
            embed = discord.Embed(description= f'Added {len(linkList)} songs')
        except:
            traceback.print_exc()
            embed = None
        return embed

    async def getData(self, link):
        data = await client.loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))
        return data

    def parseInput(self, input: str):
        if input == "":
            self.unpause()
        if input.startswith("www.") and not (input.startswith("https://") or input.startswith("http://")):
            input = "//" + input
        parsedURL = urlparse(input)
        website = parsedURL.netloc.removeprefix("www.").removesuffix(".com").removeprefix("open.")
        if website == "":
            list = self.handleSearch(input)
        elif website == "youtube":
            list = self.handleYoutubeLink(parsedURL) 
        if website == "youtu.be":
            list = self.handleYoutubeShortLink(parsedURL) 
        elif website == "i2.ytimg" or website == "i.ytimg":
            list = self.handleYoutubeImageLink(parsedURL)
        elif website == "spotify":
            list = self.handleSpotifyLink(parsedURL)
        return list
        #Figure out where the link came from, or whether to search
        #If not youtube, create search term for youtube
        #Check if playlist
            #if true - Get links in playlist
        #return link list 
        pass

    def handleYoutubeLink(self, parsedURL):
        query = parse_qs(parsedURL.query, keep_blank_values=True)
        path = parsedURL.path
        if "v" in query:
            return [f"https://www.youtube.com/watch?v={query['v'][0]}"]
        elif "list" in query:
            return self.loadYoutubePlaylist(query)
        elif "url" in query:
            return [query['url'][0]]
        elif len(path) > 10:
            return [f"https://www.youtube.com/watch?v={path[-11:]}"]
        else:
            return self.handleSearch(input)

    def handleYoutubeShortLink(self, parsedURL):
        path = parsedURL.path
        return [f"https://www.youtube.com/watch?v={path[-11:]}"]

    def handleYoutubeImageLink(self, parsedURL):
        return f"https://www.youtube.com/watch?v={parsedURL.path[4:15]}"

    def handleSpotifyLink(self, parsedURL):
        return None

    async def loadLinks(self):
        #YoutubeDL list of links (Or single link/search term)
        #return list of data
        pass

    def loadYoutubePlaylist(self, query):
        #extract playlist id from url
        playlist_id = query["list"][0]

        print(f'get all playlist items links from {playlist_id}')
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyBT0Ihv9c2ijSrzZxp3EX3MHiTnoKvZpf8")

        request = youtube.playlistItems().list(
            part = "snippet",
            playlistId = playlist_id,
            maxResults = 500
        )
        #response = request.execute()

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        return [f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}' for t in playlist_items]

   

    async def playInput(self):
        if (len(self.player.playlist) > 0 and len(self.player.unloadedURLs) > 0):
            await self.loadLinkList()
        else:
            await self.playFirstInput()
            await self.loadLinkList()

    async def setupVC(self):
        if not self.message.author.voice: return discord.Embed(description="You need to join a vc")
        if self.guild.voice_client == None: 
            await self.join()
        elif self.guild.voice_client.channel == await self.getVC(): pass
        elif self.moveToNewVC(): await self.move()

    async def playFirstInput(self):
        
        data = await self.getData(self.player.unloadedURLs.pop(0))
        self.player.playlist.insert(0, data)
        self.player.playNextItem()
        await self.channel.send(embed=self.getNowPlayingEmbed())

    async def loadLinkList(self):
        while len(self.player.unloadedURLs) > 0:
            self.player.playlist.append(await client.loop.run_in_executor(None, lambda: ytdl.extract_info(self.player.unloadedURLs.pop(0), download=False)))
        print("Finished loading all songs")

    
    async def runCommand(self):
        embed = discord.Embed(description= 'An error occured')
        tempEmbed = await self.setupVC()
        if tempEmbed != None: embed = tempEmbed
        tempEmbed = self.loadInput()
        if tempEmbed != None: embed = tempEmbed
        client.loop.create_task(self.playInput())
        embed.color = 7528669
        return embed









    def getArguments(self):
        return self.message.content[len(prefix) + len("play") + 1:].strip()  #Remove the prefix and interaction by cutting the string by the length of those two combined

    async def attemptPlay(self):

        if len(self.getArguments()) == 0: 
            if len(self.player.playlist) == 0: return await self.message.reply("You need to provide a URL to play")
            else: self.player.playNextItem()
        if not self.message.author.voice: return await self.message.reply("You need to join a vc")
        if self.guild.voice_client == None: 
            await self.join()
        elif self.guild.voice_client.channel == await self.getVC(): pass
        elif self.moveToNewVC(): await self.move()
        try:
            self.data = await self.getData()
            if "entries" not in self.data: 
                self.player.playlist.insert(0, self.data)
            else:
                for entry in self.data["entries"]:
                    self.player.playlist.append(entry)
                await self.message.reply(embed= self.getPlaylistEmbed(len(self.data["entries"])))
            if not self.guild.voice_client.is_playing():
                    self.player.playNextItem()
                    await self.message.reply(embed= self.getNowPlayingEmbed())
            else:
                await self.message.reply(embed= self.getPlayingNextEmbed())
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

class Shuffle(MusicCommand):
    
    def shuffle(self):
        if self.player.shuffle:
            self.player.shuffle = False
            return discord.Embed(description="Disabled Shuffle")
        else:
            self.player.shuffle = True
            return discord.Embed(description="Enable Shuffle")

class Skip(MusicCommand):

    def skip(self):
        if len(self.player.playlist) > 0:
            index = random.randint(0, len(self.player.playlist) - 1) if self.player.shuffle else 0
            player = YTDLSource.from_url(YTDLSource, self.player.playlist[index], loop=client.loop, stream=True)
            del(self.player.playlist[index])
            self.player.currentPlayer = player
            self.guild.voice_client.source = player
        else:
            self.guild.voice_client.stop()

    async def send(self):    
        await self.channel.send(embed= self.getNowPlayingEmbed())

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed

class Playlist(MusicCommand):

    def getPlaylistString(self):
        return "```" + "\n".join([f"{self.player.playlist.index(song) + 1}) {song['title']} ------------------- {self.parseDuration(song['duration'])}" for song in self.player.playlist] + [f"(Loading...) {url}" for url in self.player.unloadedURLs]) + "```"
        
    async def send(self):
        await self.message.reply(self.getPlaylistString())

    def parseDuration(self, duration: int):
        if duration > 0:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            duration = []
            if days > 0:
                duration.append('{}'.format(days))
            if hours > 0:
                duration.append('{}'.format(hours))
            if minutes > 0:
                duration.append('{}'.format(minutes))
            if seconds > 0:
                duration.append('{}'.format(seconds))
            
            value = ':'.join(duration)
        
        elif duration == 0:
            value = "LIVE"
        
        return value




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