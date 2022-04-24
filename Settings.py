from fnmatch import fnmatch
import discord
from discord.ext import commands, tasks
from discord.commands import Option, OptionChoice, SlashCommandGroup

import DBManager

import sqlite3
import pathlib
import logging

database_name = 'Elliot.sqlite'
database_path = pathlib.Path(database_name)

ADD_ALIASES = ['add', 'a', 'append']
REMOVE_ALIASES = ['remove', 'r', 'rm', 'delete', 'yeet']
TRUE_ALIASES = ['on', 'enable', 'true']
FALSE_ALIASES = ['off', 'disable', 'false']
RESET_ALIASES = ['reset', 'none', 'default']

DEFAULT_SETTINGS = {  #Required settings dict, provides a default value and serves as the master list of settings
    'cafe_mode': 0,
    'prefix': 'eli',
    'welcome_channel' : None,
    'age_role_list' : [],
    'settings_roles' : [],
    'log_channel' : None,
}

SETTINGS_NAMES = {  #Required settings dict, provides a user-facing setting name
    'cafe_mode': 'Café Mode',
    'prefix': 'Prefix',
    'welcome_channel' : 'Welcome Channel',
    'age_role_list' : 'Age Roles',
    'settings_roles' : 'Settings Roles',
    'log_channel' : 'Log Channel',
}

SETTINGS_ALIASES = {  #Optional settings dict for other usable names
    'cafe_mode' : ['cafe mode', 'cafemode', 'cafe', 'cafémode', 'café', 'café_mode'],
    'welcome_channel' : ['welcome channel', 'welcomechannel', 'welcome'],
    'age_role_list' : ['age roles', 'age list', 'valid age roles', 'ageroles', 'agelist', 'validageroles', 'age_roles', 'age_list', 'valid_age_roles'],
    'settings_roles' : ['settings roles', 'settingsroles'],
    'log_channel' : ['log channel', 'logchannel', 'log'],
}

SETTINGS_DESCRIPTIONS = {  #Required settings dict, provides a description of the setting
    'cafe_mode': 'Changes some wordings to be café themed',
    'prefix': 'The prefix for prefix commands',
    'welcome_channel' : 'The channel to send welcome/goodbye messages in',
    'age_role_list' : 'List of valid age roles for verification',
    'settings_roles' : 'Roles that are allowed to change settings',
    'log_channel' : 'Channel to send log messages to',
}

SETTINGS_TYPES = {  #Required settings dict, provides the expected type of the setting value
    'cafe_mode': bool,
    'prefix': str,
    'welcome_channel' : int,
    'age_role_list' : list,
    'settings_roles' : list,
    'log_channel' : int,
}

LIST_TYPES = {
    'age_role_list' : int,
    'settings_roles' : int
}

ROLE_ID_SETTINGS = [
    'age_role_list', 
    'settings_roles',
]

