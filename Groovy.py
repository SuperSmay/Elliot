import asyncio

import discord
import youtube_dl

from discord.ext import commands

from globalVariables import client

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
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

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


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
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

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