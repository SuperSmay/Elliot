import datetime
from typing import Literal
import discord
from discord.ext import commands
from discord.commands import Option, OptionChoice, SlashCommandGroup, SlashCommand

import sqlite3
import logging
import pathlib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

def get_database_info(name: str, mode: Literal['global', 'guild', 'user']='global', id: int=None):
    '''
        Gets database info from given input

        Parameters:
            - `name`: str; The name of the table to check
            - `mode`: str; The type of table to check
            - `id`: int; The id of the table to check

        Returns:
            (real_name: str; The real name of the database to access, database_path: pathlib.Path; The path to the database)
    '''
    if mode not in ['global', 'guild', 'user']:
        raise ValueError(mode)
        
    if mode == 'global':
        real_name = name
        database_path = global_database_path
        return real_name, database_path

    if not isinstance(id, int):  # ID is required after this point
        raise TypeError(id)

    if mode == 'guild':
        real_name = f'{name}_{id}'
        database_path = guild_database_path
        return real_name, database_path

    if mode == 'user':
        real_name = f'{name}_{id}'
        database_path = user_database_path
        return real_name, database_path

    

def log_event(event_name, ctx=None, modes: list[Literal['global', 'guild', 'user']]=None, id: int=None):
    '''
        Logs an event by name. If a ctx object is provided then also logs the event for the given user and guild.
        If mode is defined, then the event will be globally logged in addition to being logged to the id provided.

        Parameters:
            - `event_name`: str; The name of the table to check
            - `ctx`: discord.ApplicationContext; The name of the table to check
            - `modes`: list; The type of table to check
            - `id`: int; The id of the table to check

        Returns:
            (real_name: str; The real name of the database to access, database_path: pathlib.Path; The path to the database)
    '''
    if ctx is not None and not isinstance(ctx, discord.ApplicationContext):
        raise TypeError(ctx)
    if modes is not None and not isinstance(modes, list):
        raise TypeError(modes)
    if id is not None and not isinstance(id, int):
        raise TypeError(id)

    # Global
    if modes is None or 'global' in modes:
        ensure_table_exists('statistics')

        count = fetch_current_event_count(event_name, 'global')
        count += 1
        change_current_event_count_to(event_name, count, 'global')

    # Guild
    if ctx is not None and (modes is None or 'guild' in modes):
        
        ensure_table_exists('statistics', 'guild', ctx.guild.id)

        count = fetch_current_event_count(event_name, 'guild', ctx.guild.id)
        count += 1
        change_current_event_count_to(event_name, count, 'guild', ctx.guild.id)

    elif ctx is None and modes is not None and 'guild' in modes and id is not None:
        ensure_table_exists('statistics', 'guild', id)

        count = fetch_current_event_count(event_name, 'guild', id)
        count += 1
        change_current_event_count_to(event_name, count, 'guild', id)

    # User
    if ctx is not None and (modes is None or 'user' in modes):
        
        ensure_table_exists('statistics', 'user', ctx.author.id)

        count = fetch_current_event_count(event_name, 'user', ctx.author.id)
        count += 1
        change_current_event_count_to(event_name, count, 'user', ctx.author.id)
    elif ctx is None and modes is not None and 'user' in modes and id is not None:
        ensure_table_exists('statistics', 'user', id)

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

    if is_time_known(table_name, database_path, time):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE {table_name} SET {event_name} = (?) WHERE time = {time}", [count])
            logger.info(f'Changed {table_name} {event_name} to {count} for {time=}')
    else:
        initialize_time(table_name, database_path, time)
        change_current_event_count_to(event_name, count, mode, id)

def fetch_current_event_count(event_name, mode: Literal['global', 'guild', 'user']='global', id=None):
    
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

    update_columns(real_name, database_path, [event_name])

    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
    row = cur.execute(f"SELECT * FROM {real_name} WHERE time = (SELECT MAX(time) FROM {real_name})").fetchone()
    
    if row is not None:
        count = row[event_name]
        return count
    else:
        return 0