CHANNEL_ID_SETTINGS = [
    'welcome_channel',
    'log_channel',
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Settings(commands.Cog):
    def __init__(self):
        
        validate_settings_dicts()

        name_type_dict = {name: SETTINGS_TYPES[name] for name in DEFAULT_SETTINGS}  # This is because the default settings dict is the master list and should be the only reference for which settings currently exist
        
        DBManager.ensure_table_exists('settings')
        DBManager.update_columns('settings', name_type_dict)

    config = SlashCommandGroup(name='config', description='Configuration commands', guild_ids=[866160840037236736])

    @commands.command(name='config', description='Shows the current config')  #FIXME Parse value with quotes and stuff
    async def config_prefix_command(self, ctx, input_name='list', value='', value_two=''):
        if input_name == 'list':
            await ctx.reply(embed=self.get_config_list_embed(ctx.guild.id, 0), mention_author=False)
        else:
            try:
                setting_name = self.get_internal_setting_name(input_name)  #raises ValueError if input is invalid, so we can assume that setting_name is valid
                if value == '':
                    await ctx.reply(embed=self.get_config_info_embed(ctx.guild.id, setting_name), mention_author=False)
                elif not self.has_settings_permission(ctx.guild, ctx.author):
                    return discord.Embed(description=f'You don\'t have permission for that!', color=16741747)
                else:
                    await ctx.reply(embed=self.run_config_change_command(ctx, setting_name, value, value_two), mention_author=False)
            except ValueError:
                return discord.Embed(description=f'Setting name `{input_name}` not found!', color=16741747)
                

    # @config.command(name='list', description='Shows the current config')
    # async def config_list(self, ctx):
    #     await ctx.respond(embed=self.get_config_list_embed(ctx.guild.id, 0))

    # @config.command(name='prefix', description='Change the current prefix')
    # async def config_prefix(self, ctx, prefix: Option(discord.enums.SlashCommandOptionType.string, description='The new prefix', required=False, default='')):
    #     await ctx.respond(embed=self.run_simple_config_change_command(ctx, 'prefix', prefix))

    def has_settings_permission(self, guild, member: discord.Member):
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        member_role_ids = [role.id for role in member.roles]
        for role_id in fetch_setting(member.guild.id, 'settings_roles'):
            if role_id in member_role_ids:
                return True
        return False
    
    def get_config_list_embed(self, guild_id, page:int):
        max_page = max((len(DEFAULT_SETTINGS) - 1)//10, 0)
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ Current Settings ☾∘∙⊱⋅•⋅', description='Shows current bot configuration', color=7528669)
        for setting_name in list(DEFAULT_SETTINGS.keys())[10*page: 10*(page + 1)]:
            setting_value = fetch_setting(guild_id, setting_name)
            embed.add_field(name=f'{SETTINGS_NAMES[setting_name]} - {self.get_formatted_value(setting_value, setting_name)}', value=SETTINGS_DESCRIPTIONS[setting_name])
        embed.set_footer(text=f'Page {min(page+1, max_page + 1)} of {max_page + 1}')
        return embed

    def get_config_info_embed(self, guild_id, setting_name):  #Assumes valid setting name
        if SETTINGS_TYPES[setting_name] == list:  #Use a different format for showing list configs
            return self.get_list_config_info_embed(guild_id, setting_name)
        else:
            return self.get_simple_config_info_embed(guild_id, setting_name)

    def get_simple_config_info_embed(self, guild_id, setting_name):
        setting_value = fetch_setting(guild_id, setting_name)
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ {SETTINGS_NAMES[setting_name]} ☾∘∙⊱⋅•⋅', description=f'{SETTINGS_DESCRIPTIONS[setting_name]}', color=7528669)
        embed.add_field(name=f'Currently set to:', value=self.get_formatted_value(setting_value, setting_name))
        embed.set_footer(text=f'Change this with /config <{setting_name}> <value>')
        return embed

    def get_list_config_info_embed(self, guild_id, setting_name):
        setting_value = fetch_setting(guild_id, setting_name)
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ {SETTINGS_NAMES[setting_name]} ☾∘∙⊱⋅•⋅', description=f'{SETTINGS_DESCRIPTIONS[setting_name]}', color=7528669)
        embed.add_field(name=f'Current list:', value=self.get_formatted_value(setting_value, setting_name))
        embed.set_footer(text=f'Change this with /config <{setting_name}> add/remove <value>')
        return embed

    #region AAAAAAAA

    def get_formatted_value(self, converted_setting_value, setting_name=None) -> str:  #Returns nicely formatted string
        #Setting name is used for determining if the value should be formatted as a channel/role mention
        if converted_setting_value is None:
            return 'None'
        if isinstance(converted_setting_value, list):
            return ', '.join([self.get_formatted_value(value_from_list, setting_name) for value_from_list in converted_setting_value])
        elif setting_name in ROLE_ID_SETTINGS and (isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str)):
            return f'<@&{converted_setting_value}>'
        elif setting_name in CHANNEL_ID_SETTINGS and (isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str)):
            return f'<#{converted_setting_value}>'
        elif isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str) or isinstance(converted_setting_value, float):
            return str(converted_setting_value)
        elif isinstance(converted_setting_value, bool):
            if converted_setting_value: return 'On'
            else: return 'Off'
        else:
            return str(converted_setting_value)
        

    def get_channel_id_for_input(self, guild: discord.Guild, value):
        if isinstance(value, str) and fnmatch(value, "<#*>"):
            value = value.replace('<#', '').replace('>','')
        elif isinstance(value, str):
            for channel in guild.channels:
                if value.replace('#','').replace('-','').replace(' ','') == channel.name.replace('-','').replace(' ',''):
                    value = channel.id
                    break
        try:
            int_value = int(value)
            if int_value in [channel.id for channel in guild.channels]:
                return int_value
        except ValueError as e:
            raise e

    def get_role_id_for_input(self, guild: discord.Guild, value):
        if isinstance(value, str) and fnmatch(value, "<@&*>"):
            value = value.replace('<@&', '').replace('>','')
        try:
            int_value = int(value)
            if int_value in [role.id for role in guild.roles]:
                return int_value
        except ValueError as e:
            raise e

    def convert_input_to_type(self, value, setting_type):
        if setting_type == str:
            return str(value)
        elif setting_type == bool:
            if value.lower() in TRUE_ALIASES: return True
            if value.lower() in FALSE_ALIASES: return False
            return bool(value)
        elif setting_type == int:
            return int(value)
        elif setting_type == float:
            return float(value)
        elif setting_type == list:
            return str(value).split('%list_separator;%')
        else:
            return value

    def run_config_change_command(self, ctx, setting_name: str, raw_input: str, raw_input_two: str):  #Assumes valid setting name

        if setting_name not in DEFAULT_SETTINGS: raise ValueError(setting_name)  #Dunno why this would happen but eh
        
        if SETTINGS_TYPES[setting_name] == list:
            if raw_input.lower() in ADD_ALIASES:
                is_add = True
            elif raw_input.lower() in REMOVE_ALIASES:
                is_add = False
            else:
                return discord.Embed(description=f'Specify add or remove, not `{input_value}`!', color=16741747)
            setting_type = LIST_TYPES[setting_name] if setting_name in LIST_TYPES else int  #Default to int if no type is provided
            input_value: str = raw_input_two

        else:
            setting_type = SETTINGS_TYPES[setting_name]
            input_value: str = raw_input
        
        #Converter section

        try:
            if input_value.lower() in RESET_ALIASES and not SETTINGS_TYPES[setting_name] == list:
                converted_value = None
            elif setting_name in ROLE_ID_SETTINGS:
                converted_value = self.get_role_id_for_input(ctx.guild, input_value)
            elif setting_name in CHANNEL_ID_SETTINGS:
                converted_value = self.get_channel_id_for_input(ctx.guild, input_value)
            else:
                converted_value = self.convert_input_to_type(input_value, setting_type)
        except ValueError:
            return discord.Embed(description=f'Invalid input value `{input_value}`!', color=16741747)

        #Actually do the thing

        if SETTINGS_TYPES[setting_name] == list:
            return self.run_list_config_change_command(ctx, setting_name, converted_value, is_add)
        else:
            return self.run_simple_config_change_command(ctx, setting_name, converted_value)
            

    def run_simple_config_change_command(self, ctx, setting_name, converted_value):
        set_setting(ctx.guild.id, setting_name, converted_value)
        return discord.Embed(description=f'Changed {SETTINGS_NAMES[setting_name]} to {self.get_formatted_value(converted_value, setting_name)}!', color=7528669)

    def run_list_config_change_command(self, ctx, setting_name, converted_value, is_add: True):
        current_list: list = fetch_setting(ctx.guild.id, setting_name)
        if is_add:
            if converted_value in current_list:
                return discord.Embed(description=f'{self.get_formatted_value(converted_value, setting_name)} is already in {SETTINGS_NAMES[setting_name]}!', color=16741747)
            current_list.append(converted_value)
            set_setting(ctx.guild.id, setting_name, current_list)
            return discord.Embed(description=f'Added {self.get_formatted_value(converted_value, setting_name)} to {SETTINGS_NAMES[setting_name]}!', color=7528669)
        else:
            if converted_value not in current_list:
                return discord.Embed(description=f'{self.get_formatted_value(converted_value, setting_name)} is not in the list!', color=16741747)
            current_list: list = fetch_setting(ctx.guild.id, setting_name)
            current_list.remove(converted_value)
            set_setting(ctx.guild.id, setting_name, current_list)
            return discord.Embed(description=f'Removed {self.get_formatted_value(converted_value, setting_name)} from {SETTINGS_NAMES[setting_name]}!', color=7528669)
    #endregion
        
    def get_internal_setting_name(self, input_name: str):
        #Assumes internal names are lower case!             -------------------------------------------\/  #FIXME lmao lowercase
        if input_name.lower() in [name.lower() for name in SETTINGS_NAMES.keys()]: return input_name.lower()
        if input_name.lower() in [name.lower() for name in SETTINGS_NAMES.values()]:
            index = [name.lower() for name in SETTINGS_NAMES.values()].index(input_name)
            return list(SETTINGS_NAMES.keys())[index]
        for alias_list in SETTINGS_ALIASES.values():
            if input_name.lower() in alias_list:  #FIXME maybe this too
                index = list(SETTINGS_ALIASES.values()).index(alias_list)
                return list(SETTINGS_ALIASES.keys())[index]
        raise ValueError(input_name)  #If all other searches fail then setting name can't be found and is invalid

    def convert_user_input(self, value, setting_type, list_type=None):
        '''
        Converts the user input value to the given setting_type and returns it.
        If setting_type is `list` then list_type must also be included

        Parameters:
            - `value`: Any; The value to convert
            - `setting_type`: type; The type to convert to
            - `list_type`: type; The type to convert to if the main type is list

        Returns:
            `Any`; The formatted value
        '''
        if setting_type == str:
            return str(value)
        elif setting_type == bool:
            if value.lower == 'on': return True
            if value.lower == 'off': return False
            return bool(value)
        elif setting_type == int:
            return int(value)
        elif setting_type == float:
            return float(value)
        elif setting_type == list:
            if list_type == None: raise TypeError(list_type)
            return self.convert_user_input(value, list_type)
        else:
            return value



