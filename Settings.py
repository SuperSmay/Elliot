import discord
from discord.ext import commands, tasks
import sqlite3
import pathlib
import logging

from globalVariables import bot

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
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ {bot.user.name}\'s Current Settings ☾∘∙⊱⋅•⋅', description='Shows current bot configuration')
        for setting in list(DEFAULT_SETTINGS.keys())[10*page: 10*(page + 1)]:
            embed.add_field(name=f'{SETTINGS_NAMES[setting]} - {fetch_setting(guild_id, setting)}', value=SETTINGS_DESCRIPTIONS[setting])
        embed.set_footer(text=f'Page {min(page+1, max_page + 1)} of {max_page + 1}')
        return embed

def ensure_table_exists():
    if not does_table_exist():
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"CREATE TABLE settings {get_columns_string()}")
            logger.info('Created new settings table')

def get_columns_string():
    complete_string = ''
    for setting in DEFAULT_SETTINGS.keys():
        complete_string += f'{setting} {type_to_typename(SETTINGS_TYPES[setting])}'
    return f'(guild_id INTEGER, {complete_string})'
    
def type_to_typename(type):
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
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()
        columns = cur.execute('PRAGMA table_info(settings)').fetchall()
        for setting in DEFAULT_SETTINGS.keys():
            if setting in columns:
                continue
            column_string = f'{setting} {type_to_typename(SETTINGS_NAMES[setting])}'
            cur.execute(f"ALTER TABLE settings ADD {column_string}")
            cur.execute(f"UPDATE settings SET {setting} = {DEFAULT_SETTINGS[setting]}")

def does_table_exist():
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()
        table = cur.execute(f"SELECT * FROM sqlite_master WHERE type='table' AND name='settings'").fetchone()
        if table == None:
            return False
        else:
            return True

def process_setting_value(raw_setting, setting_type):
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
    raw_setting = fetch_all_settings(guild_id)[setting]
    setting_type = SETTINGS_TYPES[setting] if setting in SETTINGS_TYPES else int
    return process_setting_value(raw_setting, setting_type)

def fetch_all_settings(guild_id):
    if is_guild_known(guild_id):
        with sqlite3.connect(database_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            row = cur.execute(f"SELECT * FROM settings WHERE guild_id = {guild_id}").fetchone()
            return row
    else:
        return DEFAULT_SETTINGS.copy()

def set_setting(guild_id, setting, value):
    if not is_guild_known(guild_id):
        initialize_guild(guild_id)
    try:
        if type(value) == list:
            value = value.join('%list_separator;%')
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE settings SET {setting} = (?) WHERE guild_id = {guild_id}", [value])
    except Exception as e:
        logger.error(f'Changing setting {setting} to {value} failed', exc_info=e)
        raise e

def set_default_settings(guild_id):
    if is_guild_known(guild_id):
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM settings WHERE guild_id = {guild_id}")
            logger.info(f'Deleting server row {guild_id} to reset to default')
            set_default_settings(guild_id)

def initialize_guild(guild_id):
    values = [guild_id]
    values.extend(DEFAULT_SETTINGS.values())
    with sqlite3.connect(database_path) as con:
        cur = con.cursor()
        cur.execute(f"INSERT INTO settings VALUES ({'?,'*(len(DEFAULT_SETTINGS))}?)", values)
        logger.info(f'Server row {guild_id} initialized')

def is_guild_known(guild_id):
    with sqlite3.connect(database_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        row = cur.execute(f"SELECT * FROM settings WHERE guild_id = {guild_id}").fetchone()
        if row != None:
            return True
        else:
            return False

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
    set_setting(866160840037236736, 'cafe_mode', False)
    print(fetch_table('settings'))
    print(list_columns('settings'))

    