import asyncio
from code import interact
import concurrent.futures
import datetime
import logging
import pathlib
import random
import threading
import urllib.parse

import discord
import googleapiclient.discovery
import spotipy
import youtube_dl
from discord.ext import commands, tasks
from discord.commands import Option, OptionChoice
from youtubesearchpython import VideosSearch

from globalVariables import bot, music_players

##TODO List
    ## Youtube-DL simple youtube links ✓
    ## Rearrange ✓ish
    ## Split youtube playlists ✓
    ## Convert simple spotify tracks ✓
    ## Split spotify playlists and albums ✓
    ## Play youtube-dl'd input correctly ✓
    ## Add command ✓
    ## Skip command ✓
    ## Playlist command ✓ (Properly this time)
    ## Skip backwards command
    ## Play history (Youtube link or dl'd dict?) 
##

#region Variables and setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

client_id = (open(pathlib.Path('spotify-id'), 'r')).read()
client_secret = (open(pathlib.Path('spotify-secret'), 'r')).read()
client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API

yt = googleapiclient.discovery.build("youtube", "v3", developerKey = (open(pathlib.Path('youtube-api-key'), 'r')).read())
#endregion

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, data, loaded_song, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.loaded_song = loaded_song
        self.title = data.get('title')
        self.url = data.get('url')

    def from_url(cls, data, loaded_song, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        source = discord.FFmpegPCMAudio(filename, **ffmpegOptions)
        return cls(source, data=data, loaded_song=loaded_song)

class SongLoadingContext:
    def __init__(self) -> None:
        self._message = None
        self.parent_playlist = None
        self._future_embeds = []

    async def send_message(self, ctx, embed: discord.Embed):
        message = self._message
        if isinstance(message, str):
            self._future_embeds.append(embed)
        elif isinstance(message, discord.Message):
            self._message = 'Editing'
            await message.edit(embed=embed)
            self._message = message
            if len(self._future_embeds) > 0:
                next = self._future_embeds[-1]
                self._future_embeds = []
                await self.send_message(ctx, next)
        elif message == None:
            self._message = 'Sending'
            try: self._message = await ctx.reply(embed=embed, mention_author=False)
            except: self._message = await ctx.respond(embed=embed)
            if len(self._future_embeds) > 0:
                next = self._future_embeds[-1]
                self._future_embeds = []
                await self.send_message(ctx, next)

#region Song Classes
class UnloadedYoutubeSong:
    def __init__(self, youtube_url, loading_context: SongLoadingContext) -> None:
        self.youtube_url = youtube_url
        self.loading_context = loading_context
    def __str__(self):
        return self.youtube_url

class UnloadedYoutubePlaylist:
    def __init__(self, youtube_playlist_url, loading_context: SongLoadingContext) -> None:
        self.youtube_playlist_url = youtube_playlist_url
        self.loading_context = loading_context
    def __str__(self):
        return self.youtube_playlist_url

class UnloadedYoutubeSearch:
    def __init__(self, youtube_search, loading_context: SongLoadingContext) -> None:
        self.youtube_search = youtube_search
        self.loading_context = loading_context
    def __str__(self):
        return self.youtube_search

class UnloadedSpotifyTrack:
    def __init__(self, spotify_track_url, loading_context: SongLoadingContext) -> None:
        self.spotify_track_url = spotify_track_url
        self.loading_context = loading_context
    def __str__(self):
        return self.spotify_track_url

class UnloadedSpotifyAlbum:
    def __init__(self, spotify_album_url, loading_context: SongLoadingContext) -> None:
        self.spotify_album_url = spotify_album_url
        self.loading_context = loading_context
    def __str__(self):
        return self.spotify_album_url

class UnloadedSpotifyPlaylist:
    def __init__(self, spotify_playlist_url, loading_context: SongLoadingContext) -> None:
        self.spotify_playlist_url = spotify_playlist_url
        self.loading_context = loading_context
    def __str__(self):
        return self.spotify_playlist_url


class PartiallyLoadedSong:
    def __init__(self) -> None:
        self.title = None
        self.duration = None

        self.random_value = None
        self.song_list = None
        self.loading_context = None

    def get_youtube_dl(self):
        pass

class LoadedYoutubeSong(PartiallyLoadedSong):
    def __init__(self, youtube_data: dict, loading_context: SongLoadingContext, song_list=None, random_value=None) -> None:
        self.title = youtube_data['title']
        self.duration = youtube_data['duration']

        self.loading_context = loading_context
        self.random_value = random.randint(0, 10000) if random_value != None else random_value
        self.song_list = song_list if song_list != None else []

        self.youtube_data = youtube_data

    def get_youtube_dl(self):
        data = ytdl.extract_info(self.youtube_data['webpage_url'], download=False)
        return LoadedYoutubeSong(data, self.loading_context, self.song_list, self.random_value)

    def __str__(self) -> str:
        return self.title

class LoadedYoutubePlaylistSong(PartiallyLoadedSong):
    def __init__(self, youtube_snippet_from_playlist: dict, loading_context: SongLoadingContext) -> None:
        self.title = youtube_snippet_from_playlist['title']
        self.duration = 0

        self.loading_context = loading_context
        self.random_value = random.randint(0, 10000)
        self.song_list = []

        self.youtube_snippet_from_playlist = youtube_snippet_from_playlist

    def get_youtube_dl(self):
        data = ytdl.extract_info(f'https://www.youtube.com/watch?v={self.youtube_snippet_from_playlist["resourceId"]["videoId"]}', download=False)
        return LoadedYoutubeSong(data ,self.loading_context, self.song_list, self.random_value)

    def __str__(self) -> str:
        return self.title

class LoadedSpotifyTrack(PartiallyLoadedSong):
    def __init__(self, spotify_track_data: dict, loading_context: SongLoadingContext) -> None:
        self.title = spotify_track_data['name']
        self.duration = spotify_track_data['duration_ms']//1000

        self.random_value = random.randint(0, 10000)
        self.song_list = []
        self.loading_context = loading_context

        self.spotify_track_data = spotify_track_data

    def get_youtube_dl(self):
        title = f"{self.spotify_track_data['artists'][0]['name']} - {self.spotify_track_data['name']}"
        data = ytdl.extract_info(title, download=False)
        return LoadedYoutubeSong(data['entries'][0], self.loading_context, self.song_list, self.random_value)

    def __str__(self):
        return self.spotify_track_data['name']

class LoadedYoutubePlaylist:
    def __init__(self, youtube_playlist_snippets: list, title: str, loading_context: SongLoadingContext) -> None:
        self.youtube_playlist_snippets = youtube_playlist_snippets
        self.title = title
        self.loading_context = loading_context
        self.loading_context.parent_playlist = self
        self.total_count = len(youtube_playlist_snippets)
        self.count = 0
        self.error_count = 0
    def __str__(self) -> str:
        return self.title

class LoadedSpotifyAlbum:
    def __init__(self, spotify_album_data: dict, loading_context: SongLoadingContext) -> None:
        self.spotify_album_data = spotify_album_data
        self.loading_context = loading_context
        self.loading_context.parent_playlist = self
        self.total_count = len(spotify_album_data['tracks']['items'])
        self.count = 0
        self.error_count = 0
    def __str__(self):
        return self.spotify_album_data['name']

class LoadedSpotifyPlaylist:
    def __init__(self, spotify_playlist_data: dict, loading_context: SongLoadingContext) -> None:
        self.spotify_playlist_data = spotify_playlist_data
        self.loading_context = loading_context
        self.loading_context.parent_playlist = self
        self.total_count = len(spotify_playlist_data['tracks']['items'])
        self.count = 0
        self.error_count = 0
    def __str__(self):
        return self.spotify_playlist_data['name']
#endregion

#region Exceptions
class UserNotInVC(Exception): pass
class MusicAlreadyPlayingInGuild(Exception): pass
class CannotSpeakInVC(Exception): pass
class CannotConnectToVC(Exception): pass
class TriedPlayingWhenOutOfVC(Exception): pass
class NotPlaying(Exception): pass
#endregion

class iPod:
    def __init__(self, ctx):
        
        self.loaded_playlist = []
        self.loaded_queue = []

        self.partially_loaded_playlist = []
        self.partially_loaded_queue = []

        self.unloaded_playlist = []
        self.unloaded_queue = []

        self.past_songs_played = []

        self.shuffle = False
        self.loading_running = False
        self.preloading_running = False

        self.last_search = None
        self.last_context = None
        self.time_of_last_member = datetime.datetime.now(datetime.timezone.utc)
    
        music_players[ctx.guild.id] = self
        
        logger.info(f'iPod {self} created for {ctx.guild.name}')
        
    def loading_loop(self, ctx):
        logger.info('Loading loop started')
        self.loading_running = True
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.load_data_in_thread, ctx, unloaded_item, False): unloaded_item for unloaded_item in self.unloaded_playlist}

                for future in concurrent.futures.as_completed(futures):
                    unloaded_item = futures[future]
                    if unloaded_item in self.unloaded_playlist: del(self.unloaded_playlist[self.unloaded_playlist.index(unloaded_item)])
                    try: 
                        loaded_item = future.result()
                        self.on_load_succeed(ctx, unloaded_item, loaded_item, False)
                        self.distrubute_loaded_input(ctx, loaded_item, add_to_queue=False)
                    except Exception as e:
                        self.on_load_fail(ctx, unloaded_item, e)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.load_data_in_thread, ctx, unloaded_item, True): unloaded_item for unloaded_item in self.unloaded_queue}

                for future in concurrent.futures.as_completed(futures):
                    unloaded_item = futures[future]
                    if unloaded_item in self.unloaded_queue: del(self.unloaded_queue[self.unloaded_queue.index(unloaded_item)])
                    try: 
                        loaded_item = future.result()
                        self.on_load_succeed(ctx, unloaded_item, loaded_item, True)
                        self.distrubute_loaded_input(ctx, loaded_item, add_to_queue=True)
                    except Exception as e:
                        self.on_load_fail(ctx, unloaded_item, e)
            if len(self.unloaded_playlist) > 0 or len(self.unloaded_queue) > 0: self.loading_loop(ctx)
        except Exception as e:
            logger.error(f'Loading loop failed', exc_info=e)
        self.loading_running = False

    def preloading_loop(self, ctx):
        logger.info('Preloading loop started')
        self.preloading_running = True
        
        if self.shuffle: partially_loaded_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)  #FIXME please god fix this
        else: partially_loaded_playlist = self.partially_loaded_playlist

        partially_loaded_queue = self.partially_loaded_queue

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(partially_loaded_item.get_youtube_dl): partially_loaded_item for partially_loaded_item in partially_loaded_playlist[0:3]}

                for future in concurrent.futures.as_completed(futures):
                    partially_loaded_item = futures[future]
                    try:
                        if isinstance(partially_loaded_item, LoadedYoutubeSong):  #FIXME 403
                            self.on_preload_succeed(ctx, partially_loaded_item, partially_loaded_item, True)
                            continue
                        loaded_item = future.result()
                        try: self.partially_loaded_playlist[self.partially_loaded_playlist.index(partially_loaded_item)] = loaded_item
                        except ValueError: continue
                        self.on_preload_succeed(ctx, partially_loaded_item, loaded_item, False)
                    except Exception as e:
                        if partially_loaded_item in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(partially_loaded_item)])
                        self.on_load_fail(ctx, partially_loaded_item, e)
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(partially_loaded_item.get_youtube_dl): partially_loaded_item for partially_loaded_item in partially_loaded_queue[0:3]}

                for future in concurrent.futures.as_completed(futures):
                    partially_loaded_item = futures[future]
                    try:
                        if isinstance(partially_loaded_item, LoadedYoutubeSong):  #FIXME 403
                            self.on_preload_succeed(ctx, partially_loaded_item, partially_loaded_item, True)
                            continue
                        loaded_item = future.result()
                        try: self.partially_loaded_queue[self.partially_loaded_queue.index(partially_loaded_item)] = loaded_item 
                        except ValueError: continue
                        self.on_preload_succeed(ctx, partially_loaded_item, loaded_item, True)
                    except Exception as e:
                        if partially_loaded_item in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(partially_loaded_item)])
                        self.on_load_fail(ctx, partially_loaded_item, e)

            do_loop = False
            for item in partially_loaded_playlist[0:3]:  #FIXME 403
                if not isinstance(item, LoadedYoutubeSong):
                    do_loop = True
            for item in partially_loaded_queue[0:3]:
                if not isinstance(item, LoadedYoutubeSong):
                    do_loop = True
            if do_loop: self.preloading_loop(ctx)

        except Exception as e:
            logger.error(f'Preloading loop failed', exc_info=e)

        self.preloading_running = False

    #region "Buttons"
    def play(self, ctx: commands.Context, song: LoadedYoutubeSong, is_skip_backwards: bool):
        #Change player to this song
        logger.info(f'Playing {song}')
        try:
            if ctx.guild.voice_client == None: raise TriedPlayingWhenOutOfVC
            source = YTDLSource.from_url(YTDLSource, song.youtube_data, song, loop=bot.loop, stream=True)
            if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused():
                old_source =  ctx.guild.voice_client.source
                ctx.guild.voice_client.source = source
                self.on_song_end_succeed(ctx, old_source.loaded_song)
                if is_skip_backwards:
                    self.return_song_to_original_list(old_source.loaded_song)
                else:
                    self.add_song_to_play_history(old_source.loaded_song)
            else:
                ctx.guild.voice_client.play(source, after= lambda e: self.on_song_end_unknown(ctx, song, e))
            self.on_song_play(ctx, song)
        except Exception as e:
            self.on_start_play_fail(ctx, song, e)
 
    def play_next_item(self, ctx):
        #Play next item
        #Returns whether or not a new song was started
        if self.shuffle: partially_loaded_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)
        else: partially_loaded_playlist = self.partially_loaded_playlist


        if len(self.partially_loaded_queue) > 0 and isinstance(self.partially_loaded_queue[0], LoadedYoutubeSong):  #FIXME use self.is_valid_to_play() instead
            new_song = self.partially_loaded_queue[0]
            if new_song in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(new_song)])
            if new_song in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(new_song)])
            self.play(ctx, new_song, False)
            return True
        elif len(self.partially_loaded_playlist) > 0 and isinstance(partially_loaded_playlist[0], LoadedYoutubeSong):
            if self.shuffle:
                shuffled_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)
                new_song = shuffled_playlist[0]
                if new_song in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(new_song)])
                if new_song in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(new_song)])
                self.play(ctx, new_song, False)
                return True
            else:
                new_song = self.partially_loaded_playlist[0]
                if new_song in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(new_song)])
                if new_song in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(new_song)])
                self.play(ctx, new_song, False)
                return True
        else:
            if len(self.partially_loaded_queue) > 0 or len(self.partially_loaded_playlist) > 0:
                ctx.guild.voice_client.stop()
                if not self.preloading_running:
                    preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
                    preloading_thread.start()
        return False

    def play_previous_item(self, ctx):
        #Play next item
        #Returns whether or not a new song was started
        if len(self.past_songs_played) > 0:
            new_song = self.past_songs_played[0]
            if new_song in self.past_songs_played: del(self.past_songs_played[self.past_songs_played.index(new_song)])
            self.play(ctx, new_song, True)
            return True
        else:
            return False

    def play_next_if_nothing_playing(self, ctx):
        #Play next item if nothing is currently playing
        if ctx.guild.voice_client == None: raise TriedPlayingWhenOutOfVC
        if not ctx.guild.voice_client.is_playing() and not ctx.guild.voice_client.is_paused():
            if not self.play_next_item(ctx):
                if not self.preloading_running: 
                    preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
                    preloading_thread.start()
            
    def skip(self, ctx):
        #Skip a song
        if len(self.partially_loaded_playlist) > 0 or len(self.partially_loaded_queue) > 0:
            old_song = ctx.guild.voice_client.source
            self.play_next_item(ctx)
            new_song = ctx.guild.voice_client.source
            self.on_song_skip(ctx, old_song, new_song)
        else:
            old_song = ctx.guild.voice_client.source
            if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused(): ctx.guild.voice_client.stop()  #Stop current song
            new_song = None
            self.on_song_skip(ctx, old_song, new_song)

    def skip_backwards(self, ctx):
        #Skip a song backwards
        if len(self.past_songs_played) > 0:
            old_song = ctx.guild.voice_client.source
            self.play_previous_item(ctx)
            new_song = ctx.guild.voice_client.source
            self.on_song_skip_backwards(ctx, old_song, new_song)
        else:
            old_song = ctx.guild.voice_client.source
            new_song = None
            self.on_song_skip_backwards(ctx, old_song, new_song)

    def toggle_shuffle(self, ctx):
        if self.shuffle:
            self.shuffle = False
            self.on_shuffle_disable(ctx)
        else:
            self.shuffle = True
            self.reshuffle_list(self.partially_loaded_playlist)
            self.on_shuffle_enable(ctx)
        if not self.preloading_running:
            preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
            preloading_thread.start()

    def toggle_pause(self, ctx):
        if ctx.guild.voice_client == None or (not ctx.guild.voice_client.is_paused() and not ctx.guild.voice_client.is_playing()): raise NotPlaying
        if ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            self.on_pause_disable(ctx)
        else:
            ctx.guild.voice_client.pause()
            self.on_pause_enable(ctx)

    def disconnect(self, ctx, auto=False):
        if ctx.guild.voice_client == None: return
        bot.loop.create_task(ctx.guild.voice_client.disconnect())
        self.on_disconnect(ctx, auto)
    #endregion

    #region "USB cable" Yeah this anaology is falling apart a bit but whatever
    def receive_youtube_url(self, ctx, youtube_url: str, add_to_queue: bool = False, loading_context = None):  #Correctly process and call events for a youtube link. Below functions are similar
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedYoutubeSong(youtube_url, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSong(youtube_url, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_youtube_playlist_url(self, ctx, youtube_url: str, add_to_queue: bool = False, loading_context = None):
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedYoutubePlaylist(youtube_url, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubePlaylist(youtube_url, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_track_url(self, ctx, spotify_url: str, add_to_queue: bool = False, loading_context = None):
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedSpotifyTrack(spotify_url, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyTrack(spotify_url, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_album_url(self, ctx, spotify_album_url: str, add_to_queue: bool = False, loading_context = None):
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedSpotifyAlbum(spotify_album_url, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyAlbum(spotify_album_url, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_playlist_url(self, ctx, spotify_playlist_url: str, add_to_queue: bool = False, loading_context = None):
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_search_term(self, ctx, search_term: str, add_to_queue: bool = False, loading_context = None):
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = UnloadedYoutubeSearch(search_term, loading_context)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSearch(search_term, loading_context)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)
    #endregion
    
    #region Receive loaded
    def receive_loaded_youtube_data(self, ctx, loaded_song: LoadedYoutubeSong, add_to_queue: bool = False):
        if add_to_queue:
            self.partially_loaded_queue.append(loaded_song)
            loaded_song.song_list = self.partially_loaded_queue
            self.on_item_added_to_partially_loaded_queue(ctx, loaded_song)
        else:
            self.partially_loaded_playlist.append(loaded_song)
            loaded_song.song_list = self.partially_loaded_playlist
            self.on_item_added_to_partially_loaded_playlist(ctx, loaded_song)

    def receive_loaded_youtube_playlist(self, ctx, loaded_playlist: LoadedYoutubePlaylist, add_to_queue: bool = False):
        for snippet in loaded_playlist.youtube_playlist_snippets:
            self.receive_loaded_youtube_playlist_snippet(ctx, snippet, add_to_queue, loaded_playlist.loading_context)

    def receive_loaded_youtube_playlist_snippet(self, ctx, youtube_snippet: str, add_to_queue: bool = False, loading_context = None):  #Correctly process and call events for a youtube link. Below functions are similar
        if loading_context == None: loading_context = SongLoadingContext()
        if add_to_queue:
            new_item = LoadedYoutubePlaylistSong(youtube_snippet, loading_context)
            self.partially_loaded_queue.append(new_item)
            self.on_item_added_to_partially_loaded_queue(ctx, new_item)
        else:
            new_item = LoadedYoutubePlaylistSong(youtube_snippet, loading_context)
            self.partially_loaded_playlist.append(new_item)
            self.on_item_added_to_partially_loaded_playlist(ctx, new_item)

    def receive_loaded_spotify_track(self, ctx, loaded_track: LoadedSpotifyTrack, add_to_queue: bool = False):
        if add_to_queue:
            self.partially_loaded_queue.append(loaded_track)
            self.on_item_added_to_partially_loaded_queue(ctx, loaded_track)
        else:
            self.partially_loaded_playlist.append(loaded_track)
            self.on_item_added_to_partially_loaded_playlist(ctx, loaded_track)

    def receive_loaded_spotify_album(self, ctx, loaded_album: LoadedSpotifyAlbum, add_to_queue: bool = False):
        album = loaded_album.spotify_album_data
        for loaded_track in album['tracks']['items']:
            self.receive_loaded_spotify_track(ctx, LoadedSpotifyTrack(loaded_track, loaded_album.loading_context), add_to_queue)

    def receive_loaded_spotify_playlist(self, ctx, loaded_playlist: LoadedSpotifyPlaylist, add_to_queue: bool = False):
        playlist = loaded_playlist.spotify_playlist_data
        for loaded_track in [item['track'] for item in playlist['tracks']['items']]:
            self.receive_loaded_spotify_track(ctx, LoadedSpotifyTrack(loaded_track, loaded_playlist.loading_context), add_to_queue)
    #endregion
    
    #region Loaders
    def distrubute_loaded_input(self, ctx, loaded_item, add_to_queue):
        if isinstance(loaded_item, LoadedYoutubeSong):
            self.receive_loaded_youtube_data(ctx, loaded_item, add_to_queue)
        if isinstance(loaded_item, LoadedYoutubePlaylist):
            self.receive_loaded_youtube_playlist(ctx, loaded_item, add_to_queue)
        if isinstance(loaded_item, LoadedSpotifyTrack):
            self.receive_loaded_spotify_track(ctx, loaded_item, add_to_queue)
        if isinstance(loaded_item, LoadedSpotifyAlbum):
            self.receive_loaded_spotify_album(ctx, loaded_item, add_to_queue)
        if isinstance(loaded_item, LoadedSpotifyPlaylist):
            self.receive_loaded_spotify_playlist(ctx, loaded_item, add_to_queue)
        if not self.preloading_running: 
            preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
            preloading_thread.start()
            
    def process_input(self, ctx, input: str, add_to_queue: bool = False) -> None:  #Calls functions processing each type of supported link
        parsed_input = self.parse_input(input)
        for youtube_url in parsed_input['youtube_links']:
            self.receive_youtube_url(ctx, youtube_url, add_to_queue)
        for youtube_playlist_url in parsed_input['youtube_playlist_links']:
            self.receive_youtube_playlist_url(ctx, youtube_playlist_url, add_to_queue)
        for spotify_track_url in parsed_input['spotify_track_links']:
            self.receive_spotify_track_url(ctx, spotify_track_url, add_to_queue)
        for spotify_album_url in parsed_input['spotify_album_links']:
            self.receive_spotify_album_url(ctx, spotify_album_url, add_to_queue)
        for spotify_playlist_url in parsed_input['spotify_playlist_links']:
            self.receive_spotify_playlist_url(ctx, spotify_playlist_url, add_to_queue)
        for search_term in parsed_input['search_terms']:
            self.receive_search_term(ctx, search_term, add_to_queue)

    def parse_input(self, input: str) -> dict:
        output_dict = {'youtube_links' : [], 'youtube_playlist_links' : [], 'spotify_track_links' : [], 'spotify_album_links' : [], 'spotify_playlist_links' : [],'search_terms' : []}
        if input == "":
            return output_dict
        if input.startswith("www.") and not ((input.startswith("https://") or input.startswith("http://") or input.startswith("//"))):
            input = "//" + input
        parsed_url = urllib.parse.urlparse(input)
        website = parsed_url.netloc.removeprefix("www.").removesuffix(".com").removeprefix("open.")
        if website == "":
            try:
                input = int(input)
                if input <= 10 and input > 0 and self.last_search != None:
                    output_dict['youtube_links'].append(self.last_search[input-1]['link'])
                input = ''
            except ValueError:
                output_dict['search_terms'].append(input)
        elif website == "youtube":
            temp_dict = self.parse_youtube_link(parsed_url)
            output_dict.update(temp_dict)
        elif website == "youtu.be":
            temp_dict = self.handle_youtube_short_link(parsed_url) 
            output_dict.update(temp_dict)
        elif website == "spotify":
            temp_dict = self.handle_spotify_link(parsed_url)
            output_dict.update(temp_dict)
        return output_dict

    def parse_youtube_link(self, parsed_url):
        query = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)
        path = parsed_url.path
        if "v" in query:
            return {'youtube_links' : [f"https://www.youtube.com/watch?v={query['v'][0]}"]}
        elif "list" in query:
            return {'youtube_playlist_links' : [f"https://www.youtube.com/watch?list={query['list'][0]}"]}
        elif "url" in query:
            return {'youtube_links' : [query['url'][0]]}
        elif len(path) > 10:
            return {'youtube_links' : [f"https://www.youtube.com/watch?v={path[-11:]}"]}
        else:
            return {'search_terms' : [urllib.parse.urlunparse(parsed_url)]}

    def handle_youtube_short_link(self, parsed_url):
        path = parsed_url.path
        return {'youtube_links' : [f"https://www.youtube.com/watch?v={path[-11:]}"]}

    def handle_youtube_image_link(self, parsed_url):  #Doesn't work an I haven't tried to fix it
        return {'youtube_links' : [f"https://www.youtube.com/watch?v={parsed_url.path[4:15]}"]}  #FIXME

    def handle_spotify_link(self, parsed_url):
        url = urllib.parse.urlunparse(parsed_url)
        path = parsed_url.path
        if "playlist" in path:
            return {'spotify_playlist_links' : [url]}
        elif "track" in path:
            return {'spotify_track_links' : [url]}
        elif "album" in path:
            return {'spotify_album_links' : [url]}
        else:
            return {'search_terms' : [url]}

    def search_youtube(self, text_to_search, limit=10):
        search = VideosSearch(text_to_search, limit=limit)
        return search.result()['result']

    def reshuffle_list(self, playlist:list[PartiallyLoadedSong]):
        for song in playlist:
            song.random_value = random.randint(0, 10000)

    def load_data_in_thread(self, ctx, unloaded_item, add_to_queue = False):  #Blocking function to be called in a thread. Loads given input and returns constructed Loaded{Type} object
        if isinstance(unloaded_item, UnloadedYoutubeSong):
            data = self.load_youtube_url(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubeSong(data, unloaded_item.loading_context)
        elif isinstance(unloaded_item, UnloadedYoutubePlaylist):
            data, title = self.load_youtube_playlist_url(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubePlaylist(data, title, unloaded_item.loading_context)
        elif isinstance(unloaded_item, UnloadedSpotifyTrack):
            data = self.load_spotify_track_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyTrack(data, unloaded_item.loading_context)
        elif isinstance(unloaded_item, UnloadedSpotifyAlbum):
            data = self.load_spotify_album_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyAlbum(data, unloaded_item.loading_context)
        elif isinstance(unloaded_item, UnloadedSpotifyPlaylist):
            data = self.load_spotify_playlist_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyPlaylist(data, unloaded_item.loading_context)
        elif isinstance(unloaded_item, UnloadedYoutubeSearch):
            data = self.load_youtube_search(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubeSong(data, unloaded_item.loading_context)
        else:
            raise TypeError(unloaded_item)

    def run_youtube_multi_search_in_thread(self, ctx, search_term):
        items = self.search_youtube(search_term, 10)
        self.last_search = items
        self.on_search_complete(ctx, items)

    def load_youtube_url(self, ctx, unloaded_item: UnloadedYoutubeSong, add_to_queue = False) -> dict:  #Loads single youtube url and returns data dict
        if not isinstance(unloaded_item, UnloadedYoutubeSong): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        data = ytdl.extract_info(unloaded_item.youtube_url, download=False)
        return data

    def load_youtube_playlist_url(self, ctx, unloaded_item: UnloadedYoutubePlaylist, add_to_queue = False) -> list:  #Loads youtube playlist and returns list of youtube urls
        #extract playlist id from url
        if not isinstance(unloaded_item, UnloadedYoutubePlaylist): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        url = unloaded_item.youtube_playlist_url
        parsed_url = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)
        playlist_id = query["list"][0]

        request = yt.playlistItems().list(
            part = "snippet",
            playlistId = playlist_id,
            maxResults = 500
        )

        playlist_items = []
        while request is not None:
            response = request.execute()
            playlist_items += response["items"]
            request = yt.playlistItems().list_next(request, response)

        request = yt.playlists().list(
            part = "snippet",
            id = playlist_id,
            maxResults = 1
        )

        title_response = request.execute()

        return [t["snippet"] for t in playlist_items], title_response['items'][0]['snippet']['title'] 

    def load_spotify_track_url(self, ctx, unloaded_item: UnloadedSpotifyTrack, add_to_queue = False):  #Loads spotify track and returns track dict
        if not isinstance(unloaded_item, UnloadedSpotifyTrack): raise TypeError(unloaded_item)
        url = unloaded_item.spotify_track_url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        track = sp.track(url)
        return track

    def load_spotify_album_url(self, ctx, unloaded_item: UnloadedSpotifyAlbum, add_to_queue = False):  #Loads spotify album and returns album dict
        if not isinstance(unloaded_item, UnloadedSpotifyAlbum): raise TypeError(unloaded_item)
        url = unloaded_item.spotify_album_url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        album = sp.album(url)
        return album
    
    def load_spotify_playlist_url(self, ctx, unloaded_item: UnloadedSpotifyPlaylist, add_to_queue = False):  #Loads spotify playlist and returns playlist dict
        if not isinstance(unloaded_item, UnloadedSpotifyPlaylist): raise TypeError(unloaded_item)
        url = unloaded_item.spotify_playlist_url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        results = sp.playlist(url)
        tracks = results['tracks']
        while tracks['next']:
            tracks = sp.next(tracks)
            results['tracks']['items'].extend(tracks['items'])
        return results

    def load_youtube_search(self, ctx, unloaded_item: UnloadedYoutubeSearch, add_to_queue = False):  #Loads single youtube search and returns data dict
        if not isinstance(unloaded_item, UnloadedYoutubeSearch): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        data = ytdl.extract_info(unloaded_item.youtube_search, download=False)['entries'][0]
        return data
    #endregion
    
    #region Data processing
    def get_shuffle_number(self, loaded_youtube_song: LoadedYoutubeSong):
        return loaded_youtube_song.random_value

    def sort_for_shuffle(self, playlist:list[LoadedYoutubeSong]):
        new_list = playlist.copy()
        new_list.sort(key=self.get_shuffle_number)
        return new_list

    def get_formatted_playlist(self, list, page):
        index_length = 0
        for song in list[10*page: 10*(page + 1)]:
            if len(str(list.index(song) + 1)) > index_length: index_length = len(str(list.index(song) + 1))
        return [f'{self.get_consistent_length_index(list.index(song) + 1, index_length)} {self.get_consistent_length_title(song.title)}  {self.parse_duration(song.duration)}' for song in list[0 + (10*page): 10 + (10*page)]]
            
    def get_consistent_length_title(self, song_title):
        if len(song_title) < 35:
            song_title += ' '
            while len(song_title) < 35: song_title += '-'
        if len(song_title) > 35:
            song_title = song_title[0:34] + '…'
        return song_title

    def get_consistent_length_index(self, index, length):
        pos = f'{index})'
        while len(pos) < length + 1:
            pos = ' ' + pos
        return pos

    def parse_duration(self, duration):
        '''
        Converts a time, in seconds, to a string in the format hr:min:sec, or min:sec if less than one hour.
    
        @type  duration: int
        @param duration: The time, in seconds

        @rtype:   string
        @return:  The new time, hr:min:sec or min:sec
        '''

        #Divides everything into hours, minutes, and seconds
        hours = duration // 3600
        temp_time = duration % 3600 #Modulo takes the remainder of division, leaving the remaining minutes after all hours are taken out
        minutes = temp_time // 60
        seconds = temp_time % 60

        #Formats time into a readable string
        new_time = ""
        if hours > 0: #Adds hours to string if hours are available; else this will just be blank
            new_time += str(hours) + ":"

        if minutes > 0:
            if minutes < 10: #Adds a 0 to one-digit times
                new_time += "0" + str(minutes) + ":"
            else:
                new_time += str(minutes) +":"
        else: #If there are no minutes, the place still needs to be held
            new_time += "00:"

        if seconds > 0:
            if seconds < 10: #Adds a 0 to one-digit times
                new_time += "0" + str(seconds)
            else:
                new_time += str(seconds)
        else:
            new_time += "00"

        return new_time

    def clear_list(self, ctx, list_name):
        if list_name == 'both' or list_name == 'playlist': self.partially_loaded_playlist.clear()
        if list_name == 'both' or list_name == 'queue': self.partially_loaded_queue.clear()
        self.on_list_clear(ctx, list_name)

    def remove_item_from_list(self, ctx, list_name, song_list, loaded_song):
        index = song_list.index(loaded_song)
        del(song_list[index])
        self.on_remove_item_from_list(ctx, list_name, song_list, loaded_song)

    def move_items_between_lists(self, song_list, other_list, index_of_first_song, index_of_last_song, index_to_move_to):
        index_of_first_song = max(0, min(index_of_first_song, len(song_list) - 1))
        index_of_last_song = max(0, min(index_of_last_song, len(song_list) - 1))
        other_list[index_to_move_to:index_to_move_to] = song_list[index_of_first_song:index_of_last_song+1]
        for loaded_song in song_list[index_of_first_song:index_of_last_song+1]:
            loaded_song.song_list = other_list
        del(song_list[index_of_first_song:index_of_last_song+1])

    def add_song_to_play_history(self, loaded_song):
        self.past_songs_played.insert(0, loaded_song)

    def return_song_to_original_list(self, loaded_song):
        loaded_song.song_list.insert(0, loaded_song)

    #endregion

    #region Command Events
    def on_item_added_to_unloaded_queue(self, ctx, unloaded_item: UnloadedYoutubeSong):
        logger.info(f'Song added to unloaded queue event {unloaded_item}')
        if not self.loading_running: 
            loading_thread = threading.Thread(target=self.loading_loop, args=[ctx])
            loading_thread.start()

    def on_item_added_to_unloaded_playlist(self, ctx, unloaded_item: UnloadedYoutubeSong):
        logger.info(f'Song added to unloaded playlist event {unloaded_item}')
        if not self.loading_running: 
            loading_thread = threading.Thread(target=self.loading_loop, args=[ctx])
            loading_thread.start()

    def on_item_added_to_loaded_queue(self, ctx, loaded_item):
        logger.info(f'Song added to loaded queue event {loaded_item}')
        try: self.play_next_if_nothing_playing(ctx)
        except TriedPlayingWhenOutOfVC: return

    def on_item_added_to_loaded_playlist(self, ctx, loaded_item):
        logger.info(f'Song added to loaded playlist event {loaded_item}')
        try: self.play_next_if_nothing_playing(ctx)
        except TriedPlayingWhenOutOfVC: return

    def on_item_added_to_partially_loaded_queue(self, ctx, partially_loaded_item):
        logger.info(f'Song added to partially loaded queue event {partially_loaded_item}')
        

    def on_item_added_to_partially_loaded_playlist(self, ctx, partially_loaded_item):
        logger.info(f'Song added to partially loaded playlist event {partially_loaded_item}')
        

    async def on_play_command(self, ctx, input, add_to_queue=False):
        logger.info(f'Play command received')
        self.last_context = ctx
        try:
            await self.setup_vc(ctx)
            if len(input ) > 0: self.process_input(ctx, input, add_to_queue)
            else: 
                try: self.toggle_pause(ctx)
                except NotPlaying: 
                    self.play_next_item(ctx)
                    await self.on_nowplaying_command(ctx)
        except UserNotInVC as e:
            embed = discord.Embed(description='You need to join a vc!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except MusicAlreadyPlayingInGuild as e:
            embed = discord.Embed(description='Music is already playing somewhere else in this server!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotConnectToVC as e:
            embed = discord.Embed(description='I don\'t have access to that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotSpeakInVC as e:
            embed = discord.Embed(description='I don\'t have speak permissions in that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except asyncio.TimeoutError as e:
            embed = discord.Embed(description='Connection timed out.')
            embed.set_footer(text='Either the bot is running very slow, or Discord is having trouble.')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(f'Play command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_playlist_command(self, ctx, list, page):
        logger.info('Playlist command receive')
        self.last_context = ctx
        try:
            await self.respond_to_playlist_command(ctx, list, page)
        except Exception as e:
            logger.error(f'Playlist command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_skip_command(self, ctx):
        logger.info('Skip command receive')
        self.last_context = ctx
        try:
            await self.setup_vc(ctx)
            self.skip(ctx)
        except UserNotInVC as e:
            embed = discord.Embed(description='You need to join a vc!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except MusicAlreadyPlayingInGuild as e:
            embed = discord.Embed(description='Music is already playing somewhere else in this server!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotConnectToVC as e:
            embed = discord.Embed(description='I don\'t have access to that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotSpeakInVC as e:
            embed = discord.Embed(description='I don\'t have speak permissions in that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except asyncio.TimeoutError as e:
            embed = discord.Embed(description='Connection timed out.')
            embed.set_footer(text='Either the bot is running very slow, or Discord is having trouble.')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(f'Skip command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_skip_backwards_command(self, ctx):
        logger.info('Skip back command receive')
        self.last_context = ctx
        try:
            await self.setup_vc(ctx)
            self.skip_backwards(ctx)
        except UserNotInVC as e:
            embed = discord.Embed(description='You need to join a vc!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except MusicAlreadyPlayingInGuild as e:
            embed = discord.Embed(description='Music is already playing somewhere else in this server!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotConnectToVC as e:
            embed = discord.Embed(description='I don\'t have access to that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotSpeakInVC as e:
            embed = discord.Embed(description='I don\'t have speak permissions in that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except asyncio.TimeoutError as e:
            embed = discord.Embed(description='Connection timed out.')
            embed.set_footer(text='Either the bot is running very slow, or Discord is having trouble.')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(f'Skip back command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_shuffle_command(self, ctx):
        logger.info('Shuffle command receive')
        self.last_context = ctx
        try:
            self.toggle_shuffle(ctx)
        except Exception as e:
            logger.error(f'Shuffle command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_pause_command(self, ctx):
        logger.info('Pause command receive')
        self.last_context = ctx
        try:
            await self.setup_vc(ctx)
            self.toggle_pause(ctx)
        except NotPlaying as e:
            embed = discord.Embed(description='Play something first!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except UserNotInVC as e:
            embed = discord.Embed(description='You need to join a vc!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except MusicAlreadyPlayingInGuild as e:
            embed = discord.Embed(description='Music is already playing somewhere else in this server!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotConnectToVC as e:
            embed = discord.Embed(description='I don\'t have access to that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except CannotSpeakInVC as e:
            embed = discord.Embed(description='I don\'t have speak permissions in that voice channel!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except asyncio.TimeoutError as e:
            embed = discord.Embed(description='Connection timed out.')
            embed.set_footer(text='Either the bot is running very slow, or Discord is having trouble.')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(f'Pause command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_disconnect_command(self, ctx):
        logger.info('Disconnect command receive')
        self.last_context = ctx
        try:
            self.disconnect(ctx)
        except Exception as e:
            logger.error(f'Disconnect command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_search_command(self, ctx, search_term):
        logger.info('Search command receive')
        self.last_context = ctx
        thread = threading.Thread(target=self.run_youtube_multi_search_in_thread, args=(ctx, search_term))
        thread.start()

    async def on_nowplaying_command(self, ctx):
        logger.info('Now playing command receive')
        self.last_context = ctx
        try:
            embed = self.get_nowplaying_message_embed(ctx)
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except NotPlaying as e:
            logger.info(f'Nothing playing for now playing command')
            embed = discord.Embed(description='Play something first!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        except Exception as e:
            logger.error(f'Now playing command failed', exc_info=e)
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
    
    async def on_clear_command(self, ctx, list):
        logger.info('Clear command receive')
        self.last_context = ctx
        await self.respond_to_clear(ctx, list)

    async def on_remove_command(self, ctx, list_name, index):
        logger.info('Remove command receive')
        self.last_context = ctx
        if list_name == 'playlist': song_list = self.partially_loaded_playlist
        elif list_name == 'queue': song_list = self.partially_loaded_queue
        else: 
            embed = discord.Embed(description=f'List name must be `playlist` or `queue`, not `{list_name}`!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
            return
            
        if len(song_list) == 0:
            embed = discord.Embed(description=f'The {list_name} is empty!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        else:
            index = max(0, min(index, len(song_list) - 1))
            loaded_song = song_list[index]
            await self.respond_to_remove_command(ctx, list_name, song_list, loaded_song)

    async def on_move_command(self, ctx, song_list_name, index_of_first_song, index_of_last_song, index_to_move_to):
        logger.info('Move command receive')
        self.last_context = ctx
        if song_list_name == 'playlist': 
            song_list = self.partially_loaded_playlist
            other_list = self.partially_loaded_queue
            other_list_name = 'queue'
        elif song_list_name == 'queue': 
            song_list = self.partially_loaded_queue
            other_list = self.partially_loaded_playlist
            other_list_name = 'playlist'
        else: 
            embed = discord.Embed(description=f'List name must be `playlist` or `queue`, not `{song_list_name}`!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
            return
            
        if len(song_list) == 0:
            embed = discord.Embed(description=f'The {song_list_name} is empty!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        else:
            self.move_items_between_lists(song_list, other_list, index_of_first_song, index_of_last_song, index_to_move_to)
            if not self.preloading_running:
                preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
                preloading_thread.start()
            await self.respond_to_move(ctx, song_list_name, song_list, other_list_name, other_list, index_of_first_song, index_of_last_song, index_to_move_to)

    async def on_play_message_context(self, ctx, message, add_to_queue):
        logger.info('Play context command receive')
        if message.content == '':
            embed = discord.Embed(description='Message must have text')
            await ctx.respond(embed=embed)
        else:
            input = message.content
            await self.on_play_command(ctx, input, add_to_queue)

    async def on_search_message_context(self, ctx, message):
        logger.info('Search context command receive')
        if message.content == '':
            embed = discord.Embed(description='Message must have text')
            await ctx.respond(embed=embed)
        else:
            search_term = message.content
            await self.on_search_command(ctx, search_term)

    async def on_clear_button(self, interaction, list_name):
        ctx = await bot.get_context(interaction.message)
        self.clear_list(ctx, list_name)
        embed = discord.Embed(description=f'Cleared all songs from {"playlist and queue" if list_name == "both" else list_name}', color=8180120)
        await interaction.message.edit(embed=embed, view=None)

    async def on_remove_button(self, interaction, list_name, song_list, loaded_song):
        try:
            ctx = await bot.get_context(interaction.message)
            self.remove_item_from_list(ctx, list_name, song_list, loaded_song)
            embed = discord.Embed(description=f'Removed `{loaded_song}` from {list_name}', color=8180120)
        except ValueError: 
            embed = discord.Embed(description=f'{loaded_song} is not in {list_name}', color=16741747)
        await interaction.message.edit(embed=embed, view=None)
    #endregion

    #region Buttons
    class ClearCommandYesButton(discord.ui.Button):
        def __init__(self, iPod, list_name):
            self.iPod = iPod
            self.list_name = list_name
            super().__init__(style=discord.enums.ButtonStyle.danger, label='Clear')

        async def callback(self, interaction: discord.Interaction):
            await self.iPod.on_clear_button(interaction, self.list_name)
            
    class ClearCommandNoButton(discord.ui.Button):
        def __init__(self, iPod, list):
            self.iPod = iPod
            self.list = list
            super().__init__(style=discord.enums.ButtonStyle.gray, label='Cancel')

        async def callback(self, interaction: discord.Interaction):
            await interaction.message.delete()

    class RemoveCommandYesButton(discord.ui.Button):
        def __init__(self, iPod, list_name, song_list, loaded_song):
            self.iPod = iPod
            self.list_name = list_name
            self.song_list: list = song_list
            self.loaded_song = loaded_song
            super().__init__(style=discord.enums.ButtonStyle.danger, label='Remove')

        async def callback(self, interaction: discord.Interaction):
            await self.iPod.on_remove_button(interaction, self.list_name, self.song_list, self.loaded_song)

    class RemoveCommandNoButton(discord.ui.Button):
        def __init__(self, iPod, list_name, song_list, loaded_song):
            self.iPod = iPod
            self.list_name = list_name
            self.song_list = song_list
            self.loaded_song = loaded_song
            super().__init__(style=discord.enums.ButtonStyle.gray, label='Cancel')

        async def callback(self, interaction: discord.Interaction):
            await interaction.message.delete()
    #endregion
    
    #region Internal events
    def on_load_fail(self, ctx, unloaded_item, exception):
        if isinstance(exception, youtube_dl.utils.DownloadError) and exception.args[0] == 'ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.':
            logger.info(f'Age restricted video {unloaded_item} cannot be loaded')
            if unloaded_item.loading_context.parent_playlist != None: unloaded_item.loading_context.parent_playlist.error_count += 1
            bot.loop.create_task(self.respond_to_load_error(ctx, unloaded_item, message='Video is age restricted'))
        else:
            logger.error(f'Failed loading item {unloaded_item}', exc_info=exception)
            if unloaded_item.loading_context.parent_playlist != None: unloaded_item.loading_context.parent_playlist.error_count += 1
            bot.loop.create_task(self.respond_to_load_error(ctx, unloaded_item, exception))

    def on_load_start(self, ctx, unloaded_item, add_to_queue):
        logger.info(f'Started loading item {unloaded_item}')
        bot.loop.create_task(self.respond_to_add_unloaded_item(ctx, unloaded_item))

    def on_load_succeed(self, ctx, unloaded_item, loaded_item, add_to_queue):
        logger.info(f'Succeeded loading item {unloaded_item} into {loaded_item}')
        #if loaded_item.loading_context.parent_playlist != None and loaded_item.loading_context.parent_playlist != loaded_item and isinstance(loaded_item, LoadedYoutubeSong): loaded_item.loading_context.parent_playlist.count += 1
        bot.loop.create_task(self.respond_to_load_item(ctx, loaded_item, add_to_queue))

    def on_preload_succeed(self, ctx, unloaded_item, loaded_item, add_to_queue):
        logger.info(f'Succeeded preloading item {unloaded_item} into {loaded_item}')
        try: self.play_next_if_nothing_playing(ctx)
        except TriedPlayingWhenOutOfVC: return
        #if loaded_item.loading_context.parent_playlist != None and loaded_item.loading_context.parent_playlist != loaded_item and isinstance(loaded_item, LoadedYoutubeSong): loaded_item.loading_context.parent_playlist.count += 1
        #bot.loop.create_task(self.respond_to_load_item(ctx, loaded_item, add_to_queue))

    def on_vc_connect(self, ctx, channel):
        logger.info(f'Connected to channel {channel}')
        
    def on_song_play(self, ctx, new_song: LoadedYoutubeSong):
        logger.info(f'Song play succeed {new_song}')

    def on_start_play_fail(self, ctx, new_song: LoadedYoutubeSong, exception):
        logger.error(f'Song play fail {new_song}', exc_info=exception)

    def on_during_play_fail(self, ctx, song: LoadedYoutubeSong, exception):
        logger.error(f'Play failed during song {song}', exc_info=exception)
        if not self.preloading_running:
            preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
            preloading_thread.start()

    def on_song_end_unknown(self, ctx, song, exception=None):
        #When a song ends due to an unknown cause, either an exception or the song completed
        if exception == None:
            self.on_song_end_succeed(ctx, song)
            self.add_song_to_play_history(song)
            self.play_next_item(ctx)
        else:
            self.on_during_play_fail(ctx, song, exception)
            self.play_next_item(ctx)

    def on_song_end_succeed(self, ctx, song):
        logger.info('Song ended')
        if not self.preloading_running:
            preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
            preloading_thread.start()

    def on_shuffle_enable(self, ctx):
        logger.info('Shuffle on')
        bot.loop.create_task(self.respond_to_shuffle_enable(ctx))

    def on_shuffle_disable(self, ctx):
        logger.info('Shuffle off')
        bot.loop.create_task(self.respond_to_shuffle_disable(ctx))

    def on_pause_enable(self, ctx):
        logger.info('Pause on')
        bot.loop.create_task(self.respond_to_pause_enable(ctx))

    def on_pause_disable(self, ctx):
        logger.info('Pause off')
        bot.loop.create_task(self.respond_to_pause_disable(ctx))

    def on_disconnect(self, ctx, auto):
        logger.info('Disconnect')
        bot.loop.create_task(self.respond_to_disconnect(ctx, auto))

    def on_search_complete(self, ctx, items):
        logger.info('Search complete')
        bot.loop.create_task(self.respond_to_search(ctx, items))

    def on_song_skip(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        logger.info('Song skipped')
        bot.loop.create_task(self.respond_to_skip(ctx, old_song, new_song))

    def on_song_skip_backwards(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        logger.info('Song skipped back')
        bot.loop.create_task(self.respond_to_skip_backwards(ctx, old_song, new_song))
    
    def on_list_clear(self, ctx, list_name):
        logger.info(f'{list_name} cleared')

    def on_remove_item_from_list(self, ctx, list_name, song_list, loaded_song):
        logger.info(f'Removed {loaded_song} from {list_name}')
    #endregion

    #region Discord VC support
    async def setup_vc(self, ctx: commands.Context):  #Attempts to set up VC. Runs any associated events and sends any error messages
        #FIXME Don't error if already in the requested vc regardless of perms
        if ctx.author.voice == None: 
            raise UserNotInVC
        if not ctx.author.voice.channel.permissions_for(ctx.guild.me).connect:
            raise CannotConnectToVC
        if not ctx.author.voice.channel.permissions_for(ctx.guild.me).speak:
            raise CannotSpeakInVC
        elif ctx.guild.voice_client == None: 
            await ctx.author.voice.channel.connect(timeout=5)
            self.on_vc_connect(ctx, ctx.author.voice.channel)
        elif ctx.guild.voice_client.channel == ctx.author.voice.channel: 
            return
        elif self.should_change_vc(ctx): 
            await ctx.guild.voice_client.disconnect()
            await ctx.author.voice.channel.connect(timeout=5)
            self.on_vc_connect(ctx, ctx.author.voice.channel)
        else: 
            raise MusicAlreadyPlayingInGuild

    def should_change_vc(self, ctx):
        return not (ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused())
    #endregion

    #region Discord interactions
    async def respond_to_add_unloaded_item(self, ctx, item_added):
        embed = discord.Embed(description=f'Loading {item_added}...')
        await item_added.loading_context.send_message(ctx, embed)

    async def respond_to_load_error(self, ctx, item_added, exception=None, message=None):
        if exception != None:
            embed = discord.Embed(description=f'{item_added} failed to load with error: {exception}{f", message: {message}" if message != None else ""}')
            embed.color = 16741747
        elif message != None:
            embed = discord.Embed(description=f'{item_added} failed to load. {message}')
            embed.color = 16741747
        else:
            embed = discord.Embed(description=f'{item_added} failed to load due to an unknown error.')
            embed.color = 16741747
        await ctx.send(embed=embed)

    async def respond_to_load_item(self, ctx, item_loaded, add_to_queue):
        if isinstance(item_loaded, LoadedYoutubePlaylist) or isinstance(item_loaded, LoadedSpotifyAlbum) or isinstance(item_loaded, LoadedSpotifyPlaylist): 
            embed = discord.Embed(description=f'Successfully added {item_loaded.total_count} songs to {"queue" if add_to_queue else "playlist"}')
            embed.color = 7528669
        else:
            embed = discord.Embed(description=f'Successfully added {item_loaded} to {"queue" if add_to_queue else "playlist"}')
            embed.color = 7528669
        await item_loaded.loading_context.send_message(ctx, embed)
        
    async def respond_to_playlist_command(self, ctx, list, page):
        embed_to_send = self.compile_playlist(list, page)
        try: await ctx.reply(embed=embed_to_send, mention_author=False)
        except: await ctx.respond(embed=embed_to_send)

    async def respond_to_shuffle_enable(self, ctx):
        embed = discord.Embed(description='Shuffle enabled', color=3093080)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)
        if len(self.partially_loaded_queue) > len(self.partially_loaded_playlist):
            embed = discord.Embed(description='You seem to have most of your songs in the queue. Songs in the queue are not effected by shuffle. To add songs to the playlist, use `/add {song}` ~~If you want to move existing songs to the playlist and use shuffle, use `/move queue all`~~ NOT IMPLEMENTED YET', color=3093080)  #FIXME
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def respond_to_shuffle_disable(self, ctx):
        embed = discord.Embed(description='Shuffle disabled', color=3093080)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_pause_enable(self, ctx):
        embed = discord.Embed(description='Paused music', color=3093080)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_pause_disable(self, ctx):
        embed = discord.Embed(description='Unpaused msuic', color=3093080)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_disconnect(self, ctx, auto):
        embed = discord.Embed(description='Leaving voice chat', color=3093080)
        if not auto:
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
        else:
            await ctx.send(embed=embed)

    async def respond_to_search(self, ctx, items):
        embed = self.get_search_message_embed(items)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_nowplaying(self, ctx):
        embed = self.get_nowplaying_message_embed()
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_skip(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        embed = self.get_skip_message_embed(old_song, new_song)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_skip_backwards(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        embed = self.get_skip_backward_message_embed(old_song, new_song)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)
    
    async def respond_to_clear(self, ctx, list):
        view = discord.ui.View()
        view.add_item(self.ClearCommandNoButton(self, list))
        view.add_item(self.ClearCommandYesButton(self, list))
        embed = discord.Embed(description=f'Are you sure you want to clear the {"playlist and queue" if list == "both" else list}?', color=16741747)
        try: await ctx.reply(embed=embed, view=view, mention_author=False)
        except: await ctx.respond(embed=embed, view=view)

    async def respond_to_remove_command(self, ctx, list_name, song_list, loaded_song):
        view = discord.ui.View()
        view.add_item(self.RemoveCommandNoButton(self, list_name, song_list, loaded_song))
        view.add_item(self.RemoveCommandYesButton(self, list_name, song_list, loaded_song))
        embed = discord.Embed(description=f'Are you sure you want to remove `{loaded_song}` from the {list_name}?', color=16741747)
        try: await ctx.reply(embed=embed, view=view, mention_author=False)
        except: await ctx.respond(embed=embed, view=view)

    async def respond_to_move(self, ctx, song_list_name, song_list, other_list_name, other_list, index_of_first_song, index_of_last_song, index_to_move_to):
        embed = self.get_move_embed(song_list_name, song_list, other_list_name, other_list, index_of_first_song, index_of_last_song, index_to_move_to)
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)
    #endregion

    #region Message contructors
    def compile_playlist(self, list: str, page=0) -> discord.Embed:
        if list != 'both' and list != 'playlist' and list != 'queue' and list != 'history': raise ValueError(list)
        #Set lists of strings
        if self.shuffle:
            shuffled_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)
            playlist_title_list = self.get_formatted_playlist(shuffled_playlist, page)
        else:
            playlist_title_list = self.get_formatted_playlist(self.partially_loaded_playlist, page)
        queue_title_list = self.get_formatted_playlist(self.partially_loaded_queue, page)
        history_title_list = self.get_formatted_playlist(self.past_songs_played, page)
        #Max page numbers (For footer)
        max_page_queue = max((len(self.partially_loaded_queue) - 1)//10, 0)
        max_page_playlist = max((len(self.partially_loaded_playlist) - 1)//10, 0)
        max_page_history = max((len(self.past_songs_played) - 1)//10, 0)
        #Do the title
        if list == 'both': title= 'Upcoming Queue/Playlist'
        elif list == 'queue': title= 'Upcoming Queue'
        elif list == 'playlist': title= f'Upcoming Playlist{f" (will play after {len(self.partially_loaded_queue)} songs currently in queue)" if len(self.partially_loaded_queue) > 0 else ""}'
        elif list == 'history': title= f'Song History (sorted by most recent first)'
        #Do the footer
        if list == 'both': footer=f'Page {min(page+1, max(max_page_playlist, max_page_queue) + 1)} of {max(max_page_playlist, max_page_queue) + 1}'
        elif list == 'queue': footer=f'Page {min(page+1, max_page_queue + 1)} of {max_page_queue + 1}'
        elif list == 'playlist': footer=f'Page {min(page+1, max_page_playlist + 1)} of {max_page_playlist + 1}'
        elif list == 'history': footer=f'Page {min(page+1, max_page_history + 1)} of {max_page_history + 1}'
        #Do the main content
        description = ''
        if list == 'both': description += 'Queue:\n'
        if list == 'both' or list == 'queue':
            if len(queue_title_list) > 0: description += ('```\n' + '\n'.join(queue_title_list) + '```\n')
            elif len(self.partially_loaded_queue) > 0: description += '`There is nothing on this page of the queue`\n'
            else: description += '`The queue is empty`\n'
        if list == 'both': description += '\nPlaylist:\n'
        if list == 'both' or list == 'playlist': 
            if len(playlist_title_list) > 0: description += ('```\n' + '\n'.join(playlist_title_list) + '```\n')
            elif len(self.partially_loaded_playlist) > 0: description += '`There is nothing on this page of the playlist`\n'
            else: description += '`Playlist is empty`\n'
        if list == 'history': 
            if len(history_title_list) > 0: description += ('```\n' + '\n'.join(history_title_list) + '```\n')
            elif len(self.past_songs_played) > 0: description += '`There is nothing on this page of the play history`\n'
            else: description += '`Play history is empty`\n'
        #Make embed for real
        embed = discord.Embed(title=title, description=description, color=3093080)
        embed.set_footer(text=footer)
        return embed

    def get_search_message_embed(self, items):
        joined_string = '\n'.join(
            [f"{items.index(item) + 1}) {item['title']} -------- {item['duration']}"
            for item in items]
            )
        embed = discord.Embed(description=joined_string, color=9471113)
        embed.set_footer(text='Use /play {number} to play one of these songs')
        return embed

    def get_nowplaying_message_embed(self, ctx):
        if ctx.guild.voice_client == None or (not ctx.guild.voice_client.is_paused() and not ctx.guild.voice_client.is_playing()): raise NotPlaying
        embed = discord.Embed(title='Now Playing ♫', description=ctx.guild.voice_client.source.title, color=7528669)
        return embed

    def get_skip_message_embed(self, old_song: YTDLSource, new_song: YTDLSource):
        if new_song == None: 
            embed = discord.Embed(title='No more songs to play!', description='Add more with /play or /add!', color=7528669)
            if old_song != None:
                embed.set_footer(text=f'Skipped {old_song.title}')
        else: 
            embed = discord.Embed(title='Now Playing', description=new_song.title, color=7528669)
            embed.set_footer(text=f'Skipped {old_song.title}')
        return embed

    def get_skip_backward_message_embed(self, old_song: YTDLSource, new_song: YTDLSource):
        if new_song == None: 
            embed = discord.Embed(description='Nothing in the play history', color=7528669)
        else: 
            embed = discord.Embed(title='Now Playing', description=new_song.title, color=7528669)
        return embed

    def get_move_embed(self, song_list_name, song_list, other_list_name, other_list, index_of_first_song, index_of_last_song, index_to_move_to):
        moved_songs = index_of_last_song+1 - index_of_first_song
        embed = discord.Embed(description=f'Moved {moved_songs} songs from {song_list_name} to {other_list_name}')
        return embed
    #endregion

class Groovy(commands.Cog):
    def __init__(self):
        self.voice_channel_leave.start()

    @tasks.loop(minutes=1)
    async def voice_channel_leave(self):
        music_players_copy = music_players.copy()
        players: list[iPod] = music_players_copy.values()
        for player in players:
            guild = await bot.fetch_guild(player.last_context.guild.id)
            if guild.voice_client != None: 
                vc = guild.voice_client.channel
                if len(vc.members) > 1:
                    player.time_of_last_member = datetime.datetime.now(datetime.timezone.utc)
                    logger.info('Users in voice channel, updating time')
                else:
                    if (datetime.datetime.now(datetime.timezone.utc) - player.time_of_last_member).total_seconds() > 3:
                        logger.info('Nobody in voice channel for time limit, disconnecting...')
                        player.disconnect(player.last_context, True)

    @voice_channel_leave.before_loop
    async def before_vc(self):
        logger.info("Starting voice channel loop...")
        await bot.wait_until_ready()

    def get_player(self, ctx) -> iPod:
        if ctx.guild.id in music_players.keys():
            return music_players[ctx.guild.id]
        else:
            return iPod(ctx)

    #region Commands
    @commands.command(name='play', aliases=['p'], description='Add a song to the queue')
    async def prefix_play(self, ctx, input: str = '', *more_words):
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, True)

    @commands.slash_command(name='play', description='Add a song to the queue')
    async def slash_play(self, ctx: discord.ApplicationContext, input: Option(discord.enums.SlashCommandOptionType.string, description='A link or search term', required=False, default='')):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, True)

    @commands.command(name='add', aliases=['a'], description='Add a song to the playlist')
    async def prefix_add(self, ctx, input: str = '', *more_words):
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, False)

    @commands.slash_command(name='add', description='Add a song to the playlist')
    async def slash_add(self, ctx, input: Option(discord.enums.SlashCommandOptionType.string, description='A link or search term', required=False, default='')):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, False)

    @commands.command(name='skip', aliases=['s', 'sk'], description='Skip the current song!')
    async def prefix_skip(self, ctx):
        player = self.get_player(ctx)
        await player.on_skip_command(ctx)

    @commands.slash_command(name='skip', description='Skip the current song!')
    async def slash_skip(self, ctx):
        player = self.get_player(ctx)
        await player.on_skip_command(ctx)

    @commands.command(name='skipback', aliases=['sb', 'b'], description='Skip back to past songs!')
    async def prefix_skipback(self, ctx):
        player = self.get_player(ctx)
        await player.on_skip_backwards_command(ctx)

    @commands.slash_command(name='skipback', description='Skip back to past songs!')
    async def slash_skipback(self, ctx):
        player = self.get_player(ctx)
        await player.on_skip_backwards_command(ctx)
        
    @commands.command(name='playlist', aliases=['pl'], description='Show playlist/queue')
    async def prefix_playlist(self, ctx, list='both', page='1'):
        if list.lower().startswith('p'): list = 'playlist'
        if list.lower().startswith('q'): list = 'queue'
        if list.lower().startswith('h'): list = 'history'
        if list != 'both' and list != 'playlist' and list != 'queue' and list != 'history': list = 'both'
        try: page = max(0, int(page)-1)
        except ValueError: page = 0
        player = self.get_player(ctx)
        await player.on_playlist_command(ctx, list, page)

    @commands.slash_command(name='playlist', description='Show playlist/queue')
    async def slash_playlist(self, ctx, 
    list: Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Show playlist', 'playlist'), OptionChoice('Show queue', 'queue')], required=False, default='both'), 
    page: Option(discord.enums.SlashCommandOptionType.integer, description='Specify page number', required=False, default=1, min_value=1)
    ):
        player = self.get_player(ctx)
        await player.on_playlist_command(ctx, list, page)

    @commands.command(name='shuffle', aliases=['sh'], description='Toggle shuffle mode')
    async def prefix_shuffle(self, ctx):
        player = self.get_player(ctx)
        await player.on_shuffle_command(ctx)

    @commands.slash_command(name='shuffle', description='Toggle shuffle mode')
    async def slash_shuffle(self, ctx):
        player = self.get_player(ctx)
        await player.on_shuffle_command(ctx)

    @commands.command(name='pause', description='Toggle pause')
    async def prefix_pause(self, ctx):
        player = self.get_player(ctx)
        await player.on_pause_command(ctx)

    @commands.slash_command(name='pause', description='Toggle pause')
    async def slash_pause(self, ctx):
        player = self.get_player(ctx)
        await player.on_pause_command(ctx)

    @commands.command(name='disconnect', aliases=['dc', 'dis'], description='Leave VC')
    async def prefix_disconnect(self, ctx):
        player = self.get_player(ctx)
        await player.on_disconnect_command(ctx)

    @commands.slash_command(name='disconnect', description='Leave VC')
    async def slash_disconnect(self, ctx):
        player = self.get_player(ctx)
        await player.on_disconnect_command(ctx)

    @commands.command(name='search', aliases=['sch'], description='Search something on YouTube and get a list of results')
    async def prefix_search(self, ctx, input: str = 'music', *more_words):
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_search_command(ctx, input)

    @commands.slash_command(name='search', description='Search something on YouTube and get a list of results')
    async def slash_search(self, ctx, input: Option(str, description='A search term', required=True)):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_search_command(ctx, input)

    @commands.command(name="nowplaying", aliases=['np'], description="Show the now playing song")
    async def np(self, ctx):
        player = self.get_player(ctx)
        await player.on_nowplaying_command(ctx)

    @commands.slash_command(name="nowplaying", description="Show the now playing song")
    async def slash_np(self, ctx):
        player = self.get_player(ctx)
        await player.on_nowplaying_command(ctx)
    
    @commands.command(name="clear", aliases=['c'], description="Clear the playlist/queue")
    async def prefix_clear(self, ctx, list='both'):
        player = self.get_player(ctx)
        if list.lower().startswith('p'): list = 'playlist'
        if list.lower().startswith('q'): list = 'queue'
        if list != 'both' and list != 'playlist' and list != 'queue': list = 'both'
        await player.on_clear_command(ctx, list)

    @commands.slash_command(name="clear", description="Clear the playlist/queue")
    async def slash_clear(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Clear playlist', 'playlist'), OptionChoice('Clear queue', 'queue')], required=False, default='both')):
        player = self.get_player(ctx)
        await player.on_clear_command(ctx, list)

    @commands.command(name="remove", aliases=['r', 'rm'], description="Clear the playlist/queue")
    async def prefix_remove(self, ctx, list='', index='1'):
        player = self.get_player(ctx)
        if list.lower().startswith('p'): list = 'playlist'
        if list.lower().startswith('q'): list = 'queue'
        try: index = max(0, int(index)-1)
        except ValueError: index = 0
        await player.on_remove_command(ctx, list, index)

    @commands.slash_command(name="remove", description="Clear the playlist/queue")
    async def slash_remove(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Remove song from playlist', 'playlist'), OptionChoice('Remove song from queue', 'queue')], required=True), 
    index:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the song to remove', required=True, min_value=1)):
        player = self.get_player(ctx)
        await player.on_remove_command(ctx, list, index)

    @commands.command(name="move", aliases=['m', 'mv'], description="Move a song between playlist and queue")
    async def prefix_move(self, ctx, song_list_list='', index_of_first_song='1', index_of_last_song=None, index_to_move_to='1'):
        player = self.get_player(ctx)
        if song_list_list.lower().startswith('p'): song_list_list = 'playlist'
        if song_list_list.lower().startswith('q'): song_list_list = 'queue'

        try: index_of_first_song = max(0, int(index_of_first_song)-1)
        except ValueError: index_of_first_song = 0
        try: index_of_last_song = max(index_of_first_song, int(index_of_last_song)-1)
        except ValueError: index_of_last_song = index_of_first_song
        try: index_to_move_to = max(0, int(index_to_move_to)-1)
        except ValueError: index_to_move_to = 0

        await player.on_move_command(ctx, song_list_list, index_of_first_song, index_of_last_song, index_to_move_to)

    @commands.slash_command(name="move", description="Move a song between playlist and queue")
    async def slash_move(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Move song from playlist', 'playlist'), OptionChoice('Move song from queue', 'queue')], required=True), 
    index_to_start:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the first song to move', required=True, min_value=1),
    index_to_end:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the last song to move', required=True, min_value=1),
    index_to_move_to:Option(discord.enums.SlashCommandOptionType.integer, description='Where to put the songs in the other list', required=False, default=1, min_value=1)):
        player = self.get_player(ctx)
        await player.on_move_command(ctx, list, index_to_start, index_to_end, index_to_move_to)

    # @commands.message_command(name='play')
    # async def context_play(self, ctx, message: discord.Message):
    #     await ctx.defer()
    #     player = self.get_player(ctx)
    #     await player.on_play_message_context(ctx, message, True)

    # @commands.message_command(name='add')
    # async def context_add(self, ctx, message: discord.Message):
    #     await ctx.defer()
    #     player = self.get_player(ctx)
    #     await player.on_play_message_context(ctx, message, False)

    # @commands.message_command(name='search')
    # async def context_search(self, ctx, message: discord.Message):
    #     await ctx.defer()
    #     player = self.get_player(ctx)
    #     await player.on_search_message_context(ctx, message)
        
    #endregion
        




