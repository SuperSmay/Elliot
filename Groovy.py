import discord
from discord.ext import commands, tasks
import urllib
import youtube_dl
import threading

from globalVariables import musicPlayers, bot


##TODO List
    #/ Youtube-DL simple youtube links
    ## Split youtube playlists
    ## Convert simple spotify tracks
    ## Split spotify playlists and albums
    ## Play history (Youtube link or dl'd dict?)
    ## Play youtube-dl'd input correctly
    ## Add command
    ## Skip command
    ## Playlist command (Properly this time)
    ## Skip backwards command
    ## 
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

class LoadedSong:
    def __init__(self, data) -> None:
        self.data = data

class UnloadedYoutubeSong:
    def __init__(self, youtube_url) -> None:
        self.youtube_url = youtube_url

class UnloadedYoutubePlaylist:
    def __init__(self, youtube_playlist_url) -> None:
        self.youtube_playlist_url = youtube_playlist_url

class UnloadedYoutubeSearch(UnloadedYoutubeSong):
    def __init__(self, youtube_search) -> None:
        super().__init__(youtube_search)

class UnloadedSpotifyTrack:
    def __init__(self, spotify_track_url) -> None:
        self.spotify_track_url = spotify_track_url

class UnloadedSpotifyAlbum:
    def __init__(self, spotify_album_url) -> None:
        self.spotify_album_url = spotify_album_url

class UnloadedSpotifyPlaylist:
    def __init__(self, spotify_playlist_url) -> None:
        self.spotify_playlist_url = spotify_playlist_url

