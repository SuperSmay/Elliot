import asyncio, random, datetime, traceback, discord, youtube_dl, googleapiclient.discovery, spotipy, urllib, math, threading, concurrent.futures
from youtubesearchpython.__future__ import VideosSearch

from globalVariables import bot, musicPlayers

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
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdlFormatOptions)



#Structure ref

'''
class Checkloop:
    Attributes:
        run loop:
            bool
    Functions:
        loop starter:
            Starts loop for bot

        loop:
            Checks each player in musicPlayers
            If there are other users in vc:
                set player time last member to current time
            If there are not other users in vc
                if time since last member is over 5 mins:
                    disconnect
                else:
                    ignore

class Player:
    Attributes:
        Playlist
            List of `Song` objects
        Unloaded Youtube Links:
            List of youtube links
        Current player
            YTDLSource
        Guild ID
            int
        Channel ID
            int - the last channel a command was used in
        Shuffle eneabled
            bool
        Time last member in vc
            datetime
        Send now playing:
            bool

    Functions:
        PlayNext:
            Plays next track in playlist
        AfterPlay:
            Runs after a track is completed
            If there are more songs to play:
                PlayNext
            Else:
                Stop
            If error:
                print traceback
        Skip:
            Returns and skips current track
        Disconnect:
            Leave vc and remove self from musicPlayers

        Add to playlist:
            Adds new `Song` to playlist, and plays it if nothing is playing
            returns whether the song was played
        
class Song:
    Attributes:
        title
            str
        duration
            str

    Functions:
        getData:
            returns youtubedl data

class MusicCommand:
    Attributes:
        guild, channel, message
            Obvious
        player
            `Player` for given context (guild)

    Functions:
        get vc:
            returns the voice channel the command author is connected to
        get player:
            returns the `Player` for guild
        join
            joins given vc
        move
            moves to given vc
        get now playing embed
            gets embed for current player in self.player

class PlayCommand(MusicCommand):
    Attributes:

    Functions:
        parse input(str):
            returns a dict of normalized youtube/spotify links or a search term:
                {youtubeLinks : [], youtubePlaylists : [], spotifyTrackLinks : [], spotifyAlbumLinks : [], spotifyPlaylistLinks : [],searchTerms : []}
        
        load songs(parsed dict):
            loads the links from the dict:
                gets spotify data for each link and adds it to playlist
                puts youtube links into player unloaded youtube urls
                searches youtube for search terms, then adds result to unloaded urls
                starts loading unloaded urls
                returns loaded count
        
        loadSpotifyTrack
            returns data for given spotify track
        
        Ditto for albums and playlists

        getYoutubePlaylist
            returns list of links in playlist

        loadYoutubeLink
            returns youtubedl'ed given link

        searchYoutube
            searches youtube for given term and returns link

        run command
            makes sure vc is set up
            returns error if user isn't in vc or can't talk etc
            parses input then loads it
            returns success message and loaded count
'''

