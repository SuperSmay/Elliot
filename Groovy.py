import asyncio
import concurrent.futures
import datetime
import logging
import os
import pathlib
import random
import re
import threading
import urllib.parse
from difflib import SequenceMatcher
from typing import Literal

import discord
import googleapiclient.discovery
import lyricsgenius
import requests
import spotipy
import youtube_dl
from discord.commands import Option, OptionChoice, SlashCommandGroup
from discord.ext import commands, tasks
from dotenv import load_dotenv
from youtubesearchpython import VideosSearch

import String_Progress_Bar
from GlobalVariables import bot, on_log
from Settings import fetch_setting, set_setting
from Statistics import log_event

##TODO List
    ## Youtube-DL simple youtube links ✓
    ## Rearrange ✓
    ## Split youtube playlists ✓
    ## Convert simple spotify tracks ✓
    ## Split spotify playlists and albums ✓
    ## Play youtube-dl'd input correctly ✓
    ## Add command ✓
    ## Skip command ✓
    ## Playlist command (Properly this time) ✓
    ## Skip backwards command ✓
    ## Play history (Youtube link or dl'd dict?) ✓
    ## Message on new song start option ✓
    ## Guess the song?
    ## Karaoke mode?

##

#region Variables and setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addFilter(on_log)

load_dotenv()

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

client_id = os.environ.get('SPOTIFY_ID')
client_secret = os.environ.get('SPOTIFY_SECRET')
client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager) #spotify object to access API

youtube_key = os.environ.get('YOUTUBE_API_KEY')
yt = googleapiclient.discovery.build("youtube", "v3", developerKey=youtube_key)

genius_token = os.environ.get('GENIUS_TOKEN')
genius = lyricsgenius.Genius(genius_token, verbose=False, remove_section_headers=True)

music_players = {}

def setup(bot):
    bot.add_cog(Groovy())
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

class GameMember:
    def __init__(self, member: discord.Member) -> None:
        self.id = member.id
        self.name = member.display_name
        self.score = 0
#region Song Classes
class UnloadedSong:
    def __init__(self, url, loading_context: SongLoadingContext) -> None:
        self.url = url
        self.loading_context = loading_context
    def __str__(self):
        return self.url

class UnloadedYoutubeSong(UnloadedSong): pass

class UnloadedYoutubePlaylist(UnloadedSong): pass

class UnloadedYoutubeSearch(UnloadedSong): pass

class UnloadedSpotifyTrack(UnloadedSong): pass

class UnloadedSpotifyAlbum(UnloadedSong): pass

