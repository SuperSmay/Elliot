import discord
from discord.ext import commands
import datetime

# import DBManager
import Leaderboard

class LevelManager(Leaderboard.LeaderboardData):
    def __init__(self):
        super().__init__('levels')
        self.leaderboard_title = "Server XP"

        self.schema = {"user_id" : int, "message_count" : int, "voice_chat_time": int, "xp": int, "last_xp_message_time": int}
        self.defaults = {"message_count" : 0, "voice_chat_time": 0, "xp": 0, "last_xp_message_time": 0}
        self.default_column = "xp"
    
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
        level_manager = LevelManager()
        leaderboard = level_manager.get_leaderboard(message.author)

        last_xp_time = level_manager.get_member_score(message.author, leaderboard, column_name="last_xp_message_time")
        message_time = int(datetime.datetime.timestamp(message.created_at))
        
        if (message_time - last_xp_time) < 60:
            return
        
        level_manager.set_score(message.author, message_time, column_name="last_xp_message_time")
        

        level_manager.change_message_count(message.author, 1, leaderboard=leaderboard)

        level_manager.change_xp(message.author, 20, leaderboard=leaderboard)
