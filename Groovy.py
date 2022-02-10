import asyncio
import pathlib
import discord
from discord.ext import commands, tasks
import urllib.parse
import youtube_dl
import threading
import traceback
import concurrent.futures
import googleapiclient.discovery
import spotipy

from globalVariables import musicPlayers, bot


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


class LoadedYoutubeSong:
    def __init__(self, youtube_data: dict, part_of_playlist=False) -> None:
        self.youtube_data = youtube_data
        self.part_of_playlist = part_of_playlist

class LoadedYoutubePlaylist:
    def __init__(self, youtube_playlist_split_urls: list) -> None:
        self.youtube_playlist_split_urls = youtube_playlist_split_urls

class LoadedSpotifyTrack:
    def __init__(self, spotify_track_data: dict) -> None:
        self.spotify_track_data = spotify_track_data

class LoadedSpotifyAlbum:
    def __init__(self, spotify_album_data: dict) -> None:
        self.spotify_album_data = spotify_album_data

class LoadedSpotifyPlaylist:
    def __init__(self, spotify_playlist_data: dict) -> None:
        self.spotify_playlist_data = spotify_playlist_data


class UnloadedYoutubeSong:
    def __init__(self, youtube_url, part_of_playlist = False) -> None:
        self.youtube_url = youtube_url
        self.part_of_playlist = part_of_playlist

class UnloadedYoutubePlaylist:
    def __init__(self, youtube_playlist_url) -> None:
        self.youtube_playlist_url = youtube_playlist_url

class UnloadedYoutubeSearch:
    def __init__(self, youtube_search, part_of_playlist) -> None:
        self.youtube_search = youtube_search
        self.part_of_playlist = part_of_playlist

class UnloadedSpotifyTrack:
    def __init__(self, spotify_track_url) -> None:
        self.spotify_track_url = spotify_track_url

class UnloadedSpotifyAlbum:
    def __init__(self, spotify_album_url) -> None:
        self.spotify_album_url = spotify_album_url

class UnloadedSpotifyPlaylist:
    def __init__(self, spotify_playlist_url) -> None:
        self.spotify_playlist_url = spotify_playlist_url

class UserNotInVC(Exception): pass
class MusicAlreadyPlayingInGuild(Exception): pass
class CannotSpeakInVC(Exception): pass
class CannotConnectToVC(Exception): pass
class TriedPlayingWhenOutOfVC(Exception): pass