class UnloadedSpotifyPlaylist(UnloadedSong): pass


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

        self.title_from_spotify = None
        self.artist_from_spotify = None

        self.loading_context = loading_context
        self.random_value = random.randint(0, 10000) if random_value == None else random_value
        self.song_list = song_list if song_list == None else []

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
        loaded_song = LoadedYoutubeSong(data['entries'][0], self.loading_context, self.song_list, self.random_value)
        loaded_song.title_from_spotify = self.spotify_track_data['name']
        loaded_song.artist_from_spotify = self.spotify_track_data['artists'][0]['name']
        return loaded_song

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

        self.partially_loaded_playlist = []
        self.partially_loaded_queue = []

        self.unloaded_playlist = []
        self.unloaded_queue = []

        self.past_songs_played = []

        self.game_scoreboard = {}

        self.loading_running = False
        self.preloading_running = False

        self.can_guess = True
        self.give_up_pending = False
        self.seconds_until_give_up = 0

        self.time_of_last_song_start = datetime.datetime.now(datetime.timezone.utc)
        self.last_search = None
        self.last_context = None
        self.time_of_last_member = datetime.datetime.now(datetime.timezone.utc)
    
        music_players[ctx.guild.id] = self
        
        logger.info(f'iPod {self} created for {ctx.guild.name}')


        
    def loading_loop(self, ctx):
        '''
        Loops through the unloaded lists and loads any songs

        Parameters:
            - `ctx`: discord.commands.Context; The context for the load

        
        '''
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
            logger.error(f'Loading loop failed', exc_info=True)
        
        self.loading_running = False

    def preloading_loop(self, ctx):
        '''
        Loops through the partially loaded lists and fully loads the next three songs from both

        Parameters:
            - `ctx`: discord.commands.Context; The context for the load
        '''
        logger.info('Preloading loop started')
        
        items_to_preload = self.get_items_to_preload()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(partially_loaded_item.get_youtube_dl): partially_loaded_item for partially_loaded_item in items_to_preload}

                for future in concurrent.futures.as_completed(futures):
                    partially_loaded_item = futures[future]
                    try:
                        if self.is_valid_to_play(partially_loaded_item):
                            self.on_preload_succeed(ctx, partially_loaded_item, partially_loaded_item)
                            continue
                        loaded_item = future.result()
                        self.replace_item_in_partially_loaded_lists(partially_loaded_item, loaded_item)
                        self.on_preload_succeed(ctx, partially_loaded_item, loaded_item)
                    except Exception as e:
                        if partially_loaded_item in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(partially_loaded_item)])
                        self.on_load_fail(ctx, partially_loaded_item, e)
            
            do_loop = False
            for item in self.get_items_to_preload():
                if not self.is_valid_to_play(item):
                    do_loop = True
            if do_loop: self.preloading_loop(ctx)
        
        except Exception as e:
            logger.error(f'Preloading loop failed', exc_info=True)
        
        self.preloading_running = False

    def run_youtube_multi_search_in_thread(self, ctx, search_term):
        '''
        Calls functions to properly handle a youtube search command

        Parameters:
            - `ctx`: discord.commands.Context; The context of the command
            - `search_term`: str; The input
        '''
        items = self.search_youtube(search_term, 10)
        self.last_search = items
        self.on_search_complete(ctx, items)

    def run_lyric_search_in_thread(self, ctx, song_title, song_artist):
        '''
        Calls functions to properly handle a lyric search command

        Parameters:
            - `ctx`: discord.commands.Context; The context of the command
            - `search_term`: str; The input
        '''
        if not fetch_setting(ctx.guild.id, 'game_mode'):
            title, lyrics, url = self.fetch_lyrics(song_title, song_artist)
        else:
            
            title, lyrics, url = 'Hidden', '`Lyrics are hidden in game mode`', 'https://genius.com'
        self.on_lyric_search_complete(ctx, title, lyrics, url)
        

    async def respond_to_give_up_loop(self, ctx, member):
        '''
        Gives up game mode guessing after 10 seconds

        Parameters:
            - `ctx`: discord.commands.Context; The context of the command
            - `member`: discord.Member; The member that gave up
        '''
        if not self.can_guess:
            await self.respond_to_give_up_attempt(ctx, member)
            return
        if self.give_up_pending == True:
            await self.respond_to_give_up_attempt(ctx, member, True)
            return
        self.give_up_pending = True
        self.seconds_until_give_up = 10
        response = await self.respond_to_give_up_attempt(ctx, member, False)
        while self.seconds_until_give_up > 0:
            await asyncio.sleep(1)
            self.seconds_until_give_up -= 1
            if self.give_up_pending == False:
                return
            await self.respond_to_give_up_attempt(ctx, member, False, response)
        self.give_up_pending = False
        self.give_up(ctx, member, response)

    #region "Buttons" - Interal Player Actions
    def play(self, ctx: commands.Context, song: LoadedYoutubeSong, return_song_to_list: bool) -> None:
        '''
        Change the player for `ctx.voice_client` to `song`

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in
            - `song`: LoadedYoutubeSong; The new song to play
            - `return_song_to_list`: bool; Whether to return the song back to it's `song_list`

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        logger.info(f'Playing {song}')
        try:
            if ctx.guild.voice_client == None: raise TriedPlayingWhenOutOfVC
            source = YTDLSource.from_url(YTDLSource, song.youtube_data, song, loop=bot.loop, stream=True)
            if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused():
                old_source =  ctx.guild.voice_client.source
                ctx.guild.voice_client.source = source
                self.on_song_end_unknown(ctx, old_source.loaded_song, True)
                if return_song_to_list:
                    self.return_song_to_original_list(old_source.loaded_song)
                else:
                    self.add_song_to_play_history(old_source.loaded_song)
            else:
                ctx.guild.voice_client.play(source, after= lambda e: self.on_song_end_unknown(ctx, song, False, e))
            self.on_song_play(ctx, song)
        except TriedPlayingWhenOutOfVC as e:
            self.add_song_to_play_history(song)
        except Exception as e:
            self.on_start_play_fail(ctx, song, e)
 
    def play_next_item(self, ctx: commands.Context) -> bool:
        '''
        Change the player for `ctx.voice_client` to the next song in the queue or playlist. Removes that item from the queue/playlist

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in

        Returns:
            `bool`; Whether or not a new song was started

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        shuffle = fetch_setting(ctx.guild.id, 'shuffle')
        if shuffle: partially_loaded_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)
        else: partially_loaded_playlist = self.partially_loaded_playlist


        if len(self.partially_loaded_queue) > 0 and self.is_valid_to_play(self.partially_loaded_queue[0]):
            new_song = self.partially_loaded_queue[0]
            if new_song in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(new_song)])
            if new_song in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(new_song)])
            self.play(ctx, new_song, False)
            return True
        elif len(self.partially_loaded_playlist) > 0 and self.is_valid_to_play(partially_loaded_playlist[0]):
            if shuffle:
                shuffled_playlist = self.sort_for_shuffle(self.partially_loaded_playlist)
                new_song = shuffled_playlist[0]
            else:
                new_song = self.partially_loaded_playlist[0]
            if new_song in self.partially_loaded_playlist: del(self.partially_loaded_playlist[self.partially_loaded_playlist.index(new_song)])
            if new_song in self.partially_loaded_queue: del(self.partially_loaded_queue[self.partially_loaded_queue.index(new_song)])
            self.play(ctx, new_song, False)
            return True
        else:
            if len(self.partially_loaded_queue) > 0 or len(self.partially_loaded_playlist) > 0:
                ctx.guild.voice_client.stop()
                self.ensure_preload(ctx)
            return False

    def play_previous_item(self, ctx: commands.Context) -> None:
        '''
        Change the player for `ctx.voice_client` to the first song in the play history

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in

        Returns:
            `bool`; Whether or not a new song was started

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        if len(self.past_songs_played) > 0 and self.is_valid_to_play(self.past_songs_played[0]):
            new_song = self.past_songs_played[0]
            if new_song in self.past_songs_played: del(self.past_songs_played[self.past_songs_played.index(new_song)])
            self.play(ctx, new_song, True)
            return True
        elif len(self.past_songs_played) > 0:
            ctx.guild.voice_client.stop()
            self.return_song_to_original_list(ctx.guild.voice_client.source.loaded_song)
            self.return_song_to_original_list(self.past_songs_played[0])
            self.ensure_preload(ctx)
            return False
        else:
            return False

    def play_next_if_nothing_playing(self, ctx: commands.Context) -> None:
        '''
        Change the player for `ctx.voice_client` to the next song in the queue or playlist if nothing is currently playing

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        if ctx.guild.voice_client == None: raise TriedPlayingWhenOutOfVC
        if not ctx.guild.voice_client.is_playing() and not ctx.guild.voice_client.is_paused():
            self.play_next_item(ctx)
            
    def skip(self, ctx: commands.Context, silent=False) -> None:
        '''
        Skips the current song and plays the next song in the queue or playlist if availible, else stops playing

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        #FIXME decide properly where all the skip stuff goes. Right now some of it is in play next, some is in there, and some is in the on_song_end event.
        if len(self.partially_loaded_playlist) > 0 or len(self.partially_loaded_queue) > 0:
            old_song = ctx.guild.voice_client.source
            is_song_playing = self.play_next_item(ctx)
            new_song = ctx.guild.voice_client.source
            self.on_song_skip(ctx, old_song, new_song, not is_song_playing, silent)
        else:
            old_song = ctx.guild.voice_client.source
            if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused(): ctx.guild.voice_client.stop()  #Stop current song
            new_song = None
            self.on_song_skip(ctx, old_song, new_song, False, silent)

    def skip_backwards(self, ctx: commands.Context) -> None:
        '''
        Skips the current song and plays the first song in the play history if availible, else stops playing

        Parameters:
            - `ctx`: discord.commands.Context; The context to play the song in

        Raises:
            `TriedPlayingWhenOutOfVC`
        '''
        if len(self.past_songs_played) > 0:
            old_song = ctx.guild.voice_client.source
            self.play_previous_item(ctx)
            new_song = ctx.guild.voice_client.source
            self.on_song_skip_backwards(ctx, old_song, new_song)
        else:
            old_song = ctx.guild.voice_client.source
            new_song = None
            self.on_song_skip_backwards(ctx, old_song, new_song)

    def toggle_shuffle(self, ctx: commands.Context) -> None:
        '''
        Toggle shuffle mode for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change    
        '''
        if fetch_setting(ctx.guild.id, 'shuffle'):
            set_setting(ctx.guild.id, 'shuffle', False)
            self.on_shuffle_disable(ctx)
        else:
            set_setting(ctx.guild.id, 'shuffle', True)
            self.reshuffle_list(self.partially_loaded_playlist)
            self.on_shuffle_enable(ctx)
        self.ensure_preload(ctx)

    def toggle_announce(self, ctx: commands.Context) -> None:
        '''
        Toggle announce now playing mode for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change    
        '''
        if fetch_setting(self.last_context.guild.id, 'announce_songs'):
            set_setting(ctx.guild.id, 'announce_songs', False)
            self.on_announce_disable(ctx)
        else:
            set_setting(ctx.guild.id, 'announce_songs', True)
            self.on_announce_enable(ctx)

    def toggle_pause(self, ctx: commands.Context) -> None:
        '''
        Toggle pause for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change      
        '''
        if ctx.guild.voice_client == None or (not ctx.guild.voice_client.is_paused() and not ctx.guild.voice_client.is_playing()): raise NotPlaying
        if ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            self.on_pause_disable(ctx)
        else:
            ctx.guild.voice_client.pause()
            self.on_pause_enable(ctx)

    def toggle_game_mode(self, ctx: commands.Context) -> None:
        '''
        Toggle game mode for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change    
        '''
        if fetch_setting(ctx.guild.id, 'game_mode'):  #Do button shenanigans when game mode is on
            bot.loop.create_task(self.respond_to_game_mode_disable(ctx))
        else:
            set_setting(ctx.guild.id, 'game_mode', True)
            self.on_game_mode_enable(ctx)

    def toggle_autoskip(self, ctx: commands.Context) -> None:
        '''
        Toggle autoskip in game mode for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change    
        '''
        if fetch_setting(self.last_context.guild.id, 'auto_skip'):  #Do button shenanigans when game mode is on
            set_setting(ctx.guild.id, 'auto_skip', False)
            self.on_autoskip_disable(ctx)
        else:
            set_setting(ctx.guild.id, 'auto_skip', True)
            self.on_autoskip_enable(ctx)

    def submit_song_guess(self, ctx, input, loaded_song: LoadedYoutubeSong, member) -> None:
        '''
        Submit a guess for game mode

        Parameters:
            - `ctx`: discord.commands.Context; The context for the guess  
            - `input`: str; The input string
            - `loaded_song`: LoadedYoutubeSong; The correct song
            - `member`: discord.Member; The member that guessed
        '''
        logger.info(f'Guess received: {input} for {loaded_song}')
        if self.can_guess:
            if self.is_title_guess_correct(input, loaded_song):
                self.on_correct_guess(ctx, input, loaded_song, member)
            else:
                self.on_incorrect_guess(ctx, input, loaded_song, member)
        else:
            self.on_invalid_guess(ctx, input, loaded_song, member)

    def start_giveup(self, ctx: commands.Context, loaded_song, member) -> None:
        '''
        Start give up process for current player

        Parameters:
            - `ctx`: discord.commands.Context; The context for the change
            - `loaded_song`: LoadedYoutubeSong; The correct song
            - `member`: discord.Member; The member that tried to give up    
        '''
        bot.loop.create_task(self.respond_to_give_up_loop(ctx, member))

    def give_up(self, ctx, member, message=None):
        '''
            give up

            Parameters:
                - `ctx`: discord.commands.Context; The context for the change
                - `loaded_song`: LoadedYoutubeSong; The correct song
                - `member`: discord.Member; The member that tried to give up
                - `message`: discord.Message; The message that was counting down
        '''
        self.can_guess = False
        loaded_song = ctx.guild.voice_client.source.loaded_song
        bot.loop.create_task(self.respond_to_give_up(ctx, member, loaded_song, message))
        self.on_give_up(ctx)


    def disconnect(self, ctx: commands.Context, auto=False) -> None:
        '''
        Causes `ctx.voice_client` to disconnect, if one is available

        Parameters:
            - `ctx`: discord.commands.Context; The context for the disconnect
            - `auto`: bool; If the disconnection was automatic or not       
        '''
        if ctx.guild.voice_client == None: return
        bot.loop.create_task(ctx.guild.voice_client.disconnect())
        self.on_disconnect(ctx, auto)
    
    def ensure_preload(self, ctx: commands.Context):
        '''
        Starts the preloading loop if the loop is not already running

        Parameters:
            - `ctx`: discord.commands.Context; The context for the load       
        '''
        if not self.preloading_running:
            self.preloading_running = True
            preloading_thread = threading.Thread(target=self.preloading_loop, args=[ctx])
            preloading_thread.start()
    #endregion

    #region "USB cable" Yeah this anaology is falling apart a bit but whatever - Handle different forms of raw input data
    def process_input(self, ctx, input: str, add_to_queue: bool = False) -> None: 
        '''
        Calls functions to properly handle any type of supported input link (Youtube and Spotify)

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `input`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        parsed_input = self.parse_input(input)

        parsed_empty = True
        for value in parsed_input.values():
            if value == []:
                continue
            parsed_empty = False

        if parsed_empty:
            bot.loop.create_task(self.respond_to_unknown_url(ctx, input))

        for youtube_url in parsed_input['youtube_links']:
            self.receive_youtube_url(ctx, youtube_url, add_to_queue)
        for youtube_playlist_url in parsed_input['youtube_playlist_links']:
            self.receive_youtube_playlist_url(ctx, youtube_playlist_url, False)
        for spotify_track_url in parsed_input['spotify_track_links']:
            self.receive_spotify_track_url(ctx, spotify_track_url, add_to_queue)
        for spotify_album_url in parsed_input['spotify_album_links']:
            self.receive_spotify_album_url(ctx, spotify_album_url, False)
        for spotify_playlist_url in parsed_input['spotify_playlist_links']:
            self.receive_spotify_playlist_url(ctx, spotify_playlist_url, False)
        for search_term in parsed_input['search_terms']:
            self.receive_search_term(ctx, search_term, add_to_queue)

    def receive_youtube_url(self, ctx, youtube_url: str, add_to_queue: bool = False, loading_context = None):  
        '''
        Correctly process and call events for a youtube link

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `input`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a youtube link

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `youtube_url`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a spotify track link

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `spotify_url`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a spotify album link

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `spotify_album_url`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a spotify playlist link

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `spotify_playlist_url`: str; The input link
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a search input

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `search_term`: str; The input
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
    
    #region Receive loaded - Handle different types of data after it has been loaded
    def receive_loaded_youtube_data(self, ctx, loaded_song: LoadedYoutubeSong, add_to_queue: bool = False):
        '''
        Correctly process and call events for a loaded YouTube song

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `loaded_song`: LoadedYoutubeSong; The loaded song
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        if add_to_queue:
            self.partially_loaded_queue.append(loaded_song)
            loaded_song.song_list = self.partially_loaded_queue
            self.on_item_added_to_partially_loaded_queue(ctx, loaded_song)
        else:
            self.partially_loaded_playlist.append(loaded_song)
            loaded_song.song_list = self.partially_loaded_playlist
            self.on_item_added_to_partially_loaded_playlist(ctx, loaded_song)

    def receive_loaded_youtube_playlist(self, ctx, loaded_playlist: LoadedYoutubePlaylist, add_to_queue: bool = False):
        '''
        Correctly process and call events for a loaded YouTube playlist

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `loaded_playlist`: LoadedYoutubePlaylist; The loaded playlist
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        for snippet in loaded_playlist.youtube_playlist_snippets:
            self.receive_loaded_youtube_playlist_snippet(ctx, snippet, add_to_queue, loaded_playlist.loading_context)

    def receive_loaded_youtube_playlist_snippet(self, ctx, youtube_snippet: str, add_to_queue: bool = False, loading_context = None):
        '''
        Correctly process and call events for a loaded YouTube song

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `youtube_snippet`: str; The loaded youtube playlist snippet
            - `add_to_queue`: bool; Whether to add the song to the queue or not
            - `loading_context`: LoadingContext | None; The loading context for the url
        '''
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
        '''
        Correctly process and call events for a loaded YouTube playlist

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `loaded_track`: LoadedSpotifyTrack; The loaded track
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        if add_to_queue:
            self.partially_loaded_queue.append(loaded_track)
            self.on_item_added_to_partially_loaded_queue(ctx, loaded_track)
        else:
            self.partially_loaded_playlist.append(loaded_track)
            self.on_item_added_to_partially_loaded_playlist(ctx, loaded_track)

    def receive_loaded_spotify_album(self, ctx, loaded_album: LoadedSpotifyAlbum, add_to_queue: bool = False):
        '''
        Correctly process and call events for a loaded YouTube playlist

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `loaded_album`: LoadedSpotifyAlbum; The loaded album
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        album = loaded_album.spotify_album_data
        for loaded_track in album['tracks']['items']:
            self.receive_loaded_spotify_track(ctx, LoadedSpotifyTrack(loaded_track, loaded_album.loading_context), add_to_queue)

    def receive_loaded_spotify_playlist(self, ctx, loaded_playlist: LoadedSpotifyPlaylist, add_to_queue: bool = False):
        '''
        Correctly process and call events for a loaded YouTube playlist

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `loaded_playlist`: LoadedSpotifyPlaylist; The loaded playlist
            - `add_to_queue`: bool; Whether to add the song to the queue or not
        '''
        playlist = loaded_playlist.spotify_playlist_data
        for loaded_track in [item['track'] for item in playlist['tracks']['items']]:
            self.receive_loaded_spotify_track(ctx, LoadedSpotifyTrack(loaded_track, loaded_playlist.loading_context), add_to_queue)
    #endregion
    
    #region Loaders - Load different types of data into a consistent form
    def load_data_in_thread(self, ctx, unloaded_item, add_to_queue = False):
        '''
        Blocking function to be called in a thread. Loads given unloaded_item and returns constructed loaded object

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedSong; The unloaded item
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `PartiallyLoadedSong | LoadedYoutubePlaylist | LoadedSpotifyAlbum | LoadedSpotifyPlaylist`; The loaded result 
        
        Raises:
            `TypeError`
        '''
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

    def search_youtube(self, text_to_search: str, limit: int = 10) -> list[dict]:
        '''
        Blocking function to be called in a thread. Searches YouTube for the given search term

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `text_to_search`: str; The loaded album
            - `limit`: int; The number of results to get

        Returns:
            `list[dict]`; The result of the search
        '''
        search = VideosSearch(text_to_search, limit=limit)
        return search.result()['result']

    def load_youtube_url(self, ctx, unloaded_item: UnloadedYoutubeSong, add_to_queue = False) -> dict:
        '''
        Blocking function to be called in a thread. Loads single youtube url and returns data dict

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedYoutubeSong; The unloaded song to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `dict`; The result of the YouTubeDL query
        '''
        if not isinstance(unloaded_item, UnloadedYoutubeSong): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        data = ytdl.extract_info(unloaded_item.url, download=False)
        return data

    def load_youtube_playlist_url(self, ctx, unloaded_item: UnloadedYoutubePlaylist, add_to_queue = False) -> tuple[list, str]:  #Loads youtube playlist and returns list of youtube urls
        '''
        Blocking function to be called in a thread. Loads a youtube playlist and returns list of song snippets

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedYoutubeSong; The unloaded song to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `list`; The list of song snippets from the YouTube API query, `str`; The name of the playlist
        '''
        if not isinstance(unloaded_item, UnloadedYoutubePlaylist): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        url = unloaded_item.url
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

    def load_spotify_track_url(self, ctx, unloaded_item: UnloadedSpotifyTrack, add_to_queue = False) -> dict:
        '''
        Blocking function to be called in a thread. Loads a Spotify track and returns the result

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedSpotifyTrack; The unloaded track to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `dict`; The result of the Spotify API query
        '''
        if not isinstance(unloaded_item, UnloadedSpotifyTrack): raise TypeError(unloaded_item)
        url = unloaded_item.url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        track = sp.track(url)
        return track

    def load_spotify_album_url(self, ctx, unloaded_item: UnloadedSpotifyAlbum, add_to_queue = False) -> dict:
        '''
        Blocking function to be called in a thread. Loads a Spotify album and returns the result

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedSpotifyAlbum; The unloaded album to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `dict`; The result of the Spotify API query
        '''
        if not isinstance(unloaded_item, UnloadedSpotifyAlbum): raise TypeError(unloaded_item)
        url = unloaded_item.url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        album = sp.album(url)
        return album
    
    def load_spotify_playlist_url(self, ctx, unloaded_item: UnloadedSpotifyPlaylist, add_to_queue = False) -> dict:  #Loads spotify playlist and returns playlist dict
        '''
        Blocking function to be called in a thread. Loads a Spotify playlist and returns the result

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedSpotifyPlaylist; The unloaded album to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `dict`; The result of the Spotify API query
        '''
        if not isinstance(unloaded_item, UnloadedSpotifyPlaylist): raise TypeError(unloaded_item)
        url = unloaded_item.url
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        results = sp.playlist(url)
        tracks = results['tracks']
        while tracks['next']:
            tracks = sp.next(tracks)
            results['tracks']['items'].extend(tracks['items'])
        return results

    def load_youtube_search(self, ctx, unloaded_item: UnloadedYoutubeSearch, add_to_queue = False):  #Loads single youtube search and returns data dict
        '''
        Blocking function to be called in a thread. Loads a YouTube search and returns data dict

        Parameters:
            - `ctx`: discord.commands.Context; The context the input came from
            - `unloaded_item`: UnloadedSpotifyPlaylist; The unloaded album to load
            - `add_to_queue`: bool; Whether to add the song to the queue or not

        Returns:
            `dict`; The result of the YouTubeDL query
        '''
        if not isinstance(unloaded_item, UnloadedYoutubeSearch): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        data = ytdl.extract_info(unloaded_item.url, download=False)['entries'][0]
        return data
    #endregion
    
    #region Link processing
    def parse_input(self, input: str) -> dict[str, list]:
        '''
        Takes an input string and returns a dictionary with the normalized link in the right spot

        Parameters:
            - `input`: str; The input link

        Returns:
            `dict[str: list]`; A dictionary containing lists of different types of links
        '''
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
        elif website == "i.ytimg":
            temp_dict = self.handle_youtube_image_link(parsed_url) 
            output_dict.update(temp_dict)
        elif website == "spotify":
            temp_dict = self.handle_spotify_link(parsed_url)
            output_dict.update(temp_dict)
        return output_dict

    def parse_youtube_link(self, parsed_url):
        '''
        Takes a parsed url and returns a dictionary with the normalized link in the right spot to be updated onto a larger link dictionary

        Parameters:
            - `parsed_url`: str; The input link

        Returns:
            `dict[str: list]`; A dictionary containing lists of different types of links to be updated onto a larger link dictionary
        '''
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
        '''
        Takes a parsed YouTube short url and returns a dictionary with the normalized link in the right spot to be updated onto a larger link dictionary

        Parameters:
            - `parsed_url`: str; The input link

        Returns:
            `dict[str: list]`; A dictionary containing lists of different types of links to be updated onto a larger link dictionary
        '''
        path = parsed_url.path
        return {'youtube_links' : [f"https://www.youtube.com/watch?v={path[-11:]}"]}

    def handle_youtube_image_link(self, parsed_url):
        '''
        Takes a parsed url YouTube image url and returns a dictionary with the normalized link in the right spot to be updated onto a larger link dictionary

        Parameters:
            - `parsed_url`: str; The input link

        Returns:
            `dict[str: list]`; A dictionary containing lists of different types of links to be updated onto a larger link dictionary
        '''
        parsed_url_path_list = parsed_url.path.split('/')
        return {'youtube_links' : [f"https://www.youtube.com/watch?v={parsed_url_path_list[2]}"]}

    def handle_spotify_link(self, parsed_url):
        '''
        Takes a parsed Spotify url and returns a dictionary with the normalized link in the right spot to be updated onto a larger link dictionary

        Parameters:
            - `parsed_url`: str; The input link

        Returns:
            `dict[str: list]`; A dictionary containing lists of different types of links to be updated onto a larger link dictionary
        '''
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
    #endregion

    #region Data Processing
    def get_shuffle_number(self, loaded_youtube_song: LoadedYoutubeSong) -> int:
        '''
        Takes a loaded YouTube song and returns it's `random_value`

        Parameters:
            - `loaded_youtube_song`: LoadedYoutubeSong; The input song

        Returns:
            `int`; The random value stored in the song object
        '''
        return loaded_youtube_song.random_value

    def sort_for_shuffle(self, playlist: list[LoadedYoutubeSong]) -> list[LoadedYoutubeSong]:
        '''
        Returns the list sorted by the `random_value` of each song

        Parameters:
            - `playlist`: list[LoadedYoutubeSong]; The list to sort

        Returns:
            `list[LoadedYoutubeSong]`; The sorted list
        '''
        new_list = playlist.copy()
        new_list.sort(key=self.get_shuffle_number)
        return new_list

    def get_formatted_playlist(self, song_list: list[LoadedYoutubeSong], page: int) -> list[str]:
        '''
        Returns the list formatted for use in the playlist command, with an index and duration attached

        Parameters:
            - `list`: list[LoadedYoutubeSong]; The list to format
            - `page`: int; The page number (10 songs per page) to format

        Returns:
            `list[str]`; The formatted list
        '''
        index_length = 0
        for song in song_list[10*page: 10*(page + 1)]:
            if len(str(song_list.index(song) + 1)) > index_length: index_length = len(str(song_list.index(song) + 1))
        game_mode = fetch_setting(self.last_context.guild.id, 'game_mode')
        complete_list = []
        for song in song_list[0 + (10*page): 10 + (10*page)]:
            song_line = ''
            song_line += self.get_consistent_length_index(song_list.index(song) + 1, index_length)  # Do index part
            song_line += ' '
            if not game_mode: song_line += self.get_consistent_length_title(song.title)  # Title part
            else: song_line += "Song titles are hidden in game mode"
            song_line += '  '
            song_line += self.parse_duration(song.duration)  # Length part
            complete_list.append(song_line)
        
        return complete_list

    def get_consistent_length_title(self, song_title: str):
        '''
        Returns the song title truncated to a defined length or extended with '----' to meet that same length

        Parameters:
            - `song_title`: str; The name of the song

        Returns:
            `str`; The formatted song name
        '''
        if len(song_title) < 35:
            song_title += ' '
            while len(song_title) < 35: song_title += '-'
        if len(song_title) > 35:
            song_title = song_title[0:34] + '…'
        return song_title

    def get_consistent_length_index(self, index, length):
        '''
        Returns the index number with spaces before it and ')' after it matched to the length provided (if the number has fewer digets than the length)

        Parameters:
            - `index`: int; The index number
            - `length`: int; The length of the string to return

        Returns:
            `str`; The formatted index 
        '''
        pos = f'{index})'
        while len(pos) < length + 1:
            pos = ' ' + pos
        return pos

    def parse_duration(self, duration):
        '''
        Converts a time, in seconds, to a string in the format hr:min:sec, or min:sec if less than one hour.
    
        Parameters:
            - `duration`: int; The time, in seconds

        Returns:
            `str`; The new time, hr:min:sec or min:sec
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

    def get_progress_bar(self, progress_seconds, total_seconds):
        bar = String_Progress_Bar.StringBar(length=30, percent=min(100*progress_seconds/total_seconds, 100))
        bar.edge_back = '▻'
        bar.edge_front = '◅'
        bar.symbol = '●'
        bar.empty_symbol = '○'
        return f'{self.parse_duration(progress_seconds)} {bar.bar} {self.parse_duration(total_seconds)}'

        #return f'{self.parse_duration(progress_seconds)}/{self.parse_duration(total_seconds)}'

    def is_valid_to_play(self, partially_loaded_song: PartiallyLoadedSong) -> bool:
        '''
        Checks if the given `partially_loaded_item` is playable

        Parameters:
            - `partially_loaded_item`: PartiallyLoadedSong; The partially loaded song to check

        Returns:
            `bool`; Whether the song can be played or not
        '''
        if isinstance(partially_loaded_song, LoadedYoutubeSong) and not self.check_403(partially_loaded_song): return True
        else: return False

    def check_403(self, loaded_youtube_song: LoadedYoutubeSong):
        '''
        Checks if the given `loaded_youtube_song` returns an HTTP 403 error

        Parameters:
            - `loaded_youtube_song`: LoadedYoutubeSong; The loaded song to check

        Returns:
            `bool`; Whether the song returns a 403 or not
        '''
        request = requests.head(loaded_youtube_song.youtube_data['url'])
        code = request.status_code
        if code == 403: return True
        else: return False

    def get_items_to_preload(self) -> list[PartiallyLoadedSong]:
        '''
        Gets a list of the items needed for preload, that being the top three items from the playlist (or shuffled playlist) and the queue

        Returns:
            `list`; The list of partially loaded songs
        '''
        items_to_preload = []
        items_to_preload.extend(self.partially_loaded_queue[0:3])
        if fetch_setting(self.last_context.guild.id, 'shuffle'): items_to_preload.extend(self.sort_for_shuffle(self.partially_loaded_playlist)[0:3])
        else: items_to_preload.extend(self.partially_loaded_playlist[0:3])
        return items_to_preload

    def is_title_guess_correct(self, input, loaded_song: LoadedYoutubeSong) -> bool:
        if loaded_song.title_from_spotify != None:
            clean_title = self.get_clean_title_spotify(loaded_song.title_from_spotify)
        else:
            clean_title = self.get_clean_title_youtube(loaded_song.title)

        clean_input = self.get_clean_title_youtube(input)

        logger.info(f'Clean title is {clean_title}. Comparing to {clean_input}...')
        ratio = SequenceMatcher(a=clean_title,b=clean_input).ratio()
        logger.info(f'Ratio for compare is {ratio}')
        if ratio > .8 :
            return True
        else:
            return False
                
    def get_clean_title_youtube(self, title):
        '''
        Takes in a video title presumed to be from Youtube and returns a cleaned verison
        '''
        if '-' in title:
            maybe_title = title.split('-')[1].strip()
        elif '–' in title:
            maybe_title = title.split('–')[1].strip()
        else:
            maybe_title = title
        if 'ft.' in maybe_title:
            index = maybe_title.index('ft.')
            maybe_title = maybe_title[:index] 
        if '(' in maybe_title and ')' in maybe_title:
            title_without_extras = maybe_title
            index_1 = maybe_title.index('(')
            index_2 = maybe_title.index(')')
            title_without_extras = (maybe_title[:index_1] + maybe_title[index_2 + 1:]).strip()
            if len(title_without_extras) > 0 and index_1 > 0 and index_1 < index_2: maybe_title = title_without_extras
        if '[' in maybe_title and ']' in maybe_title:
            title_without_extras = maybe_title
            index_1 = maybe_title.index('[')
            index_2 = maybe_title.index(']')
            title_without_extras = (maybe_title[:index_1] + maybe_title[index_2 + 1:]).strip()
            if len(title_without_extras) > 0 and index_1 > 0 and index_1 < index_2: maybe_title = title_without_extras
        cleaned_title =  re.sub('[\W_]+', ' ', maybe_title, flags=re.UNICODE)  #Make it letters/numbers only
        return cleaned_title.lower().strip()

    def get_clean_title_spotify(self, title):
        '''
        Takes in a song title presumed to be from Spotify and returns a cleaned verison
        '''
        if '-' in title:
            maybe_title = title.split('-')[0].strip()
        elif '–' in title:
            maybe_title = title.split('–')[0].strip()
        else:
            maybe_title = title
        if 'ft.' in maybe_title:
            index = maybe_title.index('ft.')
            maybe_title = maybe_title[:index]
        if '(' in maybe_title and ')' in maybe_title:
            title_without_extras = maybe_title
            index_1 = maybe_title.index('(')
            index_2 = maybe_title.index(')')
            title_without_extras = (maybe_title[:index_1] + maybe_title[index_2 + 1:]).strip()
            if len(title_without_extras) > 0 and index_1 > 0 and index_1 < index_2: maybe_title = title_without_extras
        if '[' in maybe_title and ']' in maybe_title:
            title_without_extras = maybe_title
            index_1 = maybe_title.index('[')
            index_2 = maybe_title.index(']')
            title_without_extras = (maybe_title[:index_1] + maybe_title[index_2 + 1:]).strip()
            if len(title_without_extras) > 0 and index_1 > 0 and index_1 < index_2: maybe_title = title_without_extras
        cleaned_title =  re.sub('[\W_]+', ' ', maybe_title, flags=re.UNICODE)  #Make it letters/numbers only
        return cleaned_title.lower().strip()
    
    def get_score_for_member(self, game_member: GameMember):
        return game_member.score

    def fetch_lyrics(self, song_title, song_artist):
        song = genius.search_song(title=song_title, artist=song_artist)
        if song is not None:
            url = song.url
            song_lyrics = genius.lyrics(song_url=url)

            song_lyrics_list = song_lyrics.split('\n')  # Remove song title thing from the beginning
            song_lyrics = '\n'.join(song_lyrics_list[1:])

            if len(song_lyrics) > 4000:  # Cut off lyrics that are too long
                song_lyrics = song_lyrics[:4000]
                song_lyrics += "\n..."
            else:
                song_lyrics_list = song_lyrics.split('\n')
                last_line = ''
                for letter in song_lyrics_list[-1]:  # Cut off (numbers)Embed garbage
                    try: 
                        int(letter)  # If a number is hit then stop adding letters
                        break
                    except ValueError: 
                        last_line += letter

                song_lyrics_list[-1] = last_line.removesuffix('Embed')  # Just in case there are no numbers, remove this anyway
                song_lyrics = '\n'.join(song_lyrics_list)

            return song.title, song_lyrics, url
        else:
            return None, 'No lyrics found!', None
    #endregion

    #region Data Management
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
        self.ensure_preload(ctx)

    def reshuffle_list(self, playlist: list[PartiallyLoadedSong]):
        for song in playlist:
            song.random_value = random.randint(0, 10000)
    
    def clear_list(self, ctx, list_name):
        if list_name == 'both' or list_name == 'playlist': self.partially_loaded_playlist.clear()
        if list_name == 'both' or list_name == 'queue': self.partially_loaded_queue.clear()
        self.on_list_clear(ctx, list_name)

    def remove_item_from_list(self, ctx, list_name, song_list, loaded_song):
        index = song_list.index(loaded_song)
        del(song_list[index])
        self.on_remove_item_from_list(ctx, list_name, song_list, loaded_song)

    def move_items_between_lists(self, song_list, other_list, index_of_first_song, index_of_last_song, index_to_move_to) -> list[PartiallyLoadedSong]:
        index_of_first_song = max(0, min(index_of_first_song, len(song_list) - 1))
        index_of_last_song = max(0, min(index_of_last_song, len(song_list) - 1)) if index_of_last_song != -1 else -1
        if index_of_last_song == -1: moved_songs = song_list[index_of_first_song:]
        else: moved_songs = song_list[index_of_first_song:index_of_last_song+1]
        other_list[index_to_move_to:index_to_move_to] = moved_songs
        for loaded_song in moved_songs:
            loaded_song.song_list = other_list
        if index_of_last_song == -1: del(song_list[index_of_first_song:])
        else: del(song_list[index_of_first_song:index_of_last_song+1])
        return moved_songs

    def add_song_to_play_history(self, loaded_song):
        self.past_songs_played.insert(0, loaded_song)

    def return_song_to_original_list(self, loaded_song):
        loaded_song.song_list.insert(0, loaded_song)

    def replace_item_in_partially_loaded_lists(self, partially_loaded_item: PartiallyLoadedSong, loaded_item: LoadedYoutubeSong):
        '''
        Replaces the given `partially_loaded_item` in any partially loaded lists with the given `loaded_item`

        Parameters:
            - `partially_loaded_item`: PartiallyLoadedSong; The partially loaded song to replace
            - `loaded_item`: LoadedYoutubeSong; The loaded song to replace with 
        '''
        if partially_loaded_item in self.partially_loaded_playlist:
            index = self.partially_loaded_playlist.index(partially_loaded_item)
            self.partially_loaded_playlist[index] = loaded_item
        elif partially_loaded_item in self.partially_loaded_queue:
            index = self.partially_loaded_queue.index(partially_loaded_item)
            self.partially_loaded_queue[index] = loaded_item

    def remove_item_in_partially_loaded_lists(self, partially_loaded_item):
        '''
        Removes the given `partially_loaded_item` in any partially loaded lists 

        Parameters:
            - `partially_loaded_item`: PartiallyLoadedSong; The partially loaded song to remove
        '''
        if partially_loaded_item in self.partially_loaded_playlist:
            index = self.partially_loaded_playlist.index(partially_loaded_item)
            del self.partially_loaded_playlist[index]
        elif partially_loaded_item in self.partially_loaded_queue:
            index = self.partially_loaded_queue.index(partially_loaded_item)
            del self.partially_loaded_queue[index]

    def add_score_to_member(self, member):
        if member.id in self.game_scoreboard:
            self.game_scoreboard[member.id].score += 1
        else:
            game_member = GameMember(member)
            game_member.score = 1
            self.game_scoreboard[member.id] = game_member
            
    def reset_scores(self):
        self.game_scoreboard.clear()
    #endregion

    #region Command Events

    def groovy_decorator(func, *args, **kwargs):
        '''
        Decorator to be used on every command function to ensure consistent error catching and general functionality

        Parameters:
            - `*args`: Any;
            - `**kwargs`: Any;
        
        Returns:
            Wrapped function
        '''

        async def inner(self, input_ctx, *args, **kwargs):

            try:
                if isinstance(input_ctx, commands.Context) or isinstance(input_ctx, discord.commands.ApplicationContext):  # Don't save interactions
                    self.last_context = input_ctx
                ctx = self.last_context  # Use last valid context for vc setup

                try:
                    await self.setup_vc(ctx)
                except UserNotInVC as e:
                    embed = discord.Embed(description='You need to join a vc!')
                    await self.send_response(ctx, embed)
                    return
                except MusicAlreadyPlayingInGuild as e:
                    embed = discord.Embed(description='Music is already playing somewhere else in this server!')
                    await self.send_response(ctx, embed)
                    return
                except CannotConnectToVC as e:
                    embed = discord.Embed(description='I don\'t have access to that voice channel!')
                    await self.send_response(ctx, embed)
                    return
                except CannotSpeakInVC as e:
                    embed = discord.Embed(description='I don\'t have speak permissions in that voice channel!')
                    await self.send_response(ctx, embed)
                    return
                except asyncio.TimeoutError as e:
                    embed = discord.Embed(description='Connection timed out.')
                    embed.set_footer(text='Either the bot is running very slow, or Discord is having trouble.')
                    await self.send_response(ctx, embed)
                    return

                result = await func(self, input_ctx, *args, **kwargs)  # Make sure to pass input context through no matter what
                return result

            except Exception as e:
                logger.error(f'{func.__name__} failed', exc_info=True)
                embed = discord.Embed(description=f'An unknown error occured.\n```{e}```')
                await self.send_response(input_ctx, embed)
            
            

        return inner

    @groovy_decorator
    async def on_play_command(self, ctx, input: str, add_to_queue: bool):
        '''
        Event to be called when the play command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `input`: str; The input string
            - `add_to_queue`: bool; Whether to add the input to the queue or not
        '''
        logger.info(f'Play command received')
        if len(input ) > 0: self.process_input(ctx, input, add_to_queue)
        else: 
            try: self.toggle_pause(ctx)
            except NotPlaying: 
                self.play_next_item(ctx)
                await self.on_nowplaying_command(ctx)

    @groovy_decorator
    async def on_playlist_command(self, ctx, list: Literal["playlist", "queue", "both", "history"], page: int):
        '''
        Event to be called when the playlist command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `list`: str; The list input string
            - `page`: int; Page input
        '''
        logger.info('Playlist command receive')
        await self.respond_to_playlist_command(ctx, list, page)

    @groovy_decorator
    async def on_skip_command(self, ctx):
        '''
        Event to be called when the skip command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Skip command receive')
        self.skip(ctx)

    @groovy_decorator
    async def on_skip_backwards_command(self, ctx):
        '''
        Event to be called when the skip backwards command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Skip back command receive')
        if not fetch_setting(self.last_context.guild.id, 'game_mode'):
            self.skip_backwards(ctx)
        else:
            self.skip_backwards(ctx)
            self.can_guess = False
        
    @groovy_decorator
    async def on_shuffle_command(self, ctx):
        '''
        Event to be called when the shuffle command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Shuffle command receive')
        self.toggle_shuffle(ctx)

    @groovy_decorator
    async def on_pause_command(self, ctx):
        '''
        Event to be called when the pause command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Pause command receive')
        self.last_context = ctx
        self.toggle_pause(ctx)

    @groovy_decorator
    async def on_announce_command(self, ctx):
        '''
        Event to be called when the toggle annoucement command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Shuffle command receive')
        self.toggle_announce(ctx)

    @groovy_decorator
    async def on_game_mode_toggle_command(self, ctx):
        '''
        Event to be called when the game mode command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Game mode command receive')
        self.toggle_game_mode(ctx)
        
    @groovy_decorator
    async def on_guess_command(self, ctx, input: str):
        '''
        Event to be called when the guess command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `input`: str; The input string
        '''
        logger.info('Guess command receive')
        if ctx.guild.voice_client == None or ctx.guild.voice_client.source == None:
            embed = discord.Embed(description=f'Play something first!')
            await self.send_response(ctx, embed)
        elif fetch_setting(self.last_context.guild.id, 'game_mode'):
            loaded_song = ctx.guild.voice_client.source.loaded_song
            self.submit_song_guess(ctx, input, loaded_song, ctx.author)
        else:
            embed = discord.Embed(description=f'You need to be in game mode for this. Type `/gamemode info` for more info')
            await self.send_response(ctx, embed)

    @groovy_decorator
    async def on_giveup_command(self, ctx):
        '''
        Event to be called when the give up command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Give up command receive')
        if ctx.guild.voice_client == None or ctx.guild.voice_client.source == None:
            embed = discord.Embed(description=f'Play something first!')
            await self.send_response(ctx, embed)
        elif fetch_setting(self.last_context.guild.id, 'game_mode'):
            loaded_song = ctx.guild.voice_client.source.loaded_song
            self.start_giveup(ctx, loaded_song, ctx.author)
        else:
            embed = discord.Embed(description=f'You need to be in game mode for this. Type `/gamemode info` for more info')
            await self.send_response(ctx, embed)

    @groovy_decorator
    async def on_autoskip_command(self, ctx):
        '''
        Event to be called when the game mode command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Autoskip command receive')
        self.toggle_autoskip(ctx)

    @groovy_decorator
    async def on_music_scoreboard_command(self, ctx):
        '''
        Event to be called when the scoreboard command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Scoreboard command receive')
        if fetch_setting(self.last_context.guild.id, 'game_mode'):
            embed = self.get_game_score_embed(self.game_scoreboard)
            await self.send_response(ctx, embed)
        else:
            embed = discord.Embed(description=f'You need to be in game mode for this. Type `/gamemode info` for more info')
            await self.send_response(ctx, embed)

    @groovy_decorator
    async def on_game_mode_info_command(self, ctx):
        '''
        Event to be called when the game mode info command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Game mode info command receive')
        embed = discord.Embed(title='Music Player Game Mode!', description='Type `/guess` to guess the name of the current song! First person to guess correctly gets a point! (Works best with larger playlists in shuffle mode. Supports all kinds of song input, but **works most consistently with Spotify**)', color=7528669)
        await self.send_response(ctx, embed)

    @groovy_decorator        
    async def on_disconnect_command(self, ctx):
        '''
        Event to be called when the disconnect command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Disconnect command receive')
        self.disconnect(ctx)

    @groovy_decorator
    async def on_search_command(self, ctx, search_term):
        '''
        Event to be called when the search command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `search_term`: str; The search input string
        '''
        logger.info('Search command receive')
        thread = threading.Thread(target=self.run_youtube_multi_search_in_thread, args=(ctx, search_term))
        thread.start()

    @groovy_decorator
    async def on_nowplaying_command(self, ctx):
        '''
        Event to be called when the now playing command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Now playing command receive')
        try:
            embed = self.get_nowplaying_message_embed(ctx)
            await self.send_response(ctx, embed)
        except NotPlaying as e:
            logger.info(f'Nothing playing for now playing command')
            embed = discord.Embed(description='Play something first!')
            await self.send_response(ctx, embed)
    
    @groovy_decorator
    async def on_clear_command(self, ctx, list_name: Literal["playlist", "queue", "both"]):
        '''
        Event to be called when the clear command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `list_name`: str; The list name input string
        '''
        logger.info('Clear command receive')
        self.last_context = ctx
        await self.respond_to_clear(ctx, list_name)

    @groovy_decorator
    async def on_remove_command(self, ctx, mode: Literal["song", "all"], list_name: Literal["playlist", "queue"], index: int):
        '''
        Event to be called when the remove command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `mode`: str; The remove mode to use
            - `list_name`: str; The list name input string
            - `index`: int; The index to remove
        '''
        logger.info('Remove command receive')
        self.last_context = ctx

        if mode == 'all':
            await self.on_clear_command(ctx, list_name)
            return
        elif mode == 'song':
            pass
        else:
            embed = discord.Embed(description=f'Mode name must be `song` or `all`, not `{mode}`!')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)
            return

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

    @groovy_decorator
    async def on_move_command(self, ctx, song_list_name: Literal["playlist", "queue"], index_of_first_song: int, index_of_last_song: int, index_to_move_to: int):
        '''
        Event to be called when the move command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `song_list_name`: str; The list name to move songs from
            - `index_of_first_song`: int; The index to start at (inclusive)
            - `index_of_last_song`: int; The index to end at (inclusive)
            - `index_to_move_to`: int; The index to move to
        '''
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
            await self.send_response(ctx, embed)
            return
            
        if len(song_list) == 0:
            embed = discord.Embed(description=f'The {song_list_name} is empty!')
            await self.send_response(ctx, embed)
        if fetch_setting(ctx.guild.id, 'shuffle') and song_list_name == 'playlist':
            embed = discord.Embed(description=f'Sorry, moving songs from the playlist is disabled while shuffle is on.')  #FIXME
            await self.send_response(ctx, embed)
        else:
            moved_songs = self.move_items_between_lists(song_list, other_list, index_of_first_song, index_of_last_song, index_to_move_to)
            self.ensure_preload(ctx)
            await self.respond_to_move(ctx, song_list_name, song_list, other_list_name, other_list, moved_songs)

    @groovy_decorator
    async def on_lyrics_command(self, ctx):
        '''
        Event to be called when the lyrics command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
        '''
        logger.info('Lyrics command receive')
        self.last_context = ctx
        if ctx.guild.voice_client is None or ctx.guild.voice_client.source is None: 
            embed = discord.Embed(description=f'Play something first!')
            await self.send_response(ctx, embed)
            return

        loaded_song = ctx.guild.voice_client.source.loaded_song
        if loaded_song.title_from_spotify != None: title = self.get_clean_title_spotify(loaded_song.title_from_spotify)
        else: title = self.get_clean_title_youtube(loaded_song.title)
        if loaded_song.artist_from_spotify != None: artist = loaded_song.artist_from_spotify
        else: artist = ''

        thread = threading.Thread(target=self.run_lyric_search_in_thread, args=(ctx, title, artist))
        thread.start()

    @groovy_decorator
    async def on_play_message_context(self, ctx, message, add_to_queue: bool):
        '''
        Event to be called when the play context command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `message`: discord.Message; The message that the context command was invoked from
            - `add_to_queue`: bool; Whether to add the input to the queue or not
        '''
        logger.info('Play context command receive')
        if message.content == '':
            embed = discord.Embed(description='Message must have text')
            await ctx.respond(embed=embed)
        else:
            input = message.content
            await self.on_play_command(ctx, input, add_to_queue)

    @groovy_decorator
    async def on_search_message_context(self, ctx, message):
        '''
        Event to be called when the search context command is ran

        Parameters:
            - `ctx`: discord.commands.ApplicationContext; The context of the command
            - `message`: discord.Message; The message that the context command was invoked from
        '''
        logger.info('Search context command receive')
        if message.content == '':
            embed = discord.Embed(description='Message must have text')
            await ctx.respond(embed=embed)
        else:
            search_term = message.content
            await self.on_search_command(ctx, search_term)

    @groovy_decorator
    async def on_clear_button(self, interaction, list_name: Literal["playlist", "queue", "both"]):
        '''
        Event to be called when the confirm clear button is clicked

        Parameters:
            - `interaction`: discord.commands.Interaction; The interaction of the button
            - `list_name`: str; The name of the list to clear
        '''
        ctx = await bot.get_context(interaction.message)
        self.clear_list(ctx, list_name)
        embed = discord.Embed(description=f'Cleared all songs from {"playlist and queue" if list_name == "both" else list_name}', color=8180120)
        await interaction.message.edit(embed=embed, view=None)

    @groovy_decorator
    async def on_remove_button(self, interaction, list_name: str, song_list: list, loaded_song: LoadedYoutubeSong):
        '''
        Event to be called when the confirm remove button is clicked

        Parameters:
            - `interaction`: discord.commands.Interaction; The interaction of the button
            - `list_name`: str; The list name input string
            - `song_list`: list; The actual song list
            - `loaded_song`: LoadedYoutubeSong; The song to remove
        '''
        try:
            ctx = await bot.get_context(interaction.message)
            self.remove_item_from_list(ctx, list_name, song_list, loaded_song)
            embed = discord.Embed(description=f'Removed `{loaded_song}` from {list_name}', color=8180120)
        except ValueError: 
            embed = discord.Embed(description=f'{loaded_song} is not in {list_name}', color=16741747)
        await interaction.message.edit(embed=embed, view=None)

    @groovy_decorator
    async def on_game_mode_off_button(self, interaction):
        '''
        Event to be called when the confirm game mode off button is clicked

        Parameters:
            - `interaction`: discord.commands.Interaction; The interaction of the button
        '''
        try:
            ctx = await bot.get_context(interaction.message)
            set_setting(interaction.guild.id, 'game_mode', False)
            self.reset_scores()
            self.on_game_mode_disable(ctx)
            embed = discord.Embed(description='Game mode off!', color=3093080)
        except Exception as e: 
            embed = discord.Embed(description=f'Something went wrong! {e}', color=16741747)
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
            self.song_list: song_list = song_list
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

    class GameModeOffCommandYesButton(discord.ui.Button):
        def __init__(self, iPod):
            self.iPod = iPod
            super().__init__(style=discord.enums.ButtonStyle.danger, label='Clear Scores and Disable')

        async def callback(self, interaction: discord.Interaction):
            await self.iPod.on_game_mode_off_button(interaction)

    class GameModeOffCommandNoButton(discord.ui.Button):
        def __init__(self, iPod):
            self.iPod = iPod
            super().__init__(style=discord.enums.ButtonStyle.gray, label='Cancel')

        async def callback(self, interaction: discord.Interaction):
            await interaction.message.delete()

    class GiveUpCommandCancelButton(discord.ui.Button):
        def __init__(self, iPod):
            self.iPod = iPod
            super().__init__(style=discord.enums.ButtonStyle.danger, label='Cancel')

        async def callback(self, interaction: discord.Interaction):
            self.iPod.give_up_pending = False
            await interaction.message.delete()
    #endregion
    
    #region Internal events to be called when certain things occur. Often used for responding
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

    def on_item_added_to_partially_loaded_queue(self, ctx, partially_loaded_item):
        logger.info(f'Song added to partially loaded queue event {partially_loaded_item}')
        
    def on_item_added_to_partially_loaded_playlist(self, ctx, partially_loaded_item):
        logger.info(f'Song added to partially loaded playlist event {partially_loaded_item}')
        
    def on_load_fail(self, ctx, unloaded_item, exception):
        if isinstance(exception, youtube_dl.utils.DownloadError) and exception.args[0] == 'ERROR: Sign in to confirm your age\nThis video may be inappropriate for some users.':
            logger.info(f'Age restricted video {unloaded_item} cannot be loaded')
            if unloaded_item.loading_context.parent_playlist != None: unloaded_item.loading_context.parent_playlist.error_count += 1
            bot.loop.create_task(self.respond_to_load_error(ctx, unloaded_item, message='Video is age restricted'))
        else:
            logger.error(f'Failed loading item {unloaded_item}', exc_info=True)
            if unloaded_item.loading_context.parent_playlist != None: unloaded_item.loading_context.parent_playlist.error_count += 1
            bot.loop.create_task(self.respond_to_load_error(ctx, unloaded_item, exception))

    def on_load_start(self, ctx, unloaded_item, add_to_queue):
        logger.info(f'Started loading item {unloaded_item}')
        bot.loop.create_task(self.respond_to_add_unloaded_item(ctx, unloaded_item))

    def on_load_succeed(self, ctx, unloaded_item, loaded_item, add_to_queue):
        logger.info(f'Succeeded loading item {unloaded_item} into {loaded_item}')
        bot.loop.create_task(self.respond_to_load_item(ctx, loaded_item, add_to_queue))

    def on_preload_succeed(self, ctx, unloaded_item, loaded_item):
        if unloaded_item != loaded_item: logger.info(f'Succeeded preloading item {type(unloaded_item)}{unloaded_item} into {type(loaded_item)}{loaded_item}')
        try: self.play_next_if_nothing_playing(ctx)
        except TriedPlayingWhenOutOfVC: return

    def on_vc_connect(self, ctx, channel):
        logger.info(f'Connected to channel {channel}')
        self.reset_scores()
        
    def on_song_play(self, ctx, new_song: LoadedYoutubeSong):
        logger.info(f'Song play succeed {new_song}')
        log_event('song_played', ctx=ctx)
        self.time_of_last_song_start = datetime.datetime.now(datetime.timezone.utc)
        if fetch_setting(self.last_context.guild.id, 'announce_songs'):
            bot.loop.create_task(self.respond_to_nowplaying(ctx, True))

    def on_start_play_fail(self, ctx, new_song: LoadedYoutubeSong, exception):
        logger.error(f'Song play fail {new_song}', exc_info=True)

    def on_during_play_fail(self, ctx, song: LoadedYoutubeSong, exception):
        logger.error(f'Play failed during song {song}', exc_info=True)
        self.ensure_preload(ctx)

    def on_song_end_unknown(self, ctx, song, skip=False, exception=None):
        #When a song ends due to an unknown cause, either an exception or the song completed
        self.can_guess = True
        if exception == None:
            self.on_song_end_succeed(ctx, song)
            self.add_song_to_play_history(song)
            if not skip:
                self.play_next_item(ctx)
        elif exception == discord.errors.ClientException:
            self.on_during_play_fail(ctx, song, exception)
            self.add_song_to_play_history(song)
        else:
            self.on_during_play_fail(ctx, song, exception)
            self.play_next_item(ctx)
        self.ensure_preload(ctx)

    def on_song_end_succeed(self, ctx, song):
        logger.info('Song ended')      

    def on_shuffle_enable(self, ctx):
        logger.info('Shuffle on')
        bot.loop.create_task(self.respond_to_shuffle_enable(ctx))

    def on_shuffle_disable(self, ctx):
        logger.info('Shuffle off')
        bot.loop.create_task(self.respond_to_shuffle_disable(ctx))

    def on_announce_enable(self, ctx):
        logger.info('Announce on')
        bot.loop.create_task(self.respond_to_announce_enable(ctx))

    def on_announce_disable(self, ctx):
        logger.info('Announce off')
        bot.loop.create_task(self.respond_to_announce_disable(ctx))

    def on_pause_enable(self, ctx):
        logger.info('Pause on')
        log_event('music_paused', ctx=ctx)
        bot.loop.create_task(self.respond_to_pause_enable(ctx))

    def on_pause_disable(self, ctx):
        logger.info('Pause off')
        bot.loop.create_task(self.respond_to_pause_disable(ctx))

    def on_game_mode_enable(self, ctx):
        logger.info('Game mode on')
        bot.loop.create_task(self.respond_to_game_mode_enable(ctx))

    def on_game_mode_disable(self, ctx):
        logger.info('Game mode off')
        self.reset_scores()

    def on_autoskip_enable(self, ctx):
        logger.info('Autoskip on')
        bot.loop.create_task(self.respond_to_autoskip_enable(ctx))

    def on_autoskip_disable(self, ctx):
        logger.info('Autoskip off')
        bot.loop.create_task(self.respond_to_autoskip_disable(ctx))
    
    def on_correct_guess(self, ctx, input, loaded_song, member):
        logger.info('Correct guess yay!')
        log_event('correct_guess', ctx=ctx)
        self.can_guess = False
        self.add_score_to_member(member)
        bot.loop.create_task(self.respond_to_correct_guess(ctx, loaded_song))
        if fetch_setting(self.last_context.guild.id, 'auto_skip'):
            self.skip(ctx, True)

    def on_incorrect_guess(self, ctx, input, loaded_song, member):
        logger.info('Incorrect guess')
        log_event('incorrect_guess', ctx=ctx)
        bot.loop.create_task(self.respond_to_incorrect_guess(ctx))

    def on_invalid_guess(self, ctx, input, loaded_song, member):
        logger.info('Incorrect guess')
        bot.loop.create_task(self.respond_to_invalid_guess(ctx))
    
    def on_give_up(self, ctx):
        logger.info('Give up')
        if fetch_setting(self.last_context.guild.id, 'auto_skip'):
            self.skip(ctx, True)

    def on_disconnect(self, ctx, auto):
        logger.info('Disconnect')
        bot.loop.create_task(self.respond_to_disconnect(ctx, auto))

    def on_search_complete(self, ctx, items):
        logger.info('Search complete')
        bot.loop.create_task(self.respond_to_search(ctx, items))

    def on_lyric_search_complete(self, ctx, title, lyrics, url):
        logger.info('Lyric search complete')
        bot.loop.create_task(self.respond_to_lyric_search(ctx, title, lyrics, url))

    def on_song_skip(self, ctx, old_song: YTDLSource, new_song: YTDLSource, loading: bool, silent = False):
        logger.info('Song skipped')
        log_event('song_skip', ctx=ctx)
        if not silent:
            bot.loop.create_task(self.respond_to_skip(ctx, old_song, new_song, loading))

    def on_song_skip_backwards(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        logger.info('Song skipped back')
        log_event('song_skip', ctx=ctx)
        bot.loop.create_task(self.respond_to_skip_backwards(ctx, old_song, new_song))
    
    def on_list_clear(self, ctx, list_name):
        logger.info(f'{list_name} cleared')

    def on_remove_item_from_list(self, ctx, list_name, song_list, loaded_song):
        logger.info(f'Removed {loaded_song} from {list_name}')
    #endregion

    #region Discord VC support
    async def setup_vc(self, ctx: commands.Context):  #Attempts to set up VC. Runs any associated events and sends any error messages
        '''
        UserNotInVC, MusicAlreadyPlayingInGuild, CannotConnectToVC, CannotSpeakInVC, asyncio.TimeoutError
        '''
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
    async def send_response(self, ctx, response, view=None, depth=0):
        try:
            if hasattr(ctx, 'reply'):
                try:
                    if isinstance(response, discord.Embed):
                        return await ctx.reply(embed=response, view=view, mention_author=False)
                    else:
                        return await ctx.reply(content=response, view=view, mention_author=False)
                except Exception as e:
                    logger.error('Error sending message', exc_info=True)
                    return await ctx.reply(content=f'Error sending message\n```{e}```', view=view, mention_author=False)
            elif hasattr(ctx, 'respond'):
                try:
                    if isinstance(response, discord.Embed):
                        return await ctx.respond(embed=response, view=view)
                    else:
                        return await ctx.respond(content=response, view=view)
                except Exception as e:
                    logger.error('Error sending message', exc_info=True)
                    return await ctx.respond(content=f'Error sending message\n```{e}```')
            elif hasattr(ctx, 'channel') and hasattr(ctx.channel, 'send'):
                try:
                    if isinstance(response, discord.Embed):
                        return await ctx.channel.send(embed=response, view=view)
                    else:
                        return await ctx.channel.send(content=response, view=view)
                except Exception as e:
                    logger.error('Error sending message', exc_info=True)
                    return await ctx.channel.send(content=f'Error sending message\n```{e}```', view=view)

            logger.error('Error sending message. No valid response path found.')
        except Exception as e:
            if depth < 1:
                logger.error('Error sending message. Retrying...', {e})
                self.send_response(ctx, response, view, depth=1)
            else:
                logger.error('Error sending message. Retry failed', exc_info=True)


    async def respond_to_add_unloaded_item(self, ctx, item_added):
        embed = discord.Embed(description=f'Loading {item_added}...')
        await item_added.loading_context.send_message(ctx, embed)

    async def respond_to_unknown_url(self, ctx, url):
        embed = discord.Embed(description=f'Unknown url `{url}`. This website is not supported.')
        await self.send_response(ctx, embed)

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
            game_mode = fetch_setting(self.last_context.guild.id, 'game_mode')
            embed = discord.Embed(description=f'Successfully added {item_loaded if not game_mode else "`Song titles are hidden in game mode`"} to {"queue" if add_to_queue else "playlist"}')
            embed.color = 7528669
        await item_loaded.loading_context.send_message(ctx, embed)
        
    async def respond_to_playlist_command(self, ctx, list, page):
        embed_to_send = self.compile_playlist(list, page)
        await self.send_response(ctx, embed_to_send)

    async def respond_to_shuffle_enable(self, ctx):
        embed = discord.Embed(description='Shuffle enabled', color=3093080)
        await self.send_response(ctx, embed)
        if len(self.partially_loaded_queue) > len(self.partially_loaded_playlist):
            embed = discord.Embed(description='You seem to have most of your songs in the queue. Songs in the queue are not effected by shuffle. To add songs to the playlist, use `/add {song}` If you want to move existing songs to the playlist and use shuffle, use `/move queue` (Leave out the indexes to move all)', color=3093080)
            await self.send_response(ctx, embed)

    async def respond_to_shuffle_disable(self, ctx):
        embed = discord.Embed(description='Shuffle disabled', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_announce_enable(self, ctx):
        embed = discord.Embed(description='Announce songs enabled', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_announce_disable(self, ctx):
        embed = discord.Embed(description='Announce songs disabled', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_pause_enable(self, ctx):
        embed = discord.Embed(description='Paused music', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_pause_disable(self, ctx):
        embed = discord.Embed(description='Unpaused msuic', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_autoskip_enable(self, ctx):
        embed = discord.Embed(description='Autoskip on', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_autoskip_disable(self, ctx):
        embed = discord.Embed(description='Autoskip off', color=3093080)
        await self.send_response(ctx, embed)

    async def respond_to_game_mode_enable(self, ctx):
        embed = discord.Embed(title='Game mode ON!', description='Type `/guess` to guess the name of the current song! First person to guess correctly gets a point', color=3137695)
        await self.send_response(ctx, embed)

    async def respond_to_game_mode_disable(self, ctx):
        view = discord.ui.View()
        view.add_item(self.GameModeOffCommandYesButton(self))
        view.add_item(self.GameModeOffCommandNoButton(self))
        embed = discord.Embed(description=f'Are you sure you want to turn game mode off and clear all scores?', color=16741747)
        await self.send_response(ctx, embed, view)

    async def respond_to_give_up_attempt(self, ctx, member, already_pending=False, response=None):
        if not self.can_guess:
            loaded_song = ctx.guild.voice_client.source.loaded_song
            view = discord.ui.View()
            embed = discord.Embed(description=f'The song was {loaded_song.title}', color=16741747)
        elif not already_pending:
            view = discord.ui.View()
            view.add_item(self.GiveUpCommandCancelButton(self))
            embed = discord.Embed(description=f'Revealing song name in {self.seconds_until_give_up} seconds! Any player can cancel!', color=16741747)
        else:
            view = discord.ui.View()
            embed = discord.Embed(description=f'Giving up in {self.seconds_until_give_up} seconds', color=16741747)
        if response != None:
            if isinstance(response, discord.Message): await response.edit(embed=embed)
            elif isinstance(response, discord.Interaction): await response.edit_original_message(embed=embed)
        else:
            await self.send_response(ctx, embed, view)

    async def respond_to_give_up(self, ctx, member, loaded_song, response=None):
        embed = discord.Embed(title='You gave up!', description=f'No one knew the song! It was {loaded_song.title}', color=16741747)
        if response != None: 
            if isinstance(response, discord.Message): await response.edit(embed=embed, view=None)
            elif isinstance(response, discord.Interaction): await response.edit_original_message(embed=embed, view=None)
        else:
            await self.send_response(ctx, embed)

    async def respond_to_correct_guess(self, ctx, loaded_song: LoadedYoutubeSong):
        embed = discord.Embed(title='Correct!', description=f'You guessed {loaded_song.title} correctly! Good job!', color=3137695)
        embed.set_footer(text=f'You guessed the song in {round((datetime.datetime.now(datetime.timezone.utc) - self.time_of_last_song_start).total_seconds(), 2)} seconds!')
        await self.send_response(ctx, embed)

    async def respond_to_incorrect_guess(self, ctx):
        embed = discord.Embed(description='Incorrect! Try again', color=16741747)
        await self.send_response(ctx, embed)

    async def respond_to_invalid_guess(self, ctx):
        embed = discord.Embed(description='You can\'t guess right now', color=16741747)
        await self.send_response(ctx, embed)

    async def respond_to_disconnect(self, ctx, auto):
        embed = discord.Embed(description='Leaving voice chat', color=3093080)
        if not auto:
            await self.send_response(ctx, embed)
        else:
            await ctx.send(embed=embed)  # FIXME

    async def respond_to_search(self, ctx, items):
        embed = self.get_search_message_embed(items)
        await self.send_response(ctx, embed)

    async def respond_to_lyric_search(self, ctx, title, lyrics, url):
        source_text = f'Lyrics from [Genuis]({url})' if url is not None else ''
        embed = discord.Embed(title=f'Lyrics for {title}', description=f'{lyrics}\n\n{source_text}', color=7528669)
        await self.send_response(ctx, embed)

    async def respond_to_nowplaying(self, ctx, announce = False):
        embed = self.get_nowplaying_message_embed(ctx)
        if announce:
            await ctx.send(embed=embed)  # FIXME
        else:
            await self.send_response(ctx, embed)

    async def respond_to_skip(self, ctx, old_song: YTDLSource, new_song: YTDLSource, loading: bool):
        embed = self.get_skip_message_embed(old_song, new_song, loading)
        await self.send_response(ctx, embed)

    async def respond_to_skip_backwards(self, ctx, old_song: YTDLSource, new_song: YTDLSource):
        embed = self.get_skip_backward_message_embed(old_song, new_song)
        await self.send_response(ctx, embed)
    
    async def respond_to_clear(self, ctx, list):
        view = discord.ui.View()
        view.add_item(self.ClearCommandNoButton(self, list))
        view.add_item(self.ClearCommandYesButton(self, list))
        embed = discord.Embed(description=f'Are you sure you want to clear the {"playlist and queue" if list == "both" else list}?', color=16741747)
        await self.send_response(ctx, embed, view)

    async def respond_to_remove_command(self, ctx, list_name, song_list, loaded_song):
        view = discord.ui.View()
        view.add_item(self.RemoveCommandNoButton(self, list_name, song_list, loaded_song))
        view.add_item(self.RemoveCommandYesButton(self, list_name, song_list, loaded_song))
        embed = discord.Embed(description=f'Are you sure you want to remove `{loaded_song}` from the {list_name}?', color=16741747)
        await self.send_response(ctx, embed, view)

    async def respond_to_move(self, ctx, song_list_name, song_list, other_list_name, other_list, moved_songs):
        embed = self.get_move_embed(song_list_name, song_list, other_list_name, other_list, moved_songs)
        await self.send_response(ctx, embed)

    
    #endregion

    #region Message contructors
    def compile_playlist(self, list: str, page=0) -> discord.Embed:
        if list != 'both' and list != 'playlist' and list != 'queue' and list != 'history': raise ValueError(list)
        #Set lists of strings
        if fetch_setting(self.last_context.guild.id, 'shuffle'):
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
        if not fetch_setting(self.last_context.guild.id, 'game_mode'): 
            embed = discord.Embed(title='Now Playing ♫', description=ctx.guild.voice_client.source.title, color=7528669)
            embed.set_thumbnail(url=ctx.guild.voice_client.source.data['thumbnail'])
            progress_time = round((datetime.datetime.now(datetime.timezone.utc) - self.time_of_last_song_start).total_seconds())
            total_time = ctx.guild.voice_client.source.loaded_song.duration
            embed.add_field(name='Song Progress', value=self.get_progress_bar(progress_time, total_time))
        else: 
            embed = discord.Embed(title='Now Playing ♫', description='`Song titles are hidden in game mode`\nNice try!!', color=7528669)
        return embed

    def get_skip_message_embed(self, old_song: YTDLSource, new_song: YTDLSource, loading: bool):
        if new_song != None:
            if not fetch_setting(self.last_context.guild.id, 'game_mode'): embed = discord.Embed(title='Now Playing', description=new_song.title, color=7528669)
            else: embed = discord.Embed(title='Now Playing', description='`Song titles are hidden in game mode`', color=7528669)
            embed.set_footer(text=f'Skipped {old_song.title}')
        elif loading:
            embed = discord.Embed(title='Next song is loading...', description='Please wait for a few seconds', color=7528669)
            if old_song != None:
                embed.set_footer(text=f'Skipped {old_song.title}')
        else: 
            embed = discord.Embed(title='No more songs to play!', description='Add more with /play or /add!', color=7528669)
            if old_song != None:
                embed.set_footer(text=f'Skipped {old_song.title}')
        return embed

    def get_skip_backward_message_embed(self, old_song: YTDLSource, new_song: YTDLSource):
        if new_song == None: 
            embed = discord.Embed(description='Nothing in the play history', color=7528669)
        else: 
            if not fetch_setting(self.last_context.guild.id, 'game_mode'): embed = discord.Embed(title='Now Playing', description=new_song.title, color=7528669)
            else: embed = discord.Embed(title='Now Playing', description='`Song titles are hidden in game mode`', color=7528669)
        return embed

    def get_move_embed(self, song_list_name, song_list, other_list_name, other_list, moved_songs: list[PartiallyLoadedSong]):
        if len(moved_songs) == 1:
            embed = discord.Embed(description=f'Moved {moved_songs[0].title} from {song_list_name} to {other_list_name}')
        else:
            moved_songs_count = len(moved_songs)
            embed = discord.Embed(description=f'Moved {moved_songs_count} songs from {song_list_name} to {other_list_name}')
            
        return embed
    
    def get_game_score_embed(self, scoreboard_dict: dict[int, GameMember]):
        if len(scoreboard_dict) > 0:
            sorted_scoreboard = list(scoreboard_dict.values())
            sorted_scoreboard.sort(key=self.get_score_for_member, reverse=True)
            scoreboard_list = [f'{game_member.name} -- {game_member.score}' for game_member in sorted_scoreboard]
            formatted_scoreboard = '```\n' + '\n'.join(scoreboard_list) + '\n```'
            embed = discord.Embed(title='Current Scoreboard', description=formatted_scoreboard, color=7528669)
            return embed
        elif fetch_setting(self.last_context.guild.id, 'game_mode'):
            embed = discord.Embed(title='Current Scoreboard', description='Scoreboard is empty!', color=7528669)
            return embed
        else:
            embed = discord.Embed(description=f'You need to be in game mode for this. Type `/gamemode info` for more info')
            return embed
    #endregion

class Groovy(commands.Cog, name='Groovy'):
    def __init__(self):
        self.voice_channel_leave.start()
        self.empty_task.start()  # Why? I dunno. But it makes the create_task() responses go fast /shrug

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

    @tasks.loop(seconds=0.01)
    async def empty_task(self):
        ...

    def get_player(self, ctx) -> iPod:
        if ctx.guild.id in music_players.keys():
            return music_players[ctx.guild.id]
        else:
            return iPod(ctx)

    #region Commands
    @commands.command(name='play', aliases=['p'], description='Add a song to the queue')
    async def prefix_play(self, ctx, input: str = '', *more_words):
        log_event('prefix_command', ctx=ctx)
        log_event('play_command', ctx=ctx)
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, True)

    @commands.slash_command(name='play', description='Add a song to the queue')
    async def slash_play(self, ctx: discord.ApplicationContext, input: Option(discord.enums.SlashCommandOptionType.string, description='A link or search term', required=False, default='')):
        log_event('slash_command', ctx=ctx)
        log_event('play_command', ctx=ctx)
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, True)

    @commands.command(name='add', aliases=['a'], description='Add a song to the playlist')
    async def prefix_add(self, ctx, input: str = '', *more_words):
        log_event('prefix_command', ctx=ctx)
        log_event('play_command', ctx=ctx)
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, False)

    @commands.slash_command(name='add', description='Add a song to the playlist')
    async def slash_add(self, ctx, input: Option(discord.enums.SlashCommandOptionType.string, description='A link or search term', required=False, default='')):
        log_event('slash_command', ctx=ctx)
        log_event('play_command', ctx=ctx)
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, False)

    @commands.command(name='skip', aliases=['s', 'sk'], description='Skip the current song!')
    async def prefix_skip(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('skip_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_skip_command(ctx)

    @commands.slash_command(name='skip', description='Skip the current song!')
    async def slash_skip(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('skip_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_skip_command(ctx)

    @commands.command(name='skipback', aliases=['sb', 'b'], description='Skip back to past songs!')
    async def prefix_skipback(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('skipback_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_skip_backwards_command(ctx)

    @commands.slash_command(name='skipback', description='Skip back to past songs!')
    async def slash_skipback(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('skipback_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_skip_backwards_command(ctx)
        
    @commands.command(name='playlist', aliases=['pl'], description='Show playlist/queue')
    async def prefix_playlist(self, ctx, list='both', page='1'):
        log_event('prefix_command', ctx=ctx)
        log_event('playlist_command', ctx=ctx)
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
        log_event('slash_command', ctx=ctx)
        log_event('playlist_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_playlist_command(ctx, list, page-1)

    @commands.command(name='shuffle', aliases=['sh'], description='Toggle shuffle mode')
    async def prefix_shuffle(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('shuffle_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_shuffle_command(ctx)

    @commands.slash_command(name='shuffle', description='Toggle shuffle mode')
    async def slash_shuffle(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('shuffle_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_shuffle_command(ctx)

    @commands.command(name='announcesongs', aliases=['an', 'as'], description='Toggle announcing when a song starts')  # Prefix only
    async def prefix_announce(self, ctx):
        log_event('prefix_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_announce_command(ctx)

    @commands.command(name='pause', description='Toggle pause')
    async def prefix_pause(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('pause_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_pause_command(ctx)

    @commands.slash_command(name='pause', description='Toggle pause')
    async def slash_pause(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('pause_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_pause_command(ctx)

    @commands.command(name='gamemode', aliases=['gm'], description='Toggle music player game mode. Run for more info')
    async def prefix_gamemode(self, ctx, subcommand: str = '', input: str = ''):
        log_event('prefix_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)

        if subcommand == 'toggle' or subcommand == 't': subcommand = 'toggle'
        elif subcommand == 'guess' or subcommand == 'g': subcommand = 'guess'
        elif subcommand == 'giveup' or subcommand == 'gu': subcommand = 'give_up'
        elif subcommand == 'scoreboard' or subcommand == 'sc': subcommand = 'scoreboard'
        elif subcommand == 'info' or subcommand == 'i': subcommand = 'info'
        else: subcommand = 'toggle'

        if subcommand == 'toggle':
            await player.on_game_mode_toggle_command(ctx)
        if subcommand == 'guess':
            await player.on_guess_command(ctx, input)
        if subcommand == 'give_up':
            await player.on_giveup_command(ctx)
        if subcommand == 'scoreboard':
            await player.on_music_scoreboard_command(ctx)
        if subcommand == 'info':
            await player.on_game_mode_info_command(ctx)

    gamemode = SlashCommandGroup(name='gamemode', description='Music player game mode!')

    @gamemode.command(name='info', description='Music player game mode!')
    async def slash_gamemode(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_game_mode_info_command(ctx)

    @gamemode.command(name='toggle', description='Toggle music player game mode. Run for more info')
    async def slash_gamemode(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_game_mode_toggle_command(ctx)

    @commands.command(name='guess', aliases=['g', 'gu'], description='Guess the song name for music game mode!')
    async def prefix_guess(self, ctx, input: str = '', *more_words):
        log_event('prefix_command', ctx=ctx)
        log_event('guess_command', ctx=ctx)
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_guess_command(ctx, input)

    @gamemode.command(name='guess', description='Guess the song name for music game mode!')
    async def slash_guess(self, ctx, input: Option(discord.enums.SlashCommandOptionType.string, description='Input your guess!', required=True)):
        log_event('slash_command', ctx=ctx)
        log_event('guess_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_guess_command(ctx, input)

    @commands.command(name='giveup', description='Give up guessing the song name for music game mode!')
    async def prefix_giveup(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('giveup_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_giveup_command(ctx)

    @gamemode.command(name='giveup', description='Give up guessing the song name for music game mode!')
    async def slash_giveup(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('giveup_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_giveup_command(ctx)

    @commands.command(name='autoskip', description='Toggle music player autoskip in game mode')
    async def prefix_autoskip(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_autoskip_command(ctx)

    @gamemode.command(name='autoskip', description='Toggle music player autoskip in game mode')
    async def prefix_autoskip(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_autoskip_command(ctx)

    @commands.command(name='musicscoreboard', aliases=['scoreboard', 'scb'], description='Show the current scoreboard!')
    async def prefix_musicscoreboard(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_music_scoreboard_command(ctx)

    @gamemode.command(name='musicscoreboard', description='Show the current scoreboard')
    async def slash_musicscoreboard(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('gamemode_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_music_scoreboard_command(ctx)

    @commands.command(name='disconnect', aliases=['dc', 'dis'], description='Leave VC')
    async def prefix_disconnect(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('disconnect_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_disconnect_command(ctx)

    @commands.slash_command(name='disconnect', description='Leave VC')
    async def slash_disconnect(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('disconnect_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_disconnect_command(ctx)

    @commands.command(name='search', aliases=['sch'], description='Search something on YouTube and get a list of results')
    async def prefix_search(self, ctx, input: str = 'music', *more_words):
        log_event('prefix_command', ctx=ctx)
        log_event('search_command', ctx=ctx)
        input = (input + ' ' + ' '.join(more_words)).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_search_command(ctx, input)

    @commands.slash_command(name='search', description='Search something on YouTube and get a list of results')
    async def slash_search(self, ctx, input: Option(str, description='A search term', required=True)):
        log_event('slash_command', ctx=ctx)
        log_event('search_command', ctx=ctx)
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_search_command(ctx, input)

    @commands.command(name="nowplaying", aliases=['np'], description="Show the now playing song")
    async def np(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('nowplaying_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_nowplaying_command(ctx)

    @commands.slash_command(name="nowplaying", description="Show the now playing song")
    async def slash_np(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('nowplaying_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_nowplaying_command(ctx)
    
    @commands.command(name="clear", aliases=['c'], description="Clear the playlist/queue")  # Secret lil guy
    async def prefix_clear(self, ctx, list='both'):
        log_event('prefix_command', ctx=ctx)
        log_event('remove_command', ctx=ctx)
        player = self.get_player(ctx)
        if list.lower().startswith('p'): list = 'playlist'
        if list.lower().startswith('q'): list = 'queue'
        if list != 'both' and list != 'playlist' and list != 'queue': list = 'both'
        await player.on_clear_command(ctx, list)

    @commands.command(name="remove", aliases=['r', 'rm'], description="Remove item from playlist/queue")
    async def prefix_remove(self, ctx, mode='', list='', index='1'):
        log_event('prefix_command', ctx=ctx)
        log_event('remove_command', ctx=ctx)
        player = self.get_player(ctx)

        if mode.lower().startswith('s'): mode = 'song'
        elif mode.lower().startswith('c'): mode = 'all'
        elif mode.lower().startswith('a'): mode = 'all'

        if list.lower().startswith('p'): list = 'playlist'
        elif list.lower().startswith('q'): list = 'queue'
        elif mode == 'all': list = 'both'  # If mode is clear then 'both' is an acceptable list

        try: index = max(0, int(index)-1)
        except ValueError: index = 0

        await player.on_remove_command(ctx, mode, list, index)

    remove = SlashCommandGroup(name='remove', description="Remove items from playlist/queue")

    @remove.command(name="song", description="Remove a single song from playlist/queue")
    async def slash_remove(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Remove song from playlist', 'playlist'), OptionChoice('Remove song from queue', 'queue')], required=True), 
    index:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the song to remove', required=True, min_value=1)):
        log_event('slash_command', ctx=ctx)
        log_event('remove_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_remove_command(ctx, 'song', list, index)

    @remove.command(name="all", description="Clear the playlist/queue")
    async def slash_clear(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Clear playlist', 'playlist'), OptionChoice('Clear queue', 'queue')], required=False, default='both')):
        log_event('slash_command', ctx=ctx)
        log_event('remove_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_clear_command(ctx, list)

    @commands.command(name="move", aliases=['m', 'mv'], description="Move a song between playlist and queue")
    async def prefix_move(self, ctx, song_list_list='', index_of_first_song='1', index_of_last_song='0', index_to_move_to='1'):
        log_event('prefix_command', ctx=ctx)
        log_event('move_command', ctx=ctx)
        player = self.get_player(ctx)
        if song_list_list.lower().startswith('p'): song_list_list = 'playlist'
        if song_list_list.lower().startswith('q'): song_list_list = 'queue'

        try: index_of_first_song = max(0, int(index_of_first_song)-1)
        except (ValueError, TypeError): index_of_first_song = 0
        try: index_of_last_song = max(index_of_first_song, int(index_of_last_song)-1) if int(index_of_last_song)-1 != -1 else -1
        except (ValueError, TypeError): index_of_last_song = index_of_first_song
        try: index_to_move_to = max(0, int(index_to_move_to)-1)
        except (ValueError, TypeError): index_to_move_to = 0

        await player.on_move_command(ctx, song_list_list, index_of_first_song, index_of_last_song, index_to_move_to)

    @commands.slash_command(name="move", description="Move a song between playlist and queue")
    async def slash_move(self, ctx, 
    list:Option(discord.enums.SlashCommandOptionType.string, description='Specify playlist or queue', choices=[OptionChoice('Move song from playlist', 'playlist'), OptionChoice('Move song from queue', 'queue')], required=True), 
    index_to_start:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the first song to move', required=False, min_value=1, default=1),
    index_to_end:Option(discord.enums.SlashCommandOptionType.integer, description='Number of the last song to move', required=False, min_value=1, deafult=0),
    index_to_move_to:Option(discord.enums.SlashCommandOptionType.integer, description='Where to put the songs in the other list', required=False, default=1, min_value=1)):
        log_event('slash_command', ctx=ctx)
        log_event('move_command', ctx=ctx)
        index_to_start -= 1
        if index_to_end is None: index_to_end = 0  # Why is this needed??? I don't get it but if it works it works I guess
        index_to_end -= 1
        index_to_move_to -= 1
        player = self.get_player(ctx)
        await player.on_move_command(ctx, list, index_to_start, index_to_end, index_to_move_to)

    @commands.command(name='lyrics', aliases=['ly', 'lyr'], description='Get lyrics on the current song')
    async def prefix_lyrics(self, ctx):
        log_event('prefix_command', ctx=ctx)
        log_event('lyrics_command', ctx=ctx)
        player = self.get_player(ctx)
        await player.on_lyrics_command(ctx)

    @commands.slash_command(name='lyrics', description='Get lyrics on the current song')
    async def slash_lyrics(self, ctx):
        log_event('slash_command', ctx=ctx)
        log_event('lyrics_command', ctx=ctx)
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_lyrics_command(ctx)

    @commands.message_command(name='play')
    async def context_play(self, ctx, message: discord.Message):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_message_context(ctx, message, True)

    @commands.message_command(name='add')
    async def context_add(self, ctx, message: discord.Message):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_play_message_context(ctx, message, False)

    @commands.message_command(name='search')
    async def context_search(self, ctx, message: discord.Message):
        await ctx.defer()
        player = self.get_player(ctx)
        await player.on_search_message_context(ctx, message)
        
    #endregion
