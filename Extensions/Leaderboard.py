import datetime
import logging
import math
import sqlite3

import discord
from discord.commands import Option, OptionChoice
from discord.ext import commands

import Globals.DBManager as DBManager
from Globals.GlobalVariables import bot, numberEmoteList, on_log
from Extensions.Settings import fetch_setting
from Extensions.Statistics import log_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addFilter(on_log)

def setup(bot):
    bot.add_cog(Leaderboard())

class LeaderboardData():

    def __init__(self, internal_name):
        self.internal_name = internal_name

        #Options
        self.leaderboard_title = "Leaderboard"
        self.overwrite_old_score = True
        self.lower_score_better = False
        self.schema = {"user_id" : int, 'score' : int}
        self.defaults = {'score' : 0}
        self.units = ''
        self.default_column = 'score'

    #Get leaderboard 
    def get_leaderboard(self, member, column_name=None, exclude_names=None) -> list[dict]:
        column_name = column_name if column_name is not None else self.default_column
        exclude_names = exclude_names if exclude_names is not None else []
        DBManager.ensure_table_exists(f'{self.internal_name}_leaderboard', 'user_id', int, 'guild', member.guild.id)
        database_name, database_path = DBManager.get_database_info(f'{self.internal_name}_leaderboard', 'guild', member.guild.id)
        DBManager.update_columns(database_name, database_path, self.schema, self.defaults, False)
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            sort = 'ASC' if self.lower_score_better else 'DESC'
            exclude = DBManager.get_exlcude_string(exclude_names, 1)
            rows = cur.execute(f"SELECT * FROM {database_name} {exclude} ORDER BY {column_name} {sort}").fetchall()
            logger.info(f'Fetched leaderboard for guild_id={member.guild.id}')
            log_event('fetch_leaderboard', modes=['global', 'guild'], id=member.guild.id)
            return rows

    def get_member_score(self, member, leaderboard=None, column_name=None):
        column_name = column_name if column_name is not None else self.default_column
        leaderboard = self.get_leaderboard(member) if leaderboard is None else leaderboard
        for entry in leaderboard:
            if entry['user_id'] == member.id:
                return entry[column_name]
        if column_name in self.defaults:
            return self.defaults[column_name]
        return None

    def is_member_on_leaderboard(self, member):
        for entry in self.get_leaderboard(member):
            if entry["user_id"] == member.id: return True
        return False

    def get_user_index_on_leaderboard(self, member, leaderboard=None, exclude_names=None):
        index = 0
        leaderboard = self.get_leaderboard(member, exclude_names=exclude_names) if leaderboard is None else leaderboard
        while index < len(leaderboard):
            if leaderboard[index]["user_id"] == member.id: return index
            index += 1
        return -1

    #Edit 
    def set_score(self, member, score, column_name=None):
        column_name = column_name if column_name is not None else self.default_column
        DBManager.ensure_table_exists(f'{self.internal_name}_leaderboard', 'user_id', int, 'guild', member.guild.id)
        database_name, database_path = DBManager.get_database_info(f'{self.internal_name}_leaderboard', 'guild', member.guild.id)
        DBManager.update_columns(database_name, database_path, self.schema, self.defaults, False)
        if not DBManager.is_row_known(database_name, database_path, 'user_id', member.id):
            DBManager.initialize_row(database_name, database_path, 'user_id', member.id)
            self.on_row_init(member, column_name)
        if not self.overwrite_old_score:
            # We only need the old score if we need to check it for overwrite purposes
            old_score = self.get_member_score(member)
            if old_score is not None:
                # Cancel score set if the score is "worse"
                if self.lower_score_better and score > old_score:
                    return
                if not self.lower_score_better and old_score > score:
                    return

        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(f"UPDATE {database_name} SET {column_name} = (?) WHERE user_id = {member.id}", (score,))
            logger.info(f'Score {column_name} set to {score} for user_id={member.id}')
            return True
        return False
    
    def change_score(self, member, change, column_name):
        '''
        Change the score by the specified amount
        '''
        column_name = column_name if column_name is not None else self.default_column
        DBManager.ensure_table_exists(f'{self.internal_name}_leaderboard', 'user_id', int, 'guild', member.guild.id)
        database_name, database_path = DBManager.get_database_info(f'{self.internal_name}_leaderboard', 'guild', member.guild.id)
        DBManager.update_columns(database_name, database_path, self.schema, self.defaults, False)
        if not DBManager.is_row_known(database_name, database_path, 'user_id', member.id):
            DBManager.initialize_row(database_name, database_path, 'user_id', member.id)
            self.on_row_init(member, column_name)
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(f"UPDATE {database_name} SET {column_name} = {column_name} + {change} WHERE user_id = {member.id}")
            logger.info(f'Score {column_name} changed by {change} for user_id={member.id}')
            return True
        return False

    # Events
    def on_row_init(self, member, column_name):
        pass

    # Message to send
    def position_annoucenment(self, member):
        leaderboard = self.get_leaderboard(member)
        return f"Congratulations <@{member.id}>! You just got **{self.placement(member, leaderboard)}** on the {self.leaderboard_title} leaderboard with a score of **{self.get_member_score(member, leaderboard)}**!!"

    def placement(self, member, leaderboard=None, exclude_names=None):
        leaderboard = self.get_leaderboard(member, exclude_names=exclude_names) if leaderboard is None else leaderboard
        index = self.get_user_index_on_leaderboard(member, leaderboard)

        if index == 0:
            placement = "a __new record__"
        
        elif index % 10 == 1:
            placement = f"{index + 1}nd place"
        elif index % 10 == 2:
            placement = f"{index + 1}rd place"
        else:
            placement = f"{index + 1}th place"
        if index == 11:
            placement = "12th place"
        if index == 12:
            placement = "13th place"
        return placement

    # Create leaderboard
    async def get_leaderboard_embed(self, member, page_index = 0, column_name=None, exclude_names=None):
        leaderboard = self.get_leaderboard(member, column_name, exclude_names)
        embed = discord.Embed(title= f"⋅•⋅⊰∙∘☽{member.guild.name}'s {self.leaderboard_title} Leaderboard☾∘∙⊱⋅•⋅", color= 7528669)
        embed.add_field(name= "**Leaderboard**", value= self.leaderboard_string(await self.leaderboard_list(member, page_index, leaderboard, column_name)))
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text=f'Page {page_index + 1} of {math.ceil(len(leaderboard) / 10)}')
        return embed

    def get_position_number(self, index):
        try: return numberEmoteList[index]
        except: return numberEmoteList[9]

    # List of users
    async def leaderboard_list(self, member, page_index, leaderboard=None, column_name=None, exclude_names=None):
        column_name = column_name if column_name is not None else self.default_column
        exclude_names = exclude_names if exclude_names is not None else []
        leaderboard = self.get_leaderboard(member, exclude_names=exclude_names) if leaderboard is None else leaderboard
        leaderboard_list = []
        for position in leaderboard[page_index * 10:(page_index + 1) * 10]:
            index = leaderboard.index(position)
            leaderboard_list.append(await self.position_string(index, position, column_name))
        return leaderboard_list[:10]

    async def position_string(self, index, leaderboard_slot, column_name):
        position_number = self.get_position_number(index)
        try:
            member_name = (await bot.fetch_user(leaderboard_slot['user_id'])).name
        except discord.errors.NotFound:
            member_name = leaderboard_slot['user_id']
        score = leaderboard_slot[column_name] 
        return f'{position_number} - {member_name} - {score} {self.units}'

    def leaderboard_string(self, leaderboard_list):
        if len(leaderboard_list) == 0:
            return "This leaderboard is empty"
        return "\n".join(leaderboard_list)




