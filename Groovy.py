import asyncio
import random
import traceback
import discord
import youtube_dl
import googleapiclient.discovery
import spotipy
import urllib
from youtubesearchpython.__future__ import VideosSearch

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


class YoutubeSong:
    def __init__(self, data) -> None:
        self.data = data
        self.title = data['title']
        self.duration = self.parseDuration(data['duration'])

    async def getData(self):
        return self.data

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


class SpotifySong:
    def __init__(self, track) -> None:
        self.title = f"{track['artists'][0]['name']} - {track['name']}"
        self.duration = self.parseDuration(track['duration_ms']/1000)

    async def getData(self):
        videosSearch = VideosSearch(self.title, limit = 2)
        videosResult = await videosSearch.next()
        print(videosResult['result'][0]['link'])

        data = await client.loop.run_in_executor(None, lambda: ytdl.extract_info(videosResult['result'][0]['link'], download=False))
        return data

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
    

    

class MusicPlayer:

    def __init__(self, message):
        self.guildID = message.guild.id
        self.playlist = []
        self.currentPlayer = None
        self.shuffle = False
        self.unloadedURLs = []
        musicPlayers[self.guildID] = self

    async def playNextItem(self):
        index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
        guild = await client.fetch_guild(self.guildID)
        player = YTDLSource.from_url(YTDLSource, await self.playlist[index].getData(), loop=client.loop, stream=True)
        del(self.playlist[index])
        if guild.voice_client == None: return
        if guild.voice_client.is_playing(): guild.voice_client.source = player
        else: guild.voice_client.play(player, after= lambda e: client.loop.create_task(self.afterPlay(e)))
        self.currentPlayer = player

    async def afterPlay(self, e):
        if len(self.playlist) > 0:
            await self.playNextItem()
            self.playNextSong = False
        else:
            if len(self.unloadedURLs) > 0:
                await asyncio.sleep(1)
                await self.afterPlay(e)
            else:
                self.playNextSong = True
                guild = await client.fetch_guild(self.guildID)
                guild.voice_client.stop()
        if e != None:
            print(f"Exception occured: {e}")

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

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed
        