class MusicPlayer:

    def __init__(self, ctx):
        self.guildID = ctx.guild.id
        self.channelID = ctx.channel.id
        self.playlist = []
        self.unloadedSongs = []
        self.currentPlayer = None
        self.shuffle = False
        self.sendNowPlaying = False
        self.timeOfLastMember = datetime.datetime.now(datetime.timezone.utc)
        
        musicPlayers[self.guildID] = self

    async def playNext(self):
        index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
        guild = await bot.fetch_guild(self.guildID)
        player = YTDLSource.from_url(YTDLSource, self.playlist[index].getData(), loop=bot.loop, stream=True)
        del(self.playlist[index])
        if guild.voice_client == None: return
        if guild.voice_client.is_playing(): guild.voice_client.source = player
        else: guild.voice_client.play(player, after= lambda e: bot.loop.create_task(self.afterPlay(e)))
        self.currentPlayer = player

    async def afterPlay(self, e):
        if len(self.playlist) > 0:
            await self.playNext()
        else:
            guild = await bot.fetch_guild(self.guildID)
            guild.voice_client.stop()
        if e != None:
            print(f"Exception occured: {e}")
    
    async def skip(self):
        player = self.currentPlayer
        if len(self.playlist) > 0:
            await self.playNext()
            return player
        else:
            guild = await bot.fetch_guild(self.guildID)
            guild.voice_client.stop()
        
    async def disconnect(self):
        guild = await bot.fetch_guild(self.guildID)
        await guild.voice_client.disconnect()
        del(musicPlayers[guild.id])

    async def loadingLoop(self):
        self.playLock = threading.Lock()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(self.loadDataInThread, range(0, len(self.playlist)))

            futures = []
            for song in self.playlist:
                futures.append(
                    executor.submit(
                        self.loadDataInThread, song
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                await self.playIfNothingPlaying()
        # i = 0
        # while i < len(self.playlist):
        #     if isinstance(self.playlist[i], UnloadedSong):
        #         await self.addToPlaylist(i)
        #     i += 1

    # async def addToPlaylist(self, i):
    #     x = threading.Thread(target=self.loadDataInThread, args=(i, self.on))
    #     x.start()

    def onThreadLoadComplete(self):
        bot.loop.create_task()

    async def playIfNothingPlaying(self):
        if not (await bot.fetch_guild(self.guildID)).voice_client.is_playing() and not (await bot.fetch_guild(self.guildID)).voice_client.is_paused():
            await self.playNext()
            return True
        return False

    def loadDataInThread(self, song):
        if isinstance(song, UnloadedSong):
            data = song.loadData()
            try: self.playlist[self.playlist.index(song)] = data
            except IndexError: pass


class CheckLoop:

    async def loop():
        runLoop = True
        while runLoop:
            players = musicPlayers.values()
            for player in players:
                guild = await bot.fetch_guild(player.guildID)
                if guild.voice_client == None or guild.voice_client.channel == None: del(musicPlayers[guild.id])
                else:
                    vc = guild.voice_client.channel
                    if len(vc.members) > 1:
                        player.timeOfLastMember = datetime.datetime.now(datetime.timezone.utc)
                    else:
                        if (datetime.datetime.now(datetime.timezone.utc) - player.timeOfLastMember).total_seconds() > 300:
                            channel = await bot.fetch_channel(player.channelID)
                            await channel.send(embed = discord.Embed(description="Leaving VC"))
                            await guild.voice_client.disconnect()
                            del(musicPlayers[guild.id])
            await asyncio.sleep(30)

# Songs

class Song:
    def __init__(self) -> None:
        self.data
        self.title
        self.duration
    
    def getData(self):
        return None

    def parseDuration(self, duration):
        '''
        Converts a time, in seconds, to a string in the format hr:min:sec, or min:sec if less than one hour.
    
        @type  duration: int
        @param duration: The time, in seconds

        @rtype:   string
        @return:  The new time, hr:min:sec or min:sec
        '''

        #Divides everything into hours, minutes, and seconds
        hours = math.floor(duration / 3600)
        tempTime = duration % 3600 #Modulo takes the remainder of division, leaving the remaining minutes after all hours are taken out
        minutes = math.floor(tempTime / 60)
        seconds = tempTime % 60

        #Formats time into a readable string
        newTime = ""
        if hours > 0: #Adds hours to string if hours are available; else this will just be blank
            newTime += str(hours) + ":"

        if minutes > 0:
            if minutes < 10: #Adds a 0 to one-digit times
                newTime += "0" + str(minutes) + ":"
            else:
                newTime += str(minutes) +":"
        else: #If there are no minutes, the place still needs to be held
            newTime += "00:"

        if seconds > 0:
            if seconds < 10: #Adds a 0 to one-digit times
                newTime += "0" + str(seconds)
            else:
                newTime += str(seconds)
        else:
            newTime += "00"

        return newTime

class YoutubeSong(Song):
    def __init__(self, data) -> None:
        self.data = data
        self.title = data['title']
        self.duration = self.parseDuration(data['duration'])

    def getData(self):
        return self.data

    def getTitle(self):
        return f"{self.title} ------------------- {self.duration}"

# class SpotifySong(Song):
#     def __init__(self, track) -> None:
#         self.title = f"{track['artists'][0]['name']} - {track['name']}"
#         self.duration = self.parseDuration(track['duration_ms']/1000)

#     async def getData(self):
#         videosSearch = VideosSearch(self.title, limit = 2)
#         videosResult = await videosSearch.next()
#         print(videosResult['result'][0]['link'])

#         data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(videosResult['result'][0]['link'], download=False))
#         return data

class UnloadedSong:
    def __init__(self, text) -> None:
        self.term = text

    def getTitle(self):
        return f"Loading [{self.term}]..."

class UnloadedURL(UnloadedSong):

    def loadData(self):
        return YoutubeSong(ytdl.extract_info(self.term, download=False))

    def getData(self):
        return (self.loadData()).getData()

class UnloadedSerach(UnloadedSong):
  
    def loadData(self):
        return YoutubeSong(ytdl.extract_info(self.term, download=False)['entries'][0])

    def getData(self):
        return (self.loadData()).getData()
    
# Commands
class MusicCommand:
    def __init__(self, ctx, input=None):
        self.ctx = ctx
        self.input = input
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.player = self.getPlayer()

    def getPlayer(self):
        if self.guild.id in musicPlayers.keys(): return musicPlayers[self.guild.id]
        else: return MusicPlayer(self.ctx)

    async def join(self, vc):
        await vc.connect()

    async def move(self, vc):
        await self.guild.voice_client.move_to(vc)

    async def shouldMoveToNewVC(self):
        return not (self.guild.voice_client.is_playing() or self.guild.voice_client.is_paused())

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed

class Play(MusicCommand):

    def parseInput(self, input: str):
        returnDict = {'youtubeLinks' : [], 'youtubePlaylists' : [], 'spotifyTrackLinks' : [], 'spotifyAlbumLinks' : [], 'spotifyPlaylistLinks' : [],'searchTerms' : []}
        if input == "":
            return returnDict
        if input.startswith("www.") and not (input.startswith("https://") or input.startswith("http://") or input.startswith("//")):
            input = "//" + input
        parsedURL = urllib.parse.urlparse(input)
        website = parsedURL.netloc.removeprefix("www.").removesuffix(".com").removeprefix("open.")
        if website == "":
            returnDict['searchTerms'].append(input)
        elif website == "youtube":
            tempDict = self.handleYoutubeLink(parsedURL)
            returnDict.update(tempDict)
        elif website == "youtu.be":
            tempDict = self.handleYoutubeShortLink(parsedURL) 
            returnDict.update(tempDict)
        elif website == "i2.ytimg" or website == "i.ytimg":
            tempDict = self.handleYoutubeImageLink(parsedURL)
            returnDict.update(tempDict)
        elif website == "spotify":
            tempDict = self.handleSpotifyLink(parsedURL)
            returnDict.update(tempDict)
        return returnDict

    def handleYoutubeLink(self, parsedURL):
        query = urllib.parse.parse_qs(parsedURL.query, keep_blank_values=True)
        path = parsedURL.path
        if "v" in query:
            return {'youtubeLinks' : [f"https://www.youtube.com/watch?v={query['v'][0]}"]}
        elif "list" in query:
            return {'youtubePlaylistLinks' : [f"https://www.youtube.com/watch?list={query['list'][0]}"]}
        elif "url" in query:
            return {'youtubeLinks' : [query['url'][0]]}
        elif len(path) > 10:
            return {'youtubeLinks' : [f"https://www.youtube.com/watch?v={path[-11:]}"]}
        else:
            return {'searchTerms' : [urllib.parse.urlunparse(parsedURL)]}

    def handleYoutubeShortLink(self, parsedURL):
        path = parsedURL.path
        return {'youtubeLinks' : [f"https://www.youtube.com/watch?v={path[-11:]}"]}

    def handleYoutubeImageLink(self, parsedURL):
        return {'youtubeLinks' : [f"https://www.youtube.com/watch?v={parsedURL.path[4:15]}"]}

    def handleSpotifyLink(self, parsedURL):
        url = urllib.parse.urlunparse(parsedURL)
        path = parsedURL.path
        if "playlist" in path:
            return {'spotifyPlaylistLinks' : [url]}
        elif "track" in path:
            return {'spotifyTrackLinks' : [url]}
        elif "album" in path:
            return {'spotifyAlbumLinks' : [url]}
        else:
            return {'searchTerms' : [url]}

    async def addUnloadedSongs(self, loadDict: dict):
        # returnDict = {'youtubeLinks' : [], 'youtubePlaylists' : [], 'spotifyTrackLinks' : [], 'spotifyAlbumLinks' : [], 'spotifyPlaylistLinks' : [],'searchTerms' : []}
        count = 0
        for key in loadDict.keys():
            if key == 'youtubeLinks':
                for link in loadDict[key]:
                    self.player.playlist.append(UnloadedURL(link))  # addToPlaylist(await self.loadYoutubeLink(link))
                    count += 1
            if key == 'youtubePlaylistLinks':
                for playlistLink in loadDict[key]:
                    for link in await self.getLinksFromYoutubePlaylist(playlistLink):
                        self.player.playlist.append(UnloadedURL(link))
                        count += 1
            if key == 'spotifyTrackLinks':
                for link in loadDict[key]:
                    self.player.playlist.append(UnloadedSerach(await self.loadSpotifyTrackURL(link)))
                    count += 1
            if key == 'spotifyAlbumLinks':
                for link in loadDict[key]:
                    for track in await self.loadTracksFromSpotifyAlbum(link):
                        self.player.playlist.append(UnloadedSerach(self.loadSpotifyTrack(track)))
                        count += 1
            if key == 'spotifyPlaylistLinks':
                for link in loadDict[key]:
                    for track in await self.loadTracksFromSpotifyPlaylist(link):
                        self.player.playlist.append(UnloadedSerach(self.loadSpotifyTrack(track)))
                        count += 1
            if key == 'searchTerms':
                for term in loadDict[key]:
                    self.player.playlist.append(UnloadedSerach(term))
                    count += 1
        return count
                    # link = await self.youtubeSearch(term)
                    # print(link)
                    # print(type(link))
                    # self.player.addToPlaylist(await self.loadYoutubeLink(link))
                     
    async def youtubeSearch(self, input):
        videosSearch = VideosSearch(input, limit = 2)
        videosResult = await videosSearch.next()
        print(videosResult['result'][0]['link'])
        return videosResult['result'][0]['link']

    async def getLinksFromYoutubePlaylist(self, link):
        #extract playlist id from url
        parsedURL = urllib.parse.urlparse(link)
        query = urllib.parse.parse_qs(parsedURL.query, keep_blank_values=True)
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

    async def loadTracksFromSpotifyPlaylist(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        playlist = sp.playlist(URL)
        # return [YoutubeSong(ytdl.extract_info(f"{item['track']['artists'][0]['name']} - {item['track']['name']}", download=False)['entries'][0]) for item in playlist['tracks']['items']]
        return [item['track'] for item in playlist['tracks']['items']]

    async def loadSpotifyTrackURL(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        track = sp.track(URL)
        title = f"{track['artists'][0]['name']} - {track['name']}"
        return title
        return YoutubeSong(ytdl.extract_info(title, download=False)['entries'][0])
        # return SpotifySong(track)

    def loadSpotifyTrack(self, track):
        title = f"{track['artists'][0]['name']} - {track['name']}"
        return title
        return YoutubeSong(ytdl.extract_info(title, download=False)['entries'][0])

    async def loadTracksFromSpotifyAlbum(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        album = sp.album(URL)
        return [item['track'] for item in album['tracks']['items']]

    async def setupVC(self):  #Attempts to set up VC. Returns exit status
        if not self.ctx.author.voice: return 'userNotInVoice'
        elif self.guild.voice_client == None: 
            await self.join(self.ctx.author.voice.channel)
            return 'joinedVoice'
        elif self.guild.voice_client.channel == self.ctx.author.voice.channel: return 'noChange'
        elif await self.shouldMoveToNewVC(): 
            await self.move(self.ctx.author.voice.channel)
            return 'movedToNewVoice'
        else: return 'alreadyPlayingInOtherVoice'

    async def loadYoutubeLink(self, url):
        return YoutubeSong(ytdl.extract_info(url, download=False))


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
        skippedTrack = await self.player.skip()
        embed= discord.Embed(title='Reached the end of queue') if skippedTrack == None else self.getNowPlayingEmbed()
        embed.set_footer(text= 'Add more with `/p`!' if skippedTrack == None else f'Skipped {skippedTrack.title}')
        return embed

class Playlist(MusicCommand):

    def getPlaylistString(self):
        return "```" + "\n".join(([f"{self.player.playlist.index(song) + 1}) {song.getTitle()}" for song in self.player.playlist[:20]])) + "```" if len(self.player.playlist) > 0 else '```Nothing to play next```'
        
    async def send(self):
        try: await self.ctx.reply(self.getPlaylistString())
        except: await self.ctx.send(self.getPlaylistString())

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