def ensure_table_exists(name: str, mode: Literal['global', 'guild', 'user']='global', id: int=None):
    '''
        Checks that the input table exists in the database, and creates it if it doesn't

        Parameters:
            - `name`: str; The name of the table to check
            - `mode`: str; The type of table to check
            - `id`: int; The id of the table to check
    '''

    real_name, database_path = get_database_info(name, mode, id)

    try:
        if not does_table_exist(name, mode, id):
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"CREATE TABLE {real_name} (time INTEGER PRIMARY KEY)")
                logger.info(f'Created new {real_name} table in database {mode}')
    except Exception as e:
        logger.error(f'Failed to ensure {real_name} ({mode}) table exists', exc_info=e)
        raise e

    
def type_to_typename(type):
    '''
        Returns the proper SQLite type name to use for the given type. If type is unknown then BLOB is returned

        Parameters:
            - `type`: type; The type to convert

        Returns:
            `str`; The formatted type name
    '''
    if type == str:
        return 'TEXT'
    elif type == int:
        return 'INTEGER'
    elif type == float:
        return 'REAL'
    elif type == list:
        return 'TEXT'
    elif type == bool:
        return 'INTEGER'
    else:
        return 'BLOB'

def update_columns(table_name, database_path, name_list: list[str]):
    '''
        Adds any missing columns to the input table based on the input dictionary

        Parameters:
            - `table_name`: str; The table to search for
            - `database_path`: pathlib.Path; The path to search for the database
            - `name_list`: list[str]; A list  of column names
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            columns = cur.execute(f'PRAGMA table_info({table_name})').fetchall()
            columns_list = [column[1] for column in columns]
            for col_name in name_list:
                if col_name in columns_list:
                    continue
                cur.execute(f"ALTER TABLE {table_name} ADD {col_name} INTEGER DEFAULT 0 NOT NULL")
                logger.info(f'Created new table column {col_name=} of type=int')
    except Exception as e:
        logger.error(f'Failed to update {table_name} database columns', exc_info=e)
        raise e

def does_table_exist(name: str, mode: Literal['global', 'guild', 'user']='global', id: int=-1):
    '''
        Checks if the input table exists

        Parameters:
            - `name`: str; The name of the table to check
            - `mode`: str; The type of table to check
            - `id`: int; The id of the table to check
    '''
    
    real_name, database_path = get_database_info(name, mode, id)

    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            table = cur.execute(f"SELECT * FROM sqlite_master WHERE type='table' AND name='{real_name}'").fetchone()
            if table == None:
                return False
            else:
                return True
    except Exception as e:
        logger.error(f'Failed to check that {real_name} table exists', exc_info=e)
        raise e

def initialize_time(table_name, database_path, time):
    '''
        Adds the given day slot to the database with empty statistics

        Parameters:
            - `table_name`: str; The table to search for
            - `database_path`: pathlib.Path; The path to search for the database
            - `time`: int; The time key to add
    '''
    try:
        if not is_time_known(table_name, database_path, time):
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                con.row_factory = sqlite3.Row
                row = cur.execute(f"SELECT * FROM {table_name} WHERE time = (SELECT MAX(time) FROM {table_name})").fetchone()
                if row is not None:
                    values = [time] + list(row)[1:]
                    cur.execute(f"INSERT INTO {table_name} VALUES ({'?,'*(len(row)-1)}?)", values)
                else:
                    cur.execute(f"INSERT INTO {table_name} (time) VALUES (?)", [time])
                logger.info(f'Time row {time=} initialized')
    except Exception as e:
        logger.error(f'Failed to initalize {table_name} database row {time=}', exc_info=e)
        raise e

def is_time_known(table_name, database_path, time):
    '''
        Returns whether the time is in the database or not

        Parameters:
            - `table_name`: str; The table to search for
            - `database_path`: pathlib.Path; The path to search for the database
            - `time`: int; The time to search for

        Returns:
            `bool`; Whether the time is in the database or not
    '''
    try:
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            row = cur.execute(f"SELECT * FROM {table_name} WHERE time = {time}").fetchone()
            if row != None:
                return True
            else:
                return False
    except Exception as e:
        logger.error(f'Failed to check if {time=} is known', exc_info=e)
        raise e
    
if __name__ == '__main__':
    ensure_table_exists()  
    log_event('test')