class LeaveTimeLeaderboard(LeaderboardData):
    def __init__(self):
        super().__init__("leave_time")
        self.leaderboard_title = 'Leaver'
        self.lower_score_better = True
        self.units = 'seconds'

    def position_annoucenment(self, member):
        leaderboard = self.get_leaderboard(member)
        return f"Congratulations <@{member.id}>! You just got **{self.placement(member, leaderboard)}** for fastest leaver with a time of **{self.get_member_score(member, leaderboard)}** seconds!!"


class WeeklyLeaveTimeLeaderboard(LeaderboardData):
    def __init__(self):
        super().__init__("weekly_leave_time")
        self.leaderboard_title = "7 day leaver"
        self.lower_score_better = True
        self.schema = {"user_id" : int, "score" : int, "join_time": int}
        self.defaults = {"score" : 0}
        self.units = 'seconds'

    def set_score(self, member, score):

        leaderboard = self.get_leaderboard(member)

        if len(leaderboard) == 0 or (datetime.datetime.timestamp(datetime.datetime.now()) - leaderboard[0]["join_time"]) > 604800 or score < leaderboard[0]["score"]:
            DBManager.ensure_table_exists(f'{self.internal_name}_leaderboard', 'user_id', int, 'guild', member.guild.id)
            database_name, database_path = DBManager.get_database_info(f'{self.internal_name}_leaderboard', 'guild', member.guild.id)
            DBManager.update_columns(database_name, database_path, self.schema, self.defaults, False)
            with sqlite3.connect(database_path) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute(f"DELETE FROM {database_name}")
                cur.execute(f"REPLACE INTO {database_name} (user_id, score, join_time) VALUES ({member.id}, {score}, {int(datetime.datetime.timestamp(datetime.datetime.now()))})")
                return True

    def position_annoucenment(self, member):
        leaderboard = self.get_leaderboard(member)
        return f"Congratulations <@{member.id}>! You just got **{self.placement(member, leaderboard)}** for fastest 7 day leaver with a time of **{self.get_member_score(member, leaderboard)}** seconds!!"

