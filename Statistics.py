import datetime
from typing import Literal
import discord
from discord.ext import commands
from discord.commands import Option, OptionChoice, SlashCommandGroup, SlashCommand

import sqlite3
import logging
import pathlib

import DBManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

global_database_name = 'Elliot.sqlite'
global_database_path = pathlib.Path(f'Storage/{global_database_name}')
guild_database_name = 'ElliotGuild.sqlite'
guild_database_path = pathlib.Path(f'Storage/{guild_database_name}')
user_database_name = 'ElliotUser.sqlite'
user_database_path = pathlib.Path(f'Storage/{user_database_name}')


class Statistics(commands.Cog):
    ...

def get_time_slot():
    time = datetime.datetime.now().timestamp()
    current_time_slot = round((time//86400))*86400  # Round down to last day (UTC)
    return current_time_slot
    
def log_event(event_name, ctx: discord.ApplicationContext=None, modes: list[Literal['global', 'guild', 'user']]=None, id: int=None):
    '''
        Logs an event by name. If a ctx object is provided then also logs the event for the given user and guild.
        If mode is defined, then the event will be globally logged in addition to being logged to the id provided.

        Parameters:
            - `event_name`: str; The name of the event to log
            - `ctx`: discord.ApplicationContext; The context of the log. Optional
            - `modes`: list; The modes to log in. Defaults to global only when no ctx is provided, but defaults to all when a ctx is provided
            - `id`: int; The id of the user/guild when no ctx is provided
    '''
    if ctx is not None and not (isinstance(ctx, discord.ApplicationContext) or isinstance(ctx, discord.ext.commands.context.Context)):
        raise TypeError(ctx)
    if modes is not None and not isinstance(modes, list):
        raise TypeError(modes)
    if id is not None and not isinstance(id, int):
        raise TypeError(id)

    # Global
    if modes is None or 'global' in modes:
        DBManager.ensure_table_exists('statistics', 'time', int)

        count = fetch_current_event_count(event_name, 'global')
        count += 1
        change_current_event_count_to(event_name, count, 'global')

    # Guild
    if ctx is not None and (modes is None or 'guild' in modes):
        
        DBManager.ensure_table_exists('statistics', 'time', int, 'guild', ctx.guild.id)

        count = fetch_current_event_count(event_name, 'guild', ctx.guild.id)
        count += 1
        change_current_event_count_to(event_name, count, 'guild', ctx.guild.id)

    elif ctx is None and modes is not None and 'guild' in modes and id is not None:
        DBManager.ensure_table_exists('statistics', 'time', int, 'guild', id)

        count = fetch_current_event_count(event_name, 'guild', id)
        count += 1
        change_current_event_count_to(event_name, count, 'guild', id)

    # User
    if ctx is not None and (modes is None or 'user' in modes):
        
        DBManager.ensure_table_exists('statistics', 'time', int, 'user', ctx.author.id)

        count = fetch_current_event_count(event_name, 'user', ctx.author.id)
        count += 1
        change_current_event_count_to(event_name, count, 'user', ctx.author.id)
    elif ctx is None and modes is not None and 'user' in modes and id is not None:
        DBManager.ensure_table_exists('statistics', 'time', int, 'user', id)

        count = fetch_current_event_count(event_name, 'user', id)
        count += 1
        change_current_event_count_to(event_name, count, 'user', id)


def change_current_event_count_to(event_name, count, mode: Literal['global', 'guild', 'user']='global', id=None):

    time = get_time_slot()

    if mode == 'global':
        table_name = 'statistics'
        database_path = global_database_path
    elif mode == 'guild':
        if id is None: raise ValueError(id)
        table_name = f'statistics_{id}'
        database_path = guild_database_path
    elif mode == 'user':
        if id is None: raise ValueError(id)
        table_name = f'statistics_{id}'
        database_path = user_database_path
    else:
        raise ValueError(mode)

    if DBManager.is_row_known(table_name, database_path, 'time', time):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE {table_name} SET {event_name} = (?) WHERE time = {time}", [count])
            logger.info(f'Changed {table_name} {event_name} to {count} for {time=}')
    else:
        DBManager.initialize_row(table_name, database_path, 'time', time, copy_previous_row=True)
        change_current_event_count_to(event_name, count, mode, id)

def fetch_current_event_count(event_name, mode: Literal['global', 'guild', 'user']='global', id: int=None):
    
    if mode == 'global':
        real_name = 'statistics'
        database_path = global_database_path
    elif mode == 'guild':
        if id is None: raise ValueError(id)
        real_name = f'statistics_{id}'
        database_path = guild_database_path
    elif mode == 'user':
        if id is None: raise ValueError(id)
        real_name = f'statistics_{id}'
        database_path = user_database_path
    else:
        raise ValueError(mode)

    DBManager.update_columns(real_name, database_path, {event_name: int}, defaults={event_name: 0})

    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
    row = cur.execute(f"SELECT * FROM {real_name} WHERE time = (SELECT MAX(time) FROM {real_name})").fetchone()
    
    if row is not None:
        count = row[event_name]
        return count
    else:
        return 0
    
if __name__ == '__main__':
    DBManager.ensure_table_exists('statistics', 'time', int)  
    log_event('test')