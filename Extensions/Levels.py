import discord
from discord.commands import Option, OptionChoice
from discord.ext import commands, tasks
import datetime
import logging

from Globals.GlobalVariables import bot, on_log
import Globals.StringProgressBar as StringProgressBar
from Extensions.Statistics import log_event
from Extensions.Settings import fetch_setting

import Extensions.Leaderboard as Leaderboard

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addFilter(on_log)

MESSAGE_XP = 20
VOICE_XP = 5

def setup(bot):
    bot.add_cog(Levels())

class LevelManager(Leaderboard.LeaderboardData):
    def __init__(self):
        super().__init__('levels')
        self.leaderboard_title = "Server XP"

        self.schema = {"user_id" : int, "message_count" : int, "voice_chat_time": int, "xp": int, "last_xp_message_time": int, 'bot': bool}
        self.defaults = {"message_count" : 0, "voice_chat_time": 0, "xp": 0, "last_xp_message_time": 0, 'bot': False}
        self.default_column = "xp"


    async def position_string(self, index, leaderboard_slot, column_name):
        position_number = self.get_position_number(index)
        try:
            member_name = (await bot.fetch_user(leaderboard_slot['user_id'])).name
        except discord.errors.NotFound:
            member_name = leaderboard_slot['user_id']
        score = leaderboard_slot[column_name]

        if column_name == 'xp':
            level = self.xp_to_level(score)
            return f'{position_number} - {member_name} - Level {level}'

        if column_name == 'message_count': units = 'minutes messaging'
        if column_name == 'voice_chat_time': units = 'minutes in voice chat'

        return f'{position_number} - {member_name} - {score} {units}'


    def xp_to_level(self, xp: int):
        # https://github.com/PsKramer/mee6calc/blob/375a60bccc3e9ba70ed712dffe78c3eb513cd661/calc.js#L12
        # 5 / 6 * xp * (2 * xp * xp + 27 * xp + 91)
        level = (5/6) * (xp + 75.703)**(1/3) - 3.525
        # not exactly correct but close enough
        return int(level)

    def level_to_required_xp(self, level: int):
        xp = ((6/5) * (level + 3.525))**3 - 75.703
        return int(xp+1)

    def get_xp(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name='xp')
    
    def change_xp(self, member, change):
        return self.change_score(member, change, column_name='xp')

    def get_message_count(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name='message_count')
    
    def change_message_count(self, member, change):
        return self.change_score(member, change, column_name='message_count')

    def get_voice_chat_time(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name='voice_chat_time')
    
    def change_voice_chat_time(self, member, change):
        return self.change_score(member, change, column_name='voice_chat_time')

    def stringigy_xp(self, xp: int) -> str:
        if xp < 1000:
            return str(xp)
        if xp >= 1000:
            return f"{round(xp/1000, 2)}K"
        if xp >= 1000000:
            return f"{round(xp/1000, 2)}M"

    # Events
    def on_row_init(self, member, column_name):
        if member.bot:
            self.set_score(member, True, column_name='bot')

    def on_score_change(self, member, old_score, new_score, column_name):
        if column_name == 'xp':
            return self.on_xp_change(member, old_score, new_score)

        
    # Level specific events
    def on_xp_change(self, member, old_score, new_score):
        old_level = self.xp_to_level(old_score)
        new_level = self.xp_to_level(new_score)

        if new_level > old_level:
            return self.on_levelup(member, new_level)

    def on_levelup(self, member, level):
        bot.loop.create_task(self.respond_to_levelup(member, level))


    async def respond_to_levelup(self, member: discord.Member, level):
        channel_id = fetch_setting(member.guild.id, 'levelup_channel')
        if channel_id is None:
            return
        # Skip if channel doesn't exist (probably deleted)
        if channel_id not in [channel.id for channel in member.guild.channels]:
            return

        channel = member.guild.get_channel(channel_id)

        if not channel.permissions_for(member.guild.get_member(bot.user.id)).send_messages:
            return

        await channel.send(self.get_levelup_message(member, level))

    # Constructors
    def get_rank_embed(self, member: discord.Member, column_name='xp', exclude_names: list[str]=['bot']):
        embed = discord.Embed()
        
        if member.bot:
            # Force include bots if the member is a bot
            if 'bot' in exclude_names:
                exclude_names.remove('bot')
        
        leaderboard = self.get_leaderboard(member, column_name=column_name, exclude_names=exclude_names)
        
        index = self.get_user_index_on_leaderboard(member, leaderboard=leaderboard)

        if index == -1:
            return discord.Embed(description='Member is not on leaderboard!')
        
        xp = self.get_xp(member, leaderboard=leaderboard)
        level = self.xp_to_level(xp)

        current_progress_xp = xp - self.level_to_required_xp(level)

        current_level_xp = self.level_to_required_xp(level)
        next_level_xp = self.level_to_required_xp(level+1)

        xp_to_next_level = next_level_xp - current_level_xp


        percent = min(current_progress_xp/xp_to_next_level * 100, 100)

        progress_bar = StringProgressBar.StringBar(percent=percent, length=15)
        progress_bar.edge_back = '▻'
        progress_bar.edge_front = '◅'
        progress_bar.symbol = '●'
        progress_bar.empty_symbol = '○'

        embed.title = f"Rank #{index+1} - Level {level} - {member.display_name}"
        embed.description = f"Ranked #{index+1} out of {len(leaderboard)}"
        embed.add_field(name=f"{self.stringigy_xp(current_progress_xp)}/{self.stringigy_xp(xp_to_next_level)} xp to next level", value=progress_bar.bar)

        if 'bot' not in exclude_names:
            embed.description += " (Bots included)"
        embed.set_thumbnail(url=member.display_avatar)
        embed.color = 7528669

        return embed

    def get_levelup_message(self, member, level):
        if fetch_setting(member.guild.id, 'mention_levelups'):
            return f"Congratulations {member.mention}, you hit level {level}!"
        else:
            return f"Congratulations {member.display_name}, you hit level {level}!"

    