class iPod:
    def __init__(self, ctx):
        self.shuffle = False
        self.loaded_playlist = []
        self.loaded_queue = []
        self.unloaded_playlist = []
        self.unloaded_queue = []

        musicPlayers[ctx.guild.id] = self

    #"Buttons"

    def play(song: LoadedSong):
        #Change player to this song
        pass

    def skip(count: int = 1):
        #Skip {count} number of songs
        pass

    def skip_backwards(count: int = 1):
        #Skip {count} number of songs backwards
        pass

    #"USB cable" Yeah this anaology is falling apart a bit but whatever

    def receive_youtube_url(self, ctx, youtube_url: str, add_to_queue: bool = False):  #Correctly process and call events for a youtube link. Below functions are similar
        if add_to_queue:
            new_item = UnloadedYoutubeSong(youtube_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSong(youtube_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_youtube_playlist_url(self, ctx, youtube_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedYoutubePlaylist(youtube_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSong(youtube_url)
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

    def receive_spotify_song_url(self, ctx, spotify_playlist_url: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedSpotifyPlaylist(spotify_playlist_url)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_search_term(self, ctx, search_term: str, add_to_queue: bool = False):
        if add_to_queue:
            new_item = UnloadedYoutubeSearch(search_term)
            self.unloaded_queue.append(new_item)
            self.on_item_added_to_unloaded_queue(ctx, new_item)
        else:
            new_item = UnloadedYoutubeSearch(search_term)
            self.unloaded_playlist.append(new_item)
            self.on_item_added_to_unloaded_playlist(ctx, new_item)

    def receive_loaded_data(self, ctx, loaded_data: dict, add_to_queue: bool = False):
        if add_to_queue:
            loaded_song = LoadedSong(loaded_data)
            self.loaded_queue.append(loaded_song)
            self.on_item_added_to_loaded_queue(ctx, loaded_song)
        else:
            loaded_song = UnloadedYoutubeSearch(loaded_data)
            self.loaded_playlist.append(loaded_song)
            self.on_item_added_to_loaded_playlist(ctx, loaded_song)
    #Loaders

    def process_input(self, ctx, input: str, add_to_queue: bool = False) -> None:  #Calls functions processing each type of supported link
        parsed_input = self.parse_input(input)
        for youtube_url in parsed_input['youtube_links']:
            self.receive_youtube_url(ctx, youtube_url, add_to_queue)
        for youtube_playlist_url in parsed_input['youtube_playlist_links']:
            self.receive_youtube_playlist_url(ctx, youtube_playlist_url, add_to_queue)
        for spotify_track_url in parsed_input['spotify_track_links']:
            self.receive_youtube_url(ctx, spotify_track_url, add_to_queue)
        for spotify_album_url in parsed_input['spotify_album_links']:
            self.receive_spotify_album_url(ctx, spotify_album_url, add_to_queue)
        for spotify_playlist_url in parsed_input['spotify_playlist_links']:
            self.receive_youtube_url(ctx, spotify_playlist_url, add_to_queue)
        for search_term in parsed_input['search_terms']:
            self.receive_search_term(ctx, search_term, add_to_queue)

    def parse_input(self, input: str) -> dict:
        output_dict = {'youtube_links' : [], 'youtube_playlist_links' : [], 'spotify_track_links' : [], 'spotify_album_links' : [], 'spotify_playlist_links' : [],'search_terms' : []}
        if input == "":
            return output_dict
        if input.startswith("www.") and not (input.startswith("https://") or input.startswith("http://") or input.startswith("//")):
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
            temp_dict = self.handle_youtube_link(parsed_url)
            output_dict.update(temp_dict)
        elif website == "youtu.be":
            temp_dict = self.handle_youtube_short_link(parsed_url) 
            output_dict.update(temp_dict)
        elif website == "spotify":
            temp_dict = self.handle_spotify_link(parsed_url)
            output_dict.update(temp_dict)
        return output_dict

    def handle_youtube_link(self, parsed_url):
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

    def load_data_in_thread(self, ctx, unloaded_item, add_to_queue = False):
        if isinstance(unloaded_item, UnloadedYoutubeSong):
            self.on_load_start(ctx, unloaded_item, add_to_queue)
            try: 
                url = unloaded_item.youtube_url
                data = ytdl.extract_info(url, download=False)
                self.receive_loaded_data(data, add_to_queue)
                self.on_load_succeed(ctx, data, add_to_queue)

            except Exception as e:
                if unloaded_item in self.unloaded_queue: del(self.unloaded_queue[self.unloaded_queue.index(unloaded_item)])
                if unloaded_item in self.unloaded_playlist: del(self.unloaded_playlist[self.unloaded_playlist.index(unloaded_item)])
                self.on_load_fail(ctx, unloaded_item, e)
        else:
            print('Impropper object type passed')

    #Events

    def on_item_added_to_unloaded_queue(self, ctx, unloaded_item: UnloadedYoutubeSong | UnloadedSpotifyTrack):
        print('Song added to queue event')
        bot.loop.create_task(self.respond_to_add_item(ctx, unloaded_item))
        thread = threading.Thread(target=self.load_data_in_thread, args = (ctx, unloaded_item, True))
        thread.start()

    def on_item_added_to_unloaded_playlist(self, ctx, unloaded_item: UnloadedYoutubeSong | UnloadedSpotifyTrack):
        print('Song added to playlist event')
        bot.loop.create_task(self.respond_to_add_item(ctx, unloaded_item))
        thread = threading.Thread(target=self.load_data_in_thread, args = (ctx, unloaded_item, False))
        thread.start()

    def on_item_added_to_loaded_queue(self, ctx, loaded_item):
        pass

    def on_item_added_to_loaded_playlist(self, ctx, loaded_item):
        pass

    def on_play_command(self, ctx, input):
        print('Play command received')
        self.process_input(ctx, input)

    def on_load_fail(self, ctx, data):
        print('Load failed')

    def on_load_start(self, ctx, unloaded_item, add_to_queue):
        print('Load start')

    def on_load_succeed(self, ctx, loaded_item, add_to_queue):
        print('Load Succeed')
    #Discord VC support

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

    #Discord interactions

    async def respond_to_add_item(self, ctx, item_added):
        embed = discord.Embed(description='Item added')
        try: await ctx.reply(embed=embed, mention_author=False)
        except: await ctx.respond(embed=embed)


class Groovy(commands.Cog):
    def __init__(self):
        pass

    def get_player(self, ctx) -> iPod | None:
        if ctx.guild.id in musicPlayers.keys():
            return musicPlayers[ctx.guild.id]
        else:
            return iPod(ctx)

    @commands.command(name='play', description='Plays a song!')
    async def play(self, ctx, input: str = ''):
        self.get_player(ctx).on_play_command(ctx, input)