def validate_settings_dicts():
    for name in list(DEFAULT_SETTINGS.keys()):
        if name not in SETTINGS_NAMES or name not in SETTINGS_TYPES or name not in SETTINGS_DESCRIPTIONS:
            del(DEFAULT_SETTINGS[name])
            logger.warn(f'Setting {name=} not in all required dicts, removing...')


#region Database handling
def process_setting_value(raw_setting, setting_type, list_type=None):
    '''
        Returns the raw setting value formatted correctly using SETTINGS_TYPES. Unknown types are returned as the raw value.
        If `raw_setting` is None then None is returned.
        When returning lists, values that cannot be formatted correctly are not returned

        Parameters:
            - `raw_setting`: Any; The value to format
            - `setting_type`: type; The type to format as

        Returns:
            `Any`; The formatted input
    '''
    if raw_setting is None:
        return None
    if setting_type == str:
        return str(raw_setting)
    elif setting_type == bool:
        return bool(raw_setting)
    elif setting_type == int:
        return int(raw_setting)
    elif setting_type == float:
        return float(raw_setting)
    elif setting_type == list:
        if list_type == None: raise TypeError(list_type)
        base_list = []
        for setting in str(raw_setting).split('%list_separator;%'):
            if list_type == bool:
                try:
                    if setting == 'True':  #Assumes that original list was serialized using set_setting, thus the format for bools will match this pattern
                        base_list.append(True)
                    elif setting == 'False':
                        base_list.append(False)
                except:
                    continue
            else:
                try:
                    base_list.append(list_type(setting))
                except:
                    continue
        return base_list
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
    if raw_setting == 'NULL' or raw_setting is None:
        return DEFAULT_SETTINGS[setting]
    else:
        setting_type = SETTINGS_TYPES[setting] if setting in SETTINGS_TYPES else int
        list_type = LIST_TYPES[setting] if setting in LIST_TYPES else None
        return process_setting_value(raw_setting, setting_type, list_type)

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
                logger.info(f'Fetched all settings for {guild_id=}')
                return row
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f'Failed to fetch all settings from database row {guild_id=}', exc_info=e)
        raise e