class Levels(commands.Cog):
    def __init__(self) -> None:
        self.levels_voice_chat_loop.start()

        self.watched_channel_ids = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.channel.type == discord.ChannelType.private:
            return
        if message.is_system():
            return
        if not isinstance(message.author, discord.Member):
            return
        
        level_manager = LevelManager()

        last_xp_time = level_manager.get_member_score(message.author, column_name="last_xp_message_time")
        message_time = int(datetime.datetime.timestamp(message.created_at))
        
        # Ignore if message was within a minute of the last time XP was given
        if (message_time - last_xp_time) < 60:
            return

        # Set the last time a message gave this user XP
        level_manager.set_score(message.author, message_time, column_name="last_xp_message_time")
        # Add the message count
        level_manager.change_message_count(message.author, 1)
        # Add the XP
        level_manager.change_xp(message.author, MESSAGE_XP)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        channel_id = after.channel.id if after.channel is not None else before.channel.id
        logger.info(f"Member={member.id} entered voice chat {channel_id}")

        self.watched_channel_ids.add(channel_id)
        


    @tasks.loop(minutes=1)
    async def levels_voice_chat_loop(self):
        logger.info("Checking voice chats for xp")

        try:

            for channel_id in self.watched_channel_ids.copy():

                channel: discord.VoiceChannel = await bot.fetch_channel(channel_id)

                if channel.type != discord.ChannelType.voice:
                    logger.warn("Text Channel in Voice Channel Watch List")
                    return

                member_voice_states: dict[int: discord.VoiceState] = {await channel.guild.fetch_member(member_id): voice_state for member_id, voice_state in channel.voice_states.items()}

                if len([member for member in member_voice_states if not member.bot]) < 2:
                    if channel_id in self.watched_channel_ids:
                        self.watched_channel_ids.remove(channel_id)
                    return 

                level_manager = LevelManager()

                for member, voice_state in member_voice_states.items():
                    # Ignore AFK users and deafened users (They aren't really participating so...)
                    if voice_state.afk or voice_state.self_deaf or voice_state.deaf:
                        continue

                    level_manager.change_voice_chat_time(member, 1)
                    level_manager.change_xp(member, VOICE_XP)
        except Exception as e:
            logger.error("Voice channel XP loop failed", exc_info=True)
            user = await bot.fetch_user(bot.owner_id)
            await user.send(f"`Voice channel XP loop failed\n{e}`")

    @levels_voice_chat_loop.before_loop
    async def before_voice_loop(self):
        logger.info("Starting voice XP loop...")



    @commands.slash_command(name="levels", description="Shows the level leaderboard")
    async def levels_slash(self, ctx, sort:Option(str, name='sort', description='Sort levels leaderboard', choices=[OptionChoice('Total XP', 'xp'), OptionChoice('Minutes messaged', 'messages'), OptionChoice('Minutes in VC', 'vc')], required=False, default='xp'), page_number:Option(int, name='page', description='Page number to show', required=False, default=1), show_bots:Option(bool, name='bots', description='Show bots in leaderboard', required=False, default=False)):
        log_event('slash_command', ctx=ctx)
        log_event('leaderboard_command', ctx=ctx)
        level_manager = LevelManager()
        page_index = max(0, page_number - 1)
        if sort == 'messages': sort = 'message_count'
        elif sort == 'vc': sort = 'voice_chat_time'
        else: sort = 'xp'
        if show_bots: exclude_names = []
        else: exclude_names = ['bot']
        embed = await level_manager.fetch_leaderboard_embed(ctx.author, page_index, column_name=sort, exclude_names=exclude_names)
        await ctx.respond(embed=embed)

    @commands.command(name="levels", description="Shows the level leaderboard")
    async def levels_prefix(self, ctx, input_1='xp', input_2='1'):
        log_event('prefix_command', ctx=ctx)
        log_event('leaderboard_command', ctx=ctx)
        level_manager = LevelManager()
        try: 
            page_number = int(input_1)
            sort = input_2
        except ValueError:
            sort = input_1
            try:
                page_number = int(input_2)
            except ValueError:
                page_number = 1

        page_index = max(0, page_number - 1)
        if sort == 'messages' or sort == 'message' or sort == 'm': 
            sort = 'message_count'
            level_manager.leaderboard_title = 'Messaging minutes'
        elif sort == 'vc' or sort == 'voice' or sort == "voicechat" or sort == "voice_chat": 
            sort = 'voice_chat_time'
            level_manager.leaderboard_title = 'Voice Chat Minutes'
        else:
            sort = 'xp'
            level_manager.leaderboard_title = 'Levels'
        embed = await level_manager.fetch_leaderboard_embed(ctx.author, page_index, column_name=sort, exclude_names=['bot'])
        await ctx.reply(embed=embed, mention_author=False)

    @commands.slash_command(name="rank", description="Shows your or another member's current rank")
    async def rank_slash(self, ctx, member_input: Option(discord.Member, name='member', description='Member to get the rank of', optional=True, default=None), sort:Option(str, name='sort', description='Sort rank leaderboard', choices=[OptionChoice('Total XP', 'xp'), OptionChoice('Minutes messaged', 'messages'), OptionChoice('Minutes in VC', 'vc')], required=False, default='xp'), show_bots:Option(bool, name='bots', description='Show bots in leaderboard', required=False, default=False)):
        log_event('slash_command', ctx=ctx)
        log_event('rank_command', ctx=ctx)
        level_manager = LevelManager()
        if sort == 'messages': sort = 'message_count'
        elif sort == 'vc': sort = 'voice_chat_time'
        else: sort = 'xp'
        if show_bots: exclude_names = []
        else: exclude_names = ['bot']

        if member_input is not None:
            member = member_input
        else:
            member = ctx.author

        embed = level_manager.get_rank_embed(member, column_name=sort, exclude_names=exclude_names)
        await ctx.respond(embed=embed)

    @commands.command(name="rank", description="Shows your or another member's current rank")
    async def rank_prefix(self, ctx, input_1='xp', input_2=''):
        log_event('prefix_command', ctx=ctx)
        log_event('leaderboard_command', ctx=ctx)
        level_manager = LevelManager()
        try: 
            member_id = int(input_1.replace('<', '').replace('@', '').replace('!', '').replace('>', ''))
            sort = input_2
        except ValueError:
            sort = input_1
            try:
                member_id = int(input_2.replace('<', '').replace('@', '').replace('!', '').replace('>', ''))
            except ValueError:
                member_id = ctx.author.id

        if sort == 'messages' or sort == 'message' or sort == 'm': 
            sort = 'message_count'
        elif sort == 'vc' or sort == 'voice' or sort == "voicechat" or sort == "voice_chat": 
            sort = 'voice_chat_time'
        else:
            sort = 'xp'

        try:
            member = await ctx.guild.fetch_member(member_id)
        except discord.errors.NotFound:
            member = ctx.author

        embed = level_manager.get_rank_embed(member, column_name=sort, exclude_names=['bot'])
        await ctx.reply(embed=embed, mention_author=False)
