import discord
from discord.commands import Option, OptionChoice
from discord.ext import commands
import datetime

from GlobalVariables import bot

# import DBManager
import Leaderboard

class LevelManager(Leaderboard.LeaderboardData):
    def __init__(self):
        super().__init__('levels')
        self.leaderboard_title = "Server XP"

        self.schema = {"user_id" : int, "message_count" : int, "voice_chat_time": int, "xp": int, "last_xp_message_time": int}
        self.defaults = {"message_count" : 0, "voice_chat_time": 0, "xp": 0, "last_xp_message_time": 0}
        self.default_column = "xp"


    async def position_string(self, index, leaderboard_slot, column_name):
        position_number = self.get_position_number(index)
        try:
            member_name = (await bot.fetch_user(leaderboard_slot['user_id'])).name
        except discord.errors.NotFound:
            member_name = leaderboard_slot['user_id']
        score = leaderboard_slot[column_name]

        level_text = ''
        if column_name == 'xp':
            score = self.xp_to_level(score)
            level_text = 'Level '

        if column_name == 'message_count': self.units = 'minutes messaging'
        if column_name == 'voice_chat_time': self.units = 'minutes in voice chat'

        return f'{position_number} - {member_name} - {level_text}{score} {self.units}'


    def xp_to_level(self, xp: int):
        # https://github.com/PsKramer/mee6calc/blob/375a60bccc3e9ba70ed712dffe78c3eb513cd661/calc.js#L12
        # 5 / 6 * xp * (2 * xp * xp + 27 * xp + 91)
        level = (5/6) * (xp + 75.703)**(1/3) - 3.525
        # not exactly correct but close enough
        return int(level)

    def get_xp(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name="xp")
    
    def change_xp(self, member, change, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        xp = self.get_xp(member, leaderboard)
        xp += change
        return self.set_score(member, xp, column_name="xp")

    def get_message_count(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name="message_count")
    
    def change_message_count(self, member, change, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        message_count = self.get_message_count(member, leaderboard)
        message_count += change
        return self.set_score(member, message_count, column_name="message_count")

    def get_voice_chat_time(self, member, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        return self.get_member_score(member, leaderboard, column_name="voice_chat_time")
    
    def change_voice_chat_time(self, member, change, leaderboard=None):
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        voice_chat_time = self.get_voice_chat_time(member, leaderboard)
        voice_chat_time += change
        return self.set_score(member, voice_chat_time, column_name="voice_chat_time")
    
class Levels(commands.Cog):
    def __init__(self) -> None:
        ...

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: 
            return
        level_manager = LevelManager()
        leaderboard = level_manager.get_leaderboard(message.author)

        last_xp_time = level_manager.get_member_score(message.author, leaderboard, column_name="last_xp_message_time")
        message_time = int(datetime.datetime.timestamp(message.created_at))
        
        if (message_time - last_xp_time) < 60:
            return
        
        level_manager.set_score(message.author, message_time, column_name="last_xp_message_time")

        level_manager.change_message_count(message.author, 1, leaderboard=leaderboard)

        level_manager.change_xp(message.author, 20, leaderboard=leaderboard)

    @commands.slash_command(name="levels", description="Shows the level leaderboard")
    async def levels_slash(self, ctx, sort:Option(str, description='Sort levels leaderboard', choices=[OptionChoice('Total XP', 'xp'), OptionChoice('Minutes messaged', 'messages'), OptionChoice('Minutes in VC', 'vc')], required=False, default='xp'), page_number:Option(int, description='Page number', required=False, default=1)):
        level_manager = LevelManager()
        page_index = max(0, page_number - 1)
        if sort == 'messages': sort = 'message_count'
        elif sort == 'vc': sort = 'voice_chat_time'
        else: sort = 'xp'
        embed = await level_manager.get_leaderboard_embed(ctx.author, page_index, column_name=sort)
        await ctx.respond(embed=embed)

    @commands.command(name="levels", description="Shows the level leaderboard")
    async def levels_prefix(self, ctx, sort='xp', page_number=1):
        level_manager = LevelManager()
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
        embed = await level_manager.get_leaderboard_embed(ctx.author, page_index, column_name=sort)
        await ctx.reply(embed=embed, mention_author=False)
