import pathlib
import sqlite3
import logging

database_name = 'Elliot.sqlite'
database_path = pathlib.Path(f'Storage/{database_name}')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def ensure_table_exists(name: str, name_type_dict: dict[str, type]):
    '''
        Checks that the input table exists in the database, and creates it if it doesn't

        Parameters:
            - `name`: str; The name of the table to check
    '''
    try:
        if not does_table_exist(name):
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"CREATE TABLE {name} {get_columns_string(name_type_dict)}")
                logger.info(f'Created new {name=} table')
    except Exception as e:
        logger.error(f'Failed to ensure {name=} table exists', exc_info=e)
        raise e

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

def update_columns(name: str, name_type_dict: dict[str, type]):
    '''
        Adds any missing columns to the input table based on the input dictionary

        Parameters:
            - `name`: str; The name of the table to check
            - `name_type_dict`: dict[str, type]; A dictionary containing pairs of column names and types
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            columns = cur.execute(f'PRAGMA table_info({name})').fetchall()
            columns_list = [column[1] for column in columns]
            for col_name, type in name_type_dict.items():
                if col_name in columns_list:
                    continue
                cur.execute(f"ALTER TABLE {name} ADD {col_name} {type_to_typename(type)}")
                logger.info(f'Created new table column {col_name=} of type={type_to_typename(type)}')
    except Exception as e:
        logger.error(f'Failed to update {name=} database columns', exc_info=e)
        raise e

def does_table_exist(name: str):
    '''
        Checks if the input table exists

        Parameters:
            - `name`: str; The name of the table to check
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            table = cur.execute(f"SELECT * FROM sqlite_master WHERE type='table' AND name='{name}'").fetchone()
            if table == None:
                return False
            else:
                return True
    except Exception as e:
        logger.error(f'Failed to check that {name=} table exists', exc_info=e)
        raise e