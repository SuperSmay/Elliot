import asyncio, random, datetime, traceback, discord, youtube_dl, googleapiclient.discovery, spotipy, urllib, math, threading, concurrent.futures
from discord import guild
from youtubesearchpython.__future__ import VideosSearch

from globalVariables import bot, musicPlayers
import Events

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
        self.lastSearch = None
        self.playThisNext = None
        
        musicPlayers[self.guildID] = self
        EventHandlers.registerCallbacks(self.guildID)

    async def playNext(self):
        if len(self.playlist) == 0:
            guild = await bot.fetch_guild(self.guildID)
            if guild.voice_client != None: guild.voice_client.stop()
            return
        index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
        if self.playThisNext != None: 
            try:
                index = self.playlist.index(self.playThisNext)
                self.playThisNext = None
            except ValueError:
                index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
        while (not isinstance(self.playlist[index], LoadedSong)):
            index = random.randint(0, len(self.playlist) - 1) if self.shuffle else 0
            await asyncio.sleep(1)
        try: 
            guild = await bot.fetch_guild(self.guildID)
            player = YTDLSource.from_url(YTDLSource, self.playlist[index].data, loop=bot.loop, stream=True)
            del(self.playlist[index])
            if guild.voice_client == None: return
            if guild.voice_client.is_playing(): guild.voice_client.source = player
            else: guild.voice_client.play(player, after= lambda e: bot.loop.create_task(Events.SongEnd.call(self, self.guildID, e)))
            self.currentPlayer = player
            await Events.SongPlaybackStart.call(self, self.guildID, player)
        except youtube_dl.DownloadError as e:
            unloadedSong = self.playlist[index]
            if len(self.playlist) > 0:
                await self.playNext()
            await Events.DownloadError.call(self, self.guildID, unloadedSong, e)
            del(self.playlist[index])
        except:
            unloadedSong = self.playlist[index]
            if len(self.playlist) > 0:
                await self.playNext()
            await Events.DownloadError.call(self, self.guildID, unloadedSong, 'Unknown')
            del(self.playlist[index])
            
    async def skip(self, ctx=None):
        player = None
        if len(self.playlist) > 0:
            player = self.currentPlayer
            await self.playNext()
        else:
            guild = await bot.fetch_guild(self.guildID)
            guild.voice_client.stop()
        await Events.SongSkip.call(self, self.guildID, player, ctx)
        return player
        
    async def pause(self, ctx=None):
        guild = await bot.fetch_guild(self.guildID)
        if guild.voice_client.is_paused():
            guild.voice_client.resume()
            await Events.Unpause.call(self, self.guildID, ctx)
        else:
            guild.voice_client.pause()
            await Events.Pause.call(self, self.guildID, ctx)
        return guild.voice_client.is_paused()

    async def toggleShuffle(self, ctx=None):
        if self.shuffle:
            self.shuffle = False
            await Events.ShuffleDisable.call(self, self.guildID, ctx)
        else:
            self.shuffle = True
            await Events.ShuffleEnable.call(self, self.guildID, ctx)
        return self.shuffle

    async def disconnect(self, ctx=None):
        guild = await bot.fetch_guild(self.guildID)
        await guild.voice_client.disconnect()
        await Events.Disconnect.call(self, self.guildID, ctx)

    async def reset(self, ctx=None):
        await Events.Reset.call(self, self.guildID, ctx)

    async def loadingLoop(self, playThisNext=False, ctx=None):
        self.playLock = threading.Lock()
        count = 0
        title = ''
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.loadDataInThread, range(0, len(self.playlist)))

            futures = []
            for song in self.playlist:
                futures.append(
                    executor.submit(
                        self.loadDataInThread, song
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                title, status = (future.result())
                if status == 'success':
                    count += 1
                else:
                    await Events.DownloadError.call(self, self.guildID, song, status)
                await self.playIfNothingPlaying()
        await Events.LoadingComplete.call(self, self.guildID, count, playThisNext=playThisNext, title=title, ctx=ctx)

    async def playIfNothingPlaying(self):
        guild = await bot.fetch_guild(self.guildID)
        if not guild.voice_client.is_playing() and not guild.voice_client.is_paused():
            await self.playNext()
            return True
        return False

    def loadDataInThread(self, song):
        if isinstance(song, UnloadedURL):
            try: data = song.data
            except Exception as e:
                del(self.playlist[self.playlist.index(song)])
                return song.title, e
            try: 
                self.playlist[self.playlist.index(song)] = data
                if self.playThisNext == song: self.playThisNext = data
            except IndexError: return data.title, 'songNotInPlaylist'
            return data.title, 'success'
        return None, None

class EventHandlers:

    async def _sendGeneric(player, text, ctx, color=None):
        embed = discord.Embed(description=text)
        if color != None: embed.color = color
        if ctx == None:
            channel = await bot.fetch_channel(player.channelID)
            await channel.send(embed=embed)
        else:
            try: await ctx.reply(embed=embed)
            except: await ctx.send(embed=embed)

    async def _sendDownloadError(player, unloadedSong, e, ctx):
        await EventHandlers._sendGeneric(player, f'Failed to load {unloadedSong.text}. `{e}`', ctx)

    async def _songEnd(player, e):
        await player.playNext()
        if e != None:
            print(f"Exception occured: {e}")

    async def _sendDisconnect(player, ctx):
        await EventHandlers._sendGeneric(player, "Leaving VC", ctx)

    async def _cleanupAfterDisconnet(player: MusicPlayer, ctx):
        pass

    async def _sendReset(player, ctx):
        await EventHandlers._sendGeneric(player, "Resetting music player...", ctx)

    async def _cleanupBeforeReset(player: MusicPlayer, ctx):
        await player.disconnect()
        del(musicPlayers[player.guildID])
        Events.DownloadError.removeCallbacks(player.guildID)
        Events.SongEnd.removeCallbacks(player.guildID)
        Events.Disconnect.removeCallbacks(player.guildID)
        Events.Reset.removeCallbacks(player.guildID)
        Events.LoadingComplete.removeCallbacks(player.guildID)
        rejoinCommand = bot.get_application_command('join')
        await rejoinCommand.invoke(ctx)
    
    async def _loadingComplete(player, count, playThisNext=False, title=None, ctx=None):
        if count == 1:
            embed= discord.Embed(description=f'Successfully added {title}', color=7528669)
            if playThisNext:
                embed= discord.Embed(description=f'{title} will play next', color=7528669)
        elif count != 0:
            embed= discord.Embed(description=f'Successfully added {count} items', color=7528669)
        elif count == 0:
            return
        
        if ctx == None: 
            channel = bot.get_channel(player.channelID)
            await channel.send(embed=embed)
        else:
            try: await ctx.reply(embed=embed)
            except: await ctx.send(embed=embed)


    def registerCallbacks(guildID):
        Events.DownloadError.addCallback(guildID, EventHandlers._sendDownloadError)
        Events.SongEnd.addCallback(guildID, EventHandlers._songEnd)
        Events.Disconnect.addCallback(guildID, EventHandlers._sendDisconnect)
        Events.Disconnect.addCallback(guildID, EventHandlers._cleanupAfterDisconnet)
        Events.Reset.addCallback(guildID, EventHandlers._sendReset)
        Events.Reset.addCallback(guildID, EventHandlers._cleanupBeforeReset)
        Events.LoadingComplete.addCallback(guildID, EventHandlers._loadingComplete)




class CheckLoop:
    async def loop():
        runLoop = True
        while runLoop:
            musicPlayersCopy = musicPlayers.copy()
            players = musicPlayersCopy.values()
            for player in players:
                guild = await bot.fetch_guild(player.guildID)
                if guild.voice_client != None: 
                    vc = guild.voice_client.channel
                    if len(vc.members) > 0:
                        player.timeOfLastMember = datetime.datetime.now(datetime.timezone.utc)
                    else:
                        if (datetime.datetime.now(datetime.timezone.utc) - player.timeOfLastMember).total_seconds() > 300:
                            await player.disconnect()
            await asyncio.sleep(30)

class LoadedSong():
    def __init__(self, ytdlData) -> None:
        self.data = ytdlData
        self.title = ytdlData['title']
        self.duration = self.parseDuration(ytdlData['duration'])

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

class UnloadedURL():
    def __init__(self, text) -> None:
        self.text = text
        self.title = f"Loading {self.text}..."

    @property
    def data(self):
        return (self._loadData())

    def _loadData(self):
        return LoadedSong(ytdl.extract_info(self.text, download=False))

class UnloadedSearch(UnloadedURL):
  
    def _loadData(self):
        return LoadedSong(ytdl.extract_info(self.text, download=False)['entries'][0])
    
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

    async def reset(self):
        self.player.reset(self.ctx)

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
            try: 
                input = int(input)
                if input <= 10 and input > 0 and self.player.lastSearch != None:
                    returnDict['youtubeLinks'].append(self.player.lastSearch['result'][input-1]['link'])
                input = ''
            except ValueError:
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
                    self.player.playlist.append(UnloadedURL(link))
                    count += 1
            if key == 'youtubePlaylistLinks':
                for playlistLink in loadDict[key]:
                    for link in self.getLinksFromYoutubePlaylist(playlistLink):
                        self.player.playlist.append(UnloadedURL(link))
                        count += 1
            if key == 'spotifyTrackLinks':
                for link in loadDict[key]:
                    self.player.playlist.append(UnloadedSearch(self.loadSpotifyTrackURL(link)))
                    count += 1
            if key == 'spotifyAlbumLinks':
                for link in loadDict[key]:
                    for track in self.loadTracksFromSpotifyAlbum(link):
                        self.player.playlist.append(UnloadedSearch(self.loadSpotifyTrack(track)))
                        count += 1
            if key == 'spotifyPlaylistLinks':
                for link in loadDict[key]:
                    for track in self.loadTracksFromSpotifyPlaylist(link):
                        self.player.playlist.append(UnloadedSearch(self.loadSpotifyTrack(track)))
                        count += 1
            if key == 'searchTerms':
                for term in loadDict[key]:
                    self.player.playlist.append(UnloadedSearch(term))
                    count += 1
        return count

    def getLinksFromYoutubePlaylist(self, link):
        #extract playlist id from url
        parsedURL = urllib.parse.urlparse(link)
        query = urllib.parse.parse_qs(parsedURL.query, keep_blank_values=True)
        playlist_id = query["list"][0]

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

    def loadTracksFromSpotifyPlaylist(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        playlist = sp.playlist(URL)
        return [item['track'] for item in playlist['tracks']['items']]

    def loadSpotifyTrackURL(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        track = sp.track(URL)
        title = f"{track['artists'][0]['name']} - {track['name']}"
        return title

    def loadSpotifyTrack(self, track):
        title = f"{track['artists'][0]['name']} - {track['name']}"
        return title

    def loadTracksFromSpotifyAlbum(self, URL):
        client_id = "53c8241a03e54b6fa0bbc93bf966bc8c"
        client_secret = "034fe6ec5ad945de82dfbe1938224523"
        client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API
        album = sp.album(URL)
        return [item['track'] for item in album['tracks']['items']]

    def getPlayingNextEmbed(self):
        embed = discord.Embed(title="Playing Next", description= f"{self.player.playlist[0]['title']}")
        embed.color = 7528669
        return embed

class Search(MusicCommand):
    def __init__(self, ctx, input):
        super().__init__(ctx, input)
    
    async def youtubeSearch(self):
        videosSearch = VideosSearch(self.input, limit = 10)
        videosResult = await videosSearch.next()
        self.player.lastSearch = videosResult
        return self.formatSearch(videosResult)

    def formatSearch(self, videosResult):
        return '\n'.join([
            f"{videosResult['result'].index(item) + 1}) {item['title']} -------- {item['duration']}"
            for item in videosResult['result']
        ])

class NowPlaying(MusicCommand):
    def __init__(self, message):
        super().__init__(message)

    def getNowPlayingEmbed(self):
        embed = discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.color = 7528669
        return embed
class Playlist(MusicCommand):

    def getPlaylistString(self):
        return "```" + "\n".join(([f"{self.player.playlist.index(song) + 1}) {song.title}" for song in self.player.playlist[:20]])) + "```" if len(self.player.playlist) > 0 else '```Nothing to play next```'
        
    def run(self):
        return self.getPlaylistString()

class Skip(MusicCommand):
    async def skip(self):
        oldPlayer = await self.player.skip()
        embed= discord.Embed(title='Reached the end of queue') if oldPlayer == None else discord.Embed(title="Now Playing", description= f"{self.player.currentPlayer.title}")
        embed.set_footer(text= 'Add more with `/p`!' if oldPlayer == None else f'Skipped {oldPlayer.title}')
        embed.color = 7528669
        return embed

class Pause(MusicCommand):
    async def pause(self):
        newPauseState = await self.player.pause()
        if newPauseState: embed = discord.Embed(description='Paused music')
        else: embed = discord.Embed(description='Unpaused music')
        return embed
            
class Shuffle(MusicCommand):
    async def shuffle(self):
        newPauseState = await self.player.toggleShuffle()
        if newPauseState: embed = discord.Embed(description='Enabled shuffle')
        else: embed = discord.Embed(description='Disabled shuffle')
        return embed
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    def from_url(cls, data, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        source = discord.FFmpegPCMAudio(filename, **ffmpegOptions)
        return cls(source, data=data)