class iPod:
    def __init__(self, ctx):
        self.shuffle = False
        self.loaded_playlist = []
        self.loaded_queue = []
        self.unloaded_playlist = []
        self.unloaded_queue = []
        self.loading_running = False
    
        musicPlayers[ctx.guild.id] = self
        
    def loading_loop(self, ctx):
        self.loading_running = True
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
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
            executor.shutdown(wait=False)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.load_data_in_thread, ctx, unloaded_item, True): unloaded_item for unloaded_item in self.unloaded_queue}

                for future in concurrent.futures.as_completed(futures):
                    unloaded_item = futures[future]
                    if unloaded_item in self.unloaded_queue: del(self.unloaded_queue[self.unloaded_queue.index(unloaded_item)])
                    try: 
                        loaded_item = future.result()
                        self.on_load_succeed(ctx, unloaded_item, loaded_item, False)
                        self.distrubute_loaded_input(ctx, loaded_item, add_to_queue=True)
                    except Exception as e:
                        self.on_load_fail(ctx, unloaded_item, e)
            if len(self.unloaded_playlist) > 0 or len(self.unloaded_queue) > 0: self.loading_loop(ctx)
        except Exception as e:
            print(f'Loading loop failed with exception: {e}')
        self.loading_running = False


    #"Buttons"

    def play(self, ctx: commands.Context, song: LoadedYoutubeSong):
        #Change player to this song
        try:
            if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused(): ctx.guild.voice_client.stop()
            if ctx.guild.voice_client == None: raise TriedPlayingWhenOutOfVC
            source = YTDLSource.from_url(YTDLSource, song.youtube_data, loop=bot.loop, stream=True)
            ctx.guild.voice_client.play(source, after= lambda e: self.on_song_end_unknown(ctx, song, e))
            self.on_song_play(ctx, song)
        except Exception as e:
            self.on_start_play_fail(ctx, song, e)
 

    def play_next_item(self, ctx):
        #Play next item
        #Returns whether or not a new song was started
        if len(self.loaded_queue) > 0:
            new_song = self.loaded_queue[0]
            if new_song in self.loaded_playlist: del(self.loaded_playlist[self.loaded_playlist.index(new_song)])
            if new_song in self.loaded_queue: del(self.loaded_queue[self.loaded_queue.index(new_song)])
            self.play(ctx, new_song)
            return True
        elif len(self.loaded_playlist) > 0:
            new_song = self.loaded_playlist[0]
            if new_song in self.loaded_playlist: del(self.loaded_playlist[self.loaded_playlist.index(new_song)])
            if new_song in self.loaded_queue: del(self.loaded_queue[self.loaded_queue.index(new_song)])
            self.play(ctx, new_song)
            return True
        else:
            return False

    def play_next_if_nothing_playing(self, ctx):
        #Play next item if nothing is currently playing
        if not ctx.guild.voice_client.is_playing() and not ctx.guild.voice_client.is_paused():
            self.play_next_item(ctx)
            

    def skip(self, ctx, count: int = 1):
        #Skip {count} number of songs
        if count < 1: raise ValueError('Count cannot be less than one')
        
        for i in range(count):
            if len(self.loaded_playlist) > 0 or len(self.loaded_queue) > 0:
                self.play_next_item(ctx)
            else:
                if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused(): ctx.guild.voice_client.stop()  #Stop current song
                break


    def skip_backwards(self, ctx, count: int = 1):
        #Skip {count} number of songs backwards
        if count < 1: raise ValueError('Count cannot be less than one')
        pass

    #"USB cable" Yeah this anaology is falling apart a bit but whatever

    def receive_youtube_url(self, ctx, youtube_url: str, add_to_queue: bool = False, part_of_playlist = False):  #Correctly process and call events for a youtube link. Below functions are similar
        if add_to_queue:
            new_item = UnloadedYoutubeSong(youtube_url, part_of_playlist)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSong(youtube_url, part_of_playlist)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_youtube_playlist_url(self, ctx, youtube_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedYoutubePlaylist(youtube_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubePlaylist(youtube_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_track_url(self, ctx, spotify_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedSpotifyTrack(spotify_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyTrack(spotify_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_album_url(self, ctx, spotify_album_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedSpotifyAlbum(spotify_album_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyAlbum(spotify_album_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_spotify_playlist_url(self, ctx, spotify_playlist_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_search_term(self, ctx, search_term: str, add_to_queue: bool = False, part_of_playlist = False):
        if add_to_queue:
            new_item = UnloadedYoutubeSearch(search_term, part_of_playlist)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSearch(search_term, part_of_playlist)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    #Receive loaded

    def receive_loaded_youtube_data(self, ctx, loaded_song: LoadedYoutubeSong, add_to_queue: bool = False):
        if add_to_queue:
            self.loaded_queue.append(loaded_song)
            self.on_item_added_to_loaded_queue(ctx, loaded_song)
        else:
            self.loaded_playlist.append(loaded_song)
            self.on_item_added_to_loaded_playlist(ctx, loaded_song)

    def receive_loaded_youtube_playlist(self, ctx, loaded_playlist: LoadedYoutubePlaylist, add_to_queue: bool = False):
        for url in loaded_playlist.youtube_playlist_split_urls:
            self.receive_youtube_url(ctx, url, add_to_queue, True)
        self.on_youtube_playlist_sort_complete(ctx, loaded_playlist)

    def receive_loaded_spotify_track(self, ctx, loaded_track: LoadedSpotifyTrack, add_to_queue: bool = False):
        track = loaded_track.spotify_track_data
        title = f"{track['artists'][0]['name']} - {track['name']}"
        self.receive_search_term(ctx, title, add_to_queue, False)

    def receive_loaded_spotify_album(self, ctx, loaded_album: LoadedSpotifyAlbum, add_to_queue: bool = False):
        album = loaded_album.spotify_album_data
        for loaded_track in album['tracks']['items']:
            title = f"{loaded_track['artists'][0]['name']} - {loaded_track['name']}"
            self.receive_search_term(ctx, title, add_to_queue, True)
        self.on_spotify_album_sort_complete(ctx, loaded_album)

    def receive_loaded_spotify_playlist(self, ctx, loaded_playlist: LoadedSpotifyPlaylist, add_to_queue: bool = False):
        playlist = loaded_playlist.spotify_playlist_data
        for loaded_track in [item['track'] for item in playlist['tracks']['items']]:
            title = f"{loaded_track['artists'][0]['name']} - {loaded_track['name']}"
            self.receive_search_term(ctx, title, add_to_queue, True)
        self.on_spotify_playlist_sort_complete(ctx, loaded_playlist)

    #Loaders

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
            # try:  #FIXME
            #     input = int(input)
            #     if input <= 10 and input > 0 and self.last_search != None:
            #         output_dict['youtubeLinks'].append(self.player.lastSearch['result'][input-1]['link'])
            #     input = ''
            # except ValueError:
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

    def load_data_in_thread(self, ctx, unloaded_item, add_to_queue = False):  #Blocking function to be called in a thread. Loads given input and returns constructed Loaded{Type} object
        if isinstance(unloaded_item, UnloadedYoutubeSong):
            data = self.load_youtube_url(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubeSong(data, unloaded_item.part_of_playlist)
        elif isinstance(unloaded_item, UnloadedYoutubePlaylist):
            data = self.load_youtube_playlist_url(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubePlaylist(data)
        elif isinstance(unloaded_item, UnloadedSpotifyTrack):
            data = self.load_spotify_track_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyTrack(data)
        elif isinstance(unloaded_item, UnloadedSpotifyAlbum):
            data = self.load_spotify_album_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyAlbum(data)
        elif isinstance(unloaded_item, UnloadedSpotifyPlaylist):
            data = self.load_spotify_playlist_url(ctx, unloaded_item, add_to_queue)
            return LoadedSpotifyPlaylist(data)
        elif isinstance(unloaded_item, UnloadedYoutubeSearch):
            data = self.load_youtube_search(ctx, unloaded_item, add_to_queue)
            return LoadedYoutubeSong(data, unloaded_item.part_of_playlist)
        else:
            raise TypeError(unloaded_item)

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

        return [f'https://www.youtube.com/watch?v={t["snippet"]["resourceId"]["videoId"]}' for t in playlist_items]

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
        playlist = sp.playlist(url)
        return playlist

    def load_youtube_search(self, ctx, unloaded_item: UnloadedYoutubeSearch, add_to_queue = False):  #Loads single youtube search and returns data dict
        if not isinstance(unloaded_item, UnloadedYoutubeSearch): raise TypeError(unloaded_item)
        self.on_load_start(ctx, unloaded_item, add_to_queue)
        data = ytdl.extract_info(unloaded_item.youtube_search, download=False)['entries'][0]
        return data

    #Events

    def on_item_added_to_unloaded_queue(self, ctx, unloaded_item):
        print('Song added to queue event')
        #bot.loop.create_task(self.respond_to_add_item(ctx, unloaded_item))
        if not self.loading_running: 
            loading_thread = threading.Thread(target=self.loading_loop, args=[ctx])
            loading_thread.start()

    def on_item_added_to_unloaded_playlist(self, ctx, unloaded_item):
        print('Song added to playlist event')
        #bot.loop.create_task(self.respond_to_add_item(ctx, unloaded_item))
        if not self.loading_running: 
            loading_thread = threading.Thread(target=self.loading_loop, args=[ctx])
            loading_thread.start()

    def on_item_added_to_loaded_queue(self, ctx, loaded_item):
        self.play_next_if_nothing_playing(ctx)

    def on_item_added_to_loaded_playlist(self, ctx, loaded_item):
        self.play_next_if_nothing_playing(ctx)

    async def on_play_command(self, ctx, input, add_to_queue=False):
        print('Play command received')
        try:
            await self.setup_vc(ctx)
            self.process_input(ctx, input, add_to_queue)
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
            traceback.print_exc()
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)

    async def on_playlist_command(self, ctx):
        print('Playlist command receive')
        await self.respond_to_playlist(ctx)

    async def on_skip_command(self, ctx, count: int):
        try:
            await self.setup_vc(ctx)
            skipped_source = ctx.guild.voice_client.source
            self.skip(ctx, count)
            self.on_skip(ctx, skipped_source, count)
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
            traceback.print_exc()
            embed = discord.Embed(description=f'An unknown error occured. {e}')
            try: await ctx.reply(embed=embed, mention_author=False)
            except: await ctx.respond(embed=embed)


    def on_load_fail(self, ctx, unloaded_item, exception):
        print(f'Load failed with exception: {exception}')
        traceback.print_exc()
        bot.loop.create_task(self.respond_to_add_item_failed(ctx, unloaded_item, exception))

    def on_load_start(self, ctx, unloaded_item, add_to_queue):
        print('Load start')
        if isinstance(unloaded_item, UnloadedYoutubeSong) or isinstance(unloaded_item, UnloadedYoutubeSearch):
            if not unloaded_item.part_of_playlist: bot.loop.create_task(self.respond_to_add_item_unloaded(ctx, unloaded_item))
        else:
            bot.loop.create_task(self.respond_to_add_item_unloaded(ctx, unloaded_item))
        print(unloaded_item)

    def on_load_succeed(self, ctx, unloaded_item, loaded_item, add_to_queue):
        print('Load Succeed')
        if isinstance(loaded_item, LoadedYoutubeSong):
            if not loaded_item.part_of_playlist: bot.loop.create_task(self.respond_to_add_youtube_song(ctx, loaded_item))

    def on_vc_connect(self, ctx, channel):
        pass
        
    def on_song_play(self, ctx, new_song: LoadedYoutubeSong):
        print('Song play')
        pass

    def on_start_play_fail(self, ctx, new_song: LoadedYoutubeSong, exception):
        traceback.print_exc()
        print('Play failed starting song')

    def on_during_play_fail(self, ctx, song: LoadedYoutubeSong, exception):
        traceback.print_exc()
        print('Play failed during song')

    def on_song_end_unknown(self, ctx, song, exception=None):
        #When a song ends due to an unknown cause, either an exception or the song completed
        if exception == None:
            self.on_song_end(ctx, song)
            self.play_next_item(ctx)
        else:
            self.on_during_play_fail(ctx, song, exception)
            self.play_next_item(ctx)

    def on_song_end(self, ctx, song):
        pass

    def on_youtube_playlist_sort_complete(self, ctx, loaded_playlist: LoadedYoutubePlaylist):
        pass

    def on_spotify_album_sort_complete(self, ctx, loaded_album: LoadedSpotifyAlbum):
        pass

    def on_spotify_playlist_sort_complete(self, ctx, loaded_playlist: LoadedSpotifyPlaylist):
        pass

    def on_skip(self, ctx, skipped_source, count):
        bot.loop.create_task(self.respond_to_skip(ctx, skipped_source, count))
    

    #Discord VC support

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

    #Discord interactions

    async def respond_to_add_item_unloaded(self, ctx, item_added):
        embed = discord.Embed(description='Item added')
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_add_item_failed(self, ctx, unloaded_item, exception):
        embed = discord.Embed(description=f'{unloaded_item} failed to load with error: {exception}')
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_add_youtube_song(self, ctx, item_added: LoadedYoutubeSong):
        embed = discord.Embed(description=f'Successfully added {item_added.youtube_data["title"]}')
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    async def respond_to_playlist(self, ctx):
        text_to_send = self.compile_playlist()
        try: await ctx.reply(text_to_send, mention_author=False)
        except: await ctx.respond(text_to_send)

    async def respond_to_skip(self, ctx, skipped_source, count):
        embed= discord.Embed(title='Reached the end of queue') if ctx.guild.voice_client.source == None else discord.Embed(title="Now Playing", description= f"{ctx.guild.voice_client.source.title}")
        embed.set_footer(text= 'Add more with `/p`!' if ctx.guild.voice_client.source == None else f'Skipped {skipped_source.title}')
        embed.color = 7528669
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)

    def compile_playlist(self):
        queue_title_list = [f"{self.loaded_queue.index(song) + 1}) {song.youtube_data['title']}" for song in self.loaded_queue[:10]]
        playlist_title_list = [f"{self.loaded_playlist.index(song) + 1}) {song.youtube_data['title']}" for song in self.loaded_playlist[:10]]
        return "Queue\n```\n" + "\n".join(queue_title_list) + " ```\n" + "Playlist\n```\n" + "\n".join(playlist_title_list) + "```"if len(queue_title_list + playlist_title_list) > 0 else '```Nothing to play next```'

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


class Groovy(commands.Cog):
    def __init__(self):
        pass

    def get_player(self, ctx) -> iPod | None:
        if ctx.guild.id in musicPlayers.keys():
            return musicPlayers[ctx.guild.id]
        else:
            return iPod(ctx)

    @commands.command(name='play', description='Plays a song!')
    async def play(self, ctx, input: str = '', *more_words):
        input = input + ' ' + ' '.join(more_words).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input)

    @commands.command(name='add', description='Plays a song!')
    async def add(self, ctx, input: str = '', *more_words):
        input = input + ' ' + ' '.join(more_words).strip()  #So that any number of words is accepted in input   #FIXME add character limit or something
        player = self.get_player(ctx)
        await player.on_play_command(ctx, input, True)

    @commands.command(name='skip', description='Skips a song!')
    async def skip(self, ctx, count: str = 1):
        try: count = max(1, int(count))
        except ValueError: count = 1
        player = self.get_player(ctx)
        await player.on_skip_command(ctx, count)
        

    @commands.command(name='playlist', description='Show playlist')
    async def playlist(self, ctx):
        player = self.get_player(ctx)
        await player.on_playlist_command(ctx)
        

    @commands.command(name='play-debug', description='Debug')
    async def play_debug(self, ctx, input: str = ''):
        player = self.get_player(ctx)
        print(f'Unloaded: P: {player.unloaded_playlist} Q: {player.unloaded_queue}')
        print(f'Loaded: P: {player.loaded_playlist} Q: {player.loaded_queue}')