def set_setting(guild_id, setting, value):
    '''
        Changes the setting requested by name for the given guild id to the given value

        Parameters:
            - `guild_id`: int; The guild id to set the setting for
            - `setting`: str; The setting name
            - `value`: Any; The setting value
    '''
    if value is None: value = 'NULL'
    elif type(value) != SETTINGS_TYPES[setting]: raise TypeError(value)

    if not is_guild_known(guild_id):
        initialize_guild(guild_id)
    try:
        if isinstance(value, list):  #TODO split into separate function
            base_str = ''
            for item in value:
                base_str += str(item)
                base_str += '%list_separator;%'
            value = base_str
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE settings SET {setting} = (?) WHERE guild_id = {guild_id}", [value])
            logger.info(f'Changed setting {setting} to {value} for {guild_id=}')
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
        logger.error(f'Failed to delete settings database row {guild_id=}', exc_info=e)
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
        logger.error(f'Failed to initalize settings database row {guild_id=}', exc_info=e)
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
        logger.error(f'Failed to check if {guild_id=} is known', exc_info=e)
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

    DBManager.ensure_table_exists('settings')
    DBManager.update_columns('settings')
    #set_setting(866160840037236736, 'cafe_mode', False)
    print(fetch_table('settings'))
    print(fetch_setting(866160840037236736, 'prefix'))
    print(list_columns('settings'))

    