class Play(MusicCommand):

    def __init__(self, message):
        super().__init__(message)
        self.type = ''

    async def loadInput(self):
        input = self.message.content[len(prefix) + len("play") + 1:].strip()
        try:
            linkList = await self.parseInput(input)
            if linkList != None:
                embed = discord.Embed(description= f'Added {len(linkList)} songs')
            else:
                embed = discord.Embed(description= f'Unpaused Music')
        except:
            traceback.print_exc()
            embed = None
        return embed

    async def getData(self, link):
        data = await client.loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))
        return data

    async def parseInput(self, input: str):
        if input == "":
            if self.guild.voice_client.is_paused():
                self.guild.voice_client.resume()
            return None
        if input.startswith("www.") and not (input.startswith("https://") or input.startswith("http://")):
            input = "//" + input
        parsedURL = urllib.parse.urlparse(input)
        website = parsedURL.netloc.removeprefix("www.").removesuffix(".com").removeprefix("open.")
        if website == "":
            list = await self.handleYoutubeSearch(input)
            self.player.unloadedURLs += list
        elif website == "youtube":
            list = await self.handleYoutubeLink(parsedURL)
            self.player.unloadedURLs += list
        if website == "youtu.be":
            list = self.handleYoutubeShortLink(parsedURL) 
            self.player.unloadedURLs += list
        elif website == "i2.ytimg" or website == "i.ytimg":
            list = self.handleYoutubeImageLink(parsedURL)
        elif website == "spotify":
            list = self.handleSpotifyLink(parsedURL)
            self.player.playlist += [SpotifySong(track) for track in list]
        return list

    async def handleYoutubeLink(self, parsedURL):
        self.type = 'youtube'
        query = urllib.parse.parse_qs(parsedURL.query, keep_blank_values=True)
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
            return await self.handleYoutubeSearch(urllib.parse.urlunparse(parsedURL))

    def handleYoutubeShortLink(self, parsedURL):
        self.type = 'youtube'
        path = parsedURL.path
        return [f"https://www.youtube.com/watch?v={path[-11:]}"]

    def handleYoutubeImageLink(self, parsedURL):
        self.type = 'youtube'
        return [f"https://www.youtube.com/watch?v={parsedURL.path[4:15]}"]

    async def handleSpotifyLink(self, parsedURL):
        self.type = 'spotify'
        url = urllib.parse.urlunparse(parsedURL)
        path = parsedURL.path
        if "playlist" in path:
            return self.getTracksFromSpotifyPlaylist(url)
        elif "track" in path:
            return self.getSpotifyTrack(url)
        elif "album" in path:
            return []
        else:
            return await self.handleYoutubeSearch(url)

    async def handleYoutubeSearch(self, input):
        self.type = 'youtube'
        videosSearch = VideosSearch(input, limit = 2)
        videosResult = await videosSearch.next()
        print(videosResult['result'][0]['link'])
        return [videosResult['result'][0]['link']]

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

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = youtube.playlistItems().list_next(request, response)

        return [f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}' for t in playlist_items]

    def getTracksFromSpotifyPlaylist(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        playlist = sp.playlist(URL)
        return [item['track'] for item in playlist['tracks']['items']]

    def getSpotifyTrack(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        song = sp.track(URL)
        return [song]

    def getTracksFromSpotifyAlbum(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        album = sp.album(URL)
        return [item['track'] for item in album['tracks']['items']]

    async def playYoutubeInput(self):
        if await self.shouldNotPlayOnLoad():
            await self.loadLinkList()
        else:
            await self.playFirstInput()
            await self.channel.send(embed=self.getNowPlayingEmbed())
            await self.loadLinkList()

    async def playSpotifyInput(self):
        if await self.shouldNotPlayOnLoad():
            pass
        else:
            await self.player.playNextItem()
            await self.channel.send(embed=self.getNowPlayingEmbed())

    async def shouldNotPlayOnLoad(self):
        return (await client.fetch_guild(self.guild.id)).voice_client.is_playing() or (await client.fetch_guild(self.guild.id)).voice_client.is_paused()

    async def playInput(self):
        if self.type == 'youtube':
            await self.playYoutubeInput()
        elif self.type == 'spotify':
            await self.playSpotifyInput()

    async def setupVC(self):
        if not self.message.author.voice: return discord.Embed(description="You need to join a vc")
        if self.guild.voice_client == None: 
            await self.join()
        elif self.guild.voice_client.channel == await self.getVC(): pass
        elif self.moveToNewVC(): await self.move()

    async def playFirstInput(self):
        
        data = await self.loadYoutubeLink(self.player.unloadedURLs.pop(0))
        self.player.playlist.insert(0, data)
        await self.player.playNextItem()
        

    async def loadLinkList(self):
        while len(self.player.unloadedURLs) > 0:
            self.player.playlist.append(await self.loadYoutubeLink(self.player.unloadedURLs.pop(0)))
        print("Finished loading all songs")

    async def loadYoutubeLink(self, url):
        return YoutubeSong(await client.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False)))

    
    async def runCommand(self):
        embed = discord.Embed(description= 'An error occured')
        tempEmbed = await self.setupVC()
        if tempEmbed != None: embed = tempEmbed
        tempEmbed = await self.loadInput()
        if tempEmbed != None: embed = tempEmbed
        client.loop.create_task(self.playInput())
        embed.color = 7528669
        return embed

    def getPlayingNextEmbed(self):
        embed = discord.Embed(title="Playing Next", description= f"{self.player.playlist[0]['title']}")
        embed.color = 7528669
        return embed


class Pause(MusicCommand):
    def pause(self):
        if self.guild.voice_client.is_paused():
            self.guild.voice_client.resume()
            return discord.Embed(description='Unpaused Music')
        else:
            self.guild.voice_client.pause()
            return discord.Embed(description='Paused Music')

class Shuffle(MusicCommand):
    
    def shuffle(self):
        if self.player.shuffle:
            self.player.shuffle = False
            return discord.Embed(description="Disabled Shuffle")
        else:
            self.player.shuffle = True
            return discord.Embed(description="Enable Shuffle")

class NowPlaying(MusicCommand):
    def __init__(self, message):
        super().__init__(message)
    

class Skip(MusicCommand):

    async def skip(self):
        if len(self.player.playlist) > 0:
            await self.player.playNextItem()
            # index = random.randint(0, len(self.player.playlist) - 1) if self.player.shuffle else 0
            # player = YTDLSource.from_url(YTDLSource, await self.player.playlist[index].getData(), loop=client.loop, stream=True)
            # del(self.player.playlist[index])
            # self.player.currentPlayer = player
            # self.guild.voice_client.source = player
        else:
            self.guild.voice_client.stop()

    async def send(self):    
        await self.channel.send(embed= self.getNowPlayingEmbed())



class Playlist(MusicCommand):

    def getPlaylistString(self):
        return "```" + "\n".join(([f"{self.player.playlist.index(song) + 1}) {song.title} ------------------- {song.duration}" for song in self.player.playlist] + [f"(Loading...) {url}" for url in self.player.unloadedURLs])[:21]) + "```"
        
    async def send(self):
        await self.message.reply(self.getPlaylistString())

    




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