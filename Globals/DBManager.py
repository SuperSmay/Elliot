import os
import pathlib
import sqlite3
import logging
from typing import Any, Literal

global_database_name = 'Elliot.sqlite'
global_database_path = pathlib.Path(f'Storage/{global_database_name}')
guild_database_name = 'ElliotGuild.sqlite'
guild_database_path = pathlib.Path(f'Storage/{guild_database_name}')
user_database_name = 'ElliotUser.sqlite'
user_database_path = pathlib.Path(f'Storage/{user_database_name}')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def initialize_row(table_name, database_path, primary_column: str, primary_value, copy_previous_row=False):
    '''
        Adds the given day slot to the database with empty statistics

        Parameters:
            - `table_name`: str; The table to search for
            - `database_path`: pathlib.Path; The path to search for the database
            - `time`: int; The time key to add
    '''
    try:
        if not is_row_known(table_name, database_path, primary_column, primary_value):
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                con.row_factory = sqlite3.Row
                row = cur.execute(f"SELECT * FROM {table_name} WHERE {primary_column} = (SELECT MAX({primary_column}) FROM {table_name})").fetchone()
                if row is not None and copy_previous_row:
                    values = [primary_value] + list(row)[1:]
                    cur.execute(f"INSERT INTO {table_name} VALUES ({'?,'*(len(row)-1)}?)", values)
                else:
                    cur.execute(f"INSERT INTO {table_name} ({primary_column}) VALUES (?)", [primary_value])
                logger.info(f'{primary_column} row {primary_value=} initialized')
    except Exception as e:
        logger.error(f'Failed to initalize {table_name} database row {primary_value=}', exc_info=e)
        raise e

def is_row_known(table_name, database_path, primary_column: str, primary_value):
    '''
        Returns whether the primary value is in the database or not

        Parameters:
            - `table_name`: str; The table to search for
            - `database_path`: pathlib.Path; The path to search for the database
            - `primary_column`: str; The name of the column to search
            - `primary_value`: Any; The time to search for

        Returns:
            `bool`; Whether the time is in the database or not
    '''
    try:
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            row = cur.execute(f"SELECT * FROM {table_name} WHERE {primary_column} = {primary_value}").fetchone()
            if row != None:
                return True
            else:
                return False
    except Exception as e:
        logger.error(f'Failed to check if {primary_value=} is known', exc_info=e)
        raise e

def ensure_table_exists(name: str,  primary_column_name: str, primary_column_type, mode: Literal['global', 'guild', 'user']='global', id: int=None):
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
                cur.execute(f"CREATE TABLE {real_name} ({primary_column_name} {type_to_typename(primary_column_type)} PRIMARY KEY)")  # Ruh roh
                logger.info(f'Created new {real_name} table in database {mode}')
    except Exception as e:
        logger.error(f'Failed to ensure {real_name} ({mode}) table exists', exc_info=e)
        raise e

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

def get_columns_string(name_type_dict: dict[str, type]) -> str:
    '''
        Creates and returns the string used to create the columns for a new table based on the `name_type_dict` dict

        Parameters:
            - `name_type_dict`: dict[str, type]; A dictionary containing pairs of column names and types

        Returns:
            `str`; The SQLite string used to create a new table with the input dictionary
    '''
    complete_string = ''
    for col_name, type in name_type_dict.items():
        complete_string += f'{col_name} {type_to_typename(type)},'
    return f'(guild_id INTEGER, {complete_string} PRIMARY KEY("guild_id"))'
    
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

def update_columns(table_name, database_path, name_type_dict: dict[str, type], defaults: dict=None, allow_null=False):
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
            for col_name, type in name_type_dict.items():
                if col_name in columns_list:
                    continue
                if defaults is None:
                    default_value = None
                elif col_name in defaults:
                    default_value = defaults[col_name]
                else:
                    default_value = None
                cur.execute(f"ALTER TABLE {table_name} ADD {col_name} {type_to_typename(type)} DEFAULT {default_value} {'' if allow_null else 'NOT NULL'}")
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
        if not pathlib.Path.exists(database_path.parent):
            os.makedirs(database_path.parent)
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

def get_exlcude_string(column_list, exclude_value):
    if len(column_list) == 0:
        return ''

    exlude_strings = []
    for name in column_list:
        exlude_strings.append(f"{name} != {exclude_value}")

    return f"WHERE {'or'.join(exlude_strings)}"


def test():
    ensure_table_exists('test_table', 'test_id', int, mode='guild', id=1234)

if __name__ == "__main__":
    test()