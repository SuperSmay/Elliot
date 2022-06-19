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


