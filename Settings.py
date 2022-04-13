import discord
from discord.ext import commands, tasks
import sqlite3
import pathlib
import logging

database_name = 'Elliot.sqlite'
database_path = pathlib.Path(database_name)

DEFAULT_SETTINGS = {
    'cafe_mode': 0,
    'prefix': 'eli '
}

SETTINGS_NAMES = {
    'cafe_mode': 'Café Mode',
    'prefix': 'Prefix'
}

SETTINGS_DESCRIPTIONS = {
    'cafe_mode': 'Changes some wordings to be café themed',
    'prefix': 'The prefix for prefix commands'
}

SETTINGS_TYPES = {
    'cafe_mode': bool,
    'prefix': str
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Settings(commands.Cog):
    def __init__(self):
        ensure_table_exists()
        update_columns()

    @commands.command(name='config', description='Show\'s the current config')
    async def config_prefix(self, ctx):
        await ctx.reply(embed=self.get_config_embed(ctx.guild.id, 0), mention_author=False)

    @commands.slash_command(name='config', description='Show\'s the current config')
    async def config_slash(self, ctx):
        await ctx.respond(embed=self.get_config_embed(ctx.guild.id, 0))


    
    def get_config_embed(self, guild_id, page:int):
        max_page = max((len(DEFAULT_SETTINGS) - 1)//10, 0)
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ Current Settings ☾∘∙⊱⋅•⋅', description='Shows current bot configuration')
        for setting in list(DEFAULT_SETTINGS.keys())[10*page: 10*(page + 1)]:
            embed.add_field(name=f'{SETTINGS_NAMES[setting]} - {fetch_setting(guild_id, setting)}', value=SETTINGS_DESCRIPTIONS[setting])
        embed.set_footer(text=f'Page {min(page+1, max_page + 1)} of {max_page + 1}')
        return embed


#region Database handling
def ensure_table_exists():
    '''
        Checks that the settings table exists in the database, and creates it if it doesn't
    '''
    try:
        if not does_table_exist():
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"CREATE TABLE settings {get_columns_string()}")
                logger.info('Created new settings table')
    except Exception as e:
        logger.error('Failed to ensure settings table exists', exc_info=e)
        raise e

def get_columns_string():
    '''
        Creates and returns the string used to create the columns for a new table based on the DEFAULT_SETTINGS dict
    '''
    complete_string = ''
    for setting in DEFAULT_SETTINGS.keys():
        complete_string += f'{setting} {type_to_typename(SETTINGS_TYPES[setting])},'
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

def update_columns():
    '''
        Adds any missing columns to the settings table
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            columns = cur.execute('PRAGMA table_info(settings)').fetchall()
            for setting in DEFAULT_SETTINGS.keys():
                if setting in [column[1] for column in columns]:
                    continue
                cur.execute(f"ALTER TABLE settings ADD {setting} {type_to_typename(SETTINGS_TYPES[setting])}")
                logger.info(f'Created new table column {setting} of type {type_to_typename(SETTINGS_TYPES[setting])}')
                cur.execute(f"UPDATE settings SET {setting} = (?)", [DEFAULT_SETTINGS[setting]])
                logger.info(f'Set column {setting} to {DEFAULT_SETTINGS[setting]}')
    except Exception as e:
        logger.error('Failed to update settings database columns', exc_info=e)
        raise e

def does_table_exist():
    '''
        Checks if the settings table exists
    '''
    try:
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            table = cur.execute(f"SELECT * FROM sqlite_master WHERE type='table' AND name='settings'").fetchone()
            if table == None:
                return False
            else:
                return True
    except Exception as e:
        logger.error('Failed to check that settings table exists', exc_info=e)
        raise e

def process_setting_value(raw_setting, setting_type):
    '''
        Returns the raw setting value formatted correctly using SETTINGS_TYPES. Unknown types are returned as the raw value

        Parameters:
            - `raw_setting`: Any; The value to format
            - `setting_type`: type; The type to format as

        Returns:
            `Any`; The formatted input
    '''
    if setting_type == str:
        return str(raw_setting)
    elif setting_type == bool:
        return bool(raw_setting)
    elif setting_type == int:
        return int(raw_setting)
    elif setting_type == float:
        return float(raw_setting)
    elif setting_type == list:
        return str(raw_setting).split('%list_separator;%')
    else:
        return raw_setting

def fetch_setting(guild_id, setting):
    '''
        Returns the setting requested by name for the given guild id. Returns default value if guild is not in database or if the setting value is empty

        Parameters:
            - `guild_id`: int; The guild id to get the setting for
            - `setting`: str; The setting name

        Returns:
            `Any`; The setting value
    '''
    if setting not in DEFAULT_SETTINGS: raise ValueError(setting)
    raw_setting = fetch_all_settings(guild_id)[setting]
    if raw_setting == 'NULL':
        return DEFAULT_SETTINGS[setting]
    else:
        setting_type = SETTINGS_TYPES[setting] if setting in SETTINGS_TYPES else int
        return process_setting_value(raw_setting, setting_type)

def fetch_all_settings(guild_id):
    '''
        Returns the setting row requested by guild id. Returns default values if guild is not in database

        Parameters:
            - `guild_id`: int; The guild id to get the settings for

        Returns:
            `sqlite3.Row`; The settings row
    '''
    try:
        if is_guild_known(guild_id):
            with sqlite3.connect(database_path) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                row = cur.execute(f"SELECT * FROM settings WHERE guild_id = {guild_id}").fetchone()
                logger.info(f'Fetched all settings for guild_id={guild_id}')
                return row
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f'Failed to fetch all settings from database row guild_id={guild_id}', exc_info=e)
        raise e

def set_setting(guild_id, setting, value):
    '''
        Changes the setting requested by name for the given guild id to the given value

        Parameters:
            - `guild_id`: int; The guild id to set the setting for
            - `setting`: str; The setting name
            - `value`: Any; The setting name
    '''
    if type(value) != SETTINGS_TYPES[setting]: raise TypeError(value)
    if not is_guild_known(guild_id):
        initialize_guild(guild_id)
    try:
        if type(value) == list:  #TODO split into separate function
            value = value.join('%list_separator;%')
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE settings SET {setting} = (?) WHERE guild_id = {guild_id}", [value])
            logger.info(f'Changed setting {setting} to {value} for guild_id={guild_id}')
    except Exception as e:
        logger.error(f'Changing setting {setting} to {value} failed', exc_info=e)
        raise e

def set_default_settings(guild_id):
    '''
        Removes the given guild id from the database

        Parameters:
            - `guild_id`: int; The guild id to remove
    '''
    try:
        if is_guild_known(guild_id):
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"DELETE FROM settings WHERE guild_id = {guild_id}")
                logger.info(f'Deleting server row {guild_id} to reset to default')
    except Exception as e:
        logger.error('Failed to delete settings database row guild_id={guild_id}', exc_info=e)
        raise e

def initialize_guild(guild_id):
    '''
        Adds the given guild id to the database with empty settings

        Parameters:
            - `guild_id`: int; The guild id to add
    '''
    try:
        if not is_guild_known(guild_id):
            values = [guild_id]
            values.extend(['NULL' for i in DEFAULT_SETTINGS])
            #values.extend(DEFAULT_SETTINGS.values())
            with sqlite3.connect(database_path) as con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO settings VALUES ({'?,'*(len(DEFAULT_SETTINGS))}?)", values)
                logger.info(f'Guild row {guild_id} initialized')
    except Exception as e:
        logger.error('Failed to initalize settings database row guild_id={guild_id}', exc_info=e)
        raise e

def is_guild_known(guild_id):
    '''
        Returns whether the guild is in the database or not

        Parameters:
            - `guild_id`: int; The guild id to search for

        Returns:
            `bool`; Whether the guild is in the database or not
    '''
    try:
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            row = cur.execute(f"SELECT * FROM settings WHERE guild_id = {guild_id}").fetchone()
            if row != None:
                return True
            else:
                return False
    except Exception as e:
        logger.error(f'Failed to check if guild_id={guild_id} is known', exc_info=e)
        raise e
#endregion

if __name__ == '__main__':

    def fetch_table(table_name):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            table = cur.execute(f"SELECT * from {table_name}").fetchall()
            return table

    def delete_table(table_name):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"DROP TABLE {table_name}")

    def list_columns(table_name):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            columns = cur.execute(f'PRAGMA table_info({table_name})').fetchall()
            return columns

    ensure_table_exists()
    update_columns()
    #set_setting(866160840037236736, 'cafe_mode', False)
    print(fetch_table('settings'))
    print(fetch_setting(866160840037236736, 'prefix'))
    print(list_columns('settings'))

    