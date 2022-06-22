from mee6_py_api import API
import asyncio
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # https://stackoverflow.com/questions/16780014/import-file-from-parent-directory
import Levels

# Fake guild to skip discord API
class LeaderboardGuild:
    def __init__(self, id) -> None:
        self.id = id

# Fake member to skip discord API
class LeaderboardMember:
    def __init__(self, id, guild_id) -> None:
        self.id = id
        self.guild = LeaderboardGuild(guild_id)

mee6API = API(811369107181666343)

async def run_api():
    level_manger = Levels.LevelManager()
    for i in range(20):
        leaderboard_page = await mee6API.levels.get_leaderboard_page(i)
        for player in leaderboard_page['players']:
            print(player['username'])
            member = LeaderboardMember(int(player['id']), int(player['guild_id']))
            level_manger.set_score(member, int(player['message_count']), column_name='message_count')
            level_manger.set_score(member, int(player['message_count'])*20, column_name='xp')
        

def main():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_api())

if __name__ == "__main__":
    main()