class Leaderboard(commands.Cog, name='Leaderboards'):

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        time_since_join = (datetime.datetime.now(datetime.timezone.utc) - member.joined_at).total_seconds()
        if time_since_join <= 360:
            score = round(time_since_join, 2)
            leaderboard = LeaveTimeLeaderboard()
            announce = leaderboard.set_score(member, score)
            if leaderboard.get_user_index_on_leaderboard(member) < 10 and announce:
                channel_id = fetch_setting(member.guild.id, 'welcome_channel')
                if channel_id is None: return
                channel = await bot.fetch_channel(channel_id)
                await channel.send(leaderboard.position_annoucenment(member))
            
            leaderboard = WeeklyLeaveTimeLeaderboard()
            announce = leaderboard.set_score(member, score)
            if leaderboard.get_user_index_on_leaderboard(member) < 1 and announce:
                channel_id = fetch_setting(member.guild.id, 'welcome_channel')
                if channel_id is None: return
                channel = await bot.fetch_channel(channel_id)
                await channel.send(leaderboard.position_annoucenment(member))

    @commands.slash_command(name="leaderboard", description="Shows a leaderboard")
    async def leaderboard_slash(self, ctx, leaderboard:Option(str, description='Leaderboard to show', choices=[OptionChoice('Weekly top leaver time', 'weekly'), OptionChoice('Top 10 leaver times', 'leaver')], required=False, default='leaver')):
        log_event('slash_command', ctx=ctx)
        log_event('leaderboard_command', ctx=ctx)
        if leaderboard == 'weekly':
            leaderboard_data = WeeklyLeaveTimeLeaderboard()
        elif leaderboard == 'leaver':
            leaderboard_data = LeaveTimeLeaderboard()
        embed = await leaderboard_data.get_leaderboard_embed(ctx.author)
        await ctx.respond(embed=embed)

    @commands.command(name="leaderboard", aliases=['leaverboard'], description="Shows a leaderboard")
    async def leaderboard_prefix(self, ctx, leaderboard='leaver'):
        if leaderboard == 'weekly':
            leaderboard_data = WeeklyLeaveTimeLeaderboard()
        else:
            leaderboard_data = LeaveTimeLeaderboard()
        embed = await leaderboard_data.get_leaderboard_embed(ctx.author)
        await ctx.reply(embed=embed, mention_author= False)