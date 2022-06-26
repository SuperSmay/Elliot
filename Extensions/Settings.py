import logging
import sqlite3
from fnmatch import fnmatch

import discord
from discord.commands import Option, OptionChoice, SlashCommand, SlashCommandGroup
from discord.ext import commands

import Globals.DBManager as DBManager
from Extensions.Statistics import log_event

ADD_ALIASES = ['add', 'a', 'append']
REMOVE_ALIASES = ['remove', 'r', 'rm', 'delete', 'yeet']
TRUE_ALIASES = ['on', 'enable', 'true']
FALSE_ALIASES = ['off', 'disable', 'false']
RESET_ALIASES = ['reset', 'none', 'default']

DEFAULT_SETTINGS = {  #Required settings dict, provides a default value and serves as the master list of settings
    'cafe_mode': False,
    'verification_system': False,
    'prefix': 'eli',
    'welcome_channel' : None,
    'role_channel' : None,
    'age_role_list' : [],
    'pronoun_role_list': [],
    'settings_roles' : [],
    'unverified_role' : None,
    'verified_role' : None,
    'too_old_role' : None,
    'too_young_role' : None,
    'log_channel' : None,
    'bump_channel' : None,
    'bump_role' : None,
    'bot_role' : None,
    'announce_songs': False,
    'shuffle': False,
    'game_mode': False,
    'auto_skip': False,

}

SETTINGS_NAMES = {  #Required settings dict, provides a user-facing setting name
    'cafe_mode': 'Café Mode',
    'verification_system': 'Verification',
    'prefix': 'Prefix',
    'welcome_channel' : 'Welcome Channel',
    'role_channel' : 'Role Channel',
    'age_role_list' : 'Age Roles',
    'pronoun_role_list': 'Pronoun Roles',
    'settings_roles' : 'Settings Roles',
    'unverified_role' : 'Unverified Role',
    'verified_role' : 'Verified Role',
    'too_young_role' : 'Too Young Role',
    'too_old_role' : 'Too Old Role',
    'log_channel' : 'Log Channel',
    'bump_channel' : 'Bump Reminder Channel',
    'bump_role' : 'Bump Reminder Role',
    'bot_role' : 'Server Bot Role',
    'announce_songs': 'Announce Now Playing Song',
    'shuffle': 'Shuffle',
    'game_mode': 'Music Player Game Mode',
    'auto_skip': 'Music Player Autoskip',
}

SETTINGS_ALIASES = {  #Optional settings dict for other usable names
    'cafe_mode' : ['cafemode', 'cafe', 'cafémode', 'café', 'café_mode'],
    'verification_system': ['verificationsystem', 'verification', 'verify'],
    'welcome_channel' : ['welcomechannel', 'welcome'],
    'role_channel' : ['rolechannel'],
    'age_role_list' : ['ageroles', 'agerole', 'agelist', 'validageroles', 'age_roles', 'age_list', 'valid_age_roles'],
    'pronoun_role_list': ['pronounrolelist', 'pronounroles', 'pronounrole', 'pronoun_roles', 'pronoun_role', 'validpronounroles', 'valid_pronoun_roles',],
    'settings_roles' : ['settingsroles'],
    'unverified_role' : ['unverifiedrole', 'unverified'],
    'verified_role' : ['verifiedrole', 'verified'],
    'too_young_role' : ['tooyoungrole', 'tooyoung', 'youngrole', 'too_young', 'young_role'],
    'too_old_role' : ['toooldrole', 'tooold', 'oldrole', 'too_old', 'old_role'],
    'log_channel' : ['logchannel', 'log'],
    'bump_channel' : ['bumpchannel'],
    'bump_role' : ['bumprole'],
    'bot_role' : ['botrole'],
    'announce_songs': ['announcesongs'],
    'game_mode': ['gamemode'],
    'auto_skip': ['autoskip'],
}

SETTINGS_DESCRIPTIONS = {  #Required settings dict, provides a description of the setting
    'cafe_mode': 'Changes some wordings to be café themed',
    'verification_system': 'Enable/disable the verification system based on pronoun roles and age roles. Requires age roles, pronoun roles, verified and unverified roles to be filled out',
    'prefix': 'The prefix for prefix commands',
    'welcome_channel' : 'The channel to send welcome/goodbye messages in',
    'role_channel' : 'The channel that users can be reffered to to get roles',
    'age_role_list' : 'List of valid age roles for verification',
    'pronoun_role_list': 'List of valid pronoun roles for verification',
    'settings_roles' : 'Roles that are allowed to change settings',
    'unverified_role' : 'Role that new users get when joining the server',
    'verified_role' : 'Role for verified users to get',
    'too_young_role' : 'Role that will auto kick people for being too young',
    'too_old_role' : 'Role that will auto kick people for being too old',
    'log_channel' : 'Channel to send log messages to',
    'bump_channel' : 'Channel to send bump reminders in',
    'bump_role' : 'Role to ping for bump reminders',
    'bot_role' : 'Role that you give bot users to excluse them from the member count',
    'announce_songs': 'Announce what song is playing when a new song starts',
    'shuffle': 'Shuffle the upcoming playlist (Queue is unaffected!)',
    'game_mode': 'Turns on the guessing game for the music player',
    'auto_skip': 'Skip songs after they have been guessed in game mode',
}

SETTINGS_TYPES = {  #Required settings dict, provides the expected type of the setting value
    'cafe_mode': bool,
    'verification_system': bool,
    'prefix': str,
    'welcome_channel' : int,
    'role_channel' : int,
    'age_role_list' : list,
    'pronoun_role_list': list,
    'settings_roles' : list,
    'unverified_role' : int,
    'verified_role' : int,
    'too_young_role' : int,
    'too_old_role' : int,
    'log_channel' : int,
    'bump_channel' : int,
    'bump_role' : int,
    'bot_role' : int,
    'announce_songs': bool,
    'shuffle': bool,
    'game_mode': bool,
    'auto_skip': bool,
}

LIST_TYPES = {  #Required if SETTINGS_TYPE is list
    'age_role_list' : int,
    'pronoun_role_list': int,
    'settings_roles' : int
}

ROLE_ID_SETTINGS = [  # Must be int type
    'age_role_list', 
    'pronoun_role_list',
    'settings_roles',
    'unverified_role',
    'verified_role',
    'too_young_role',
    'too_old_role',
    'bump_role',
    'bot_role',
]

CHANNEL_ID_SETTINGS = [  # Must be int type
    'welcome_channel',
    'role_channel',
    'log_channel',
    'bump_channel',
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Caches
global_prefix_dict = {}  
global_verification_system_dict = {}
global_unverified_role_dict = {}

def setup(bot):
    bot.add_cog(Settings())

class Settings(commands.Cog):
    def __init__(self):
        
        validate_settings_dicts()  # Validate dicts of settings on startup

        name_type_dict = {name: SETTINGS_TYPES[name] for name in DEFAULT_SETTINGS}  # This is because the default settings dict is the master list and should be the only reference for which settings currently exist
        
        DBManager.ensure_table_exists('settings', 'guild_id', int)  
        DBManager.update_columns('settings', DBManager.global_database_path, name_type_dict)

    config_list_complete = [OptionChoice(name=SETTINGS_NAMES[setting], value=setting) for setting in DEFAULT_SETTINGS]
    config_list_complete.append(OptionChoice(name='List All', value='list'))

    @commands.slash_command(name='config', description='Show/change the current config')
    async def config_command(self, ctx, setting_name:Option(str, required=True, choices=config_list_complete, description='The option to change'), mode: Option(str, required=False, default='', choices=[OptionChoice(name='Add', value='add'), OptionChoice(name='Remove', value='remove')], description='Add or remove items from list settings'), value: Option(str, required=False, description='New setting value')):
        log_event('slash_command', ctx=ctx)
        log_event('config_command', ctx=ctx)
        if setting_name == 'list':
            try: page = int(value) - 1
            except ValueError: page = 0
            await ctx.reply(embed=self.get_all_config_list_embed(page), mention_author=False)
        
        if value == '':
            await ctx.respond(embed=self.get_config_info_embed(ctx.guild.id, setting_name))
        elif not self.settings_permission_allowed(ctx.author):
            await ctx.respond(embed=discord.Embed(description=f'You don\'t have permission for that!', color=16741747))
        else:
            if SETTINGS_TYPES[setting_name] == list:
                converted_raw_input = mode
            else:
                converted_raw_input = value
            converted_raw_input_two = value

            await ctx.respond(embed=self.run_config_change_command(ctx, setting_name, converted_raw_input, converted_raw_input_two))

    @commands.command(name='config', description='Shows the current config')  #FIXME Parse value with quotes and stuff
    async def config_prefix_command(self, ctx, input_name='list', value='', value_two=''):
        log_event('prefix_command', ctx=ctx)
        log_event('config_command', ctx=ctx)
        try: 
            int(input_name)
            value = input_name
            input_name = 'list'
        except ValueError: page = 0  #If the input cannot be converted to an int, then its not a number and the page should be default (duh)

        if input_name == 'list':
            try: page = int(value) - 1
            except ValueError: page = 0
            await ctx.reply(embed=self.get_all_config_list_embed(page), mention_author=False)
        else:
            try:
                setting_name = self.get_internal_setting_name(input_name)  #raises ValueError if input is invalid, so we can assume that setting_name is valid
                if value == '':
                    await ctx.reply(embed=self.get_config_info_embed(ctx.guild.id, setting_name), mention_author=False)
                elif not self.settings_permission_allowed(ctx.author):
                    await ctx.reply(embed=discord.Embed(description=f'You don\'t have permission for that!', color=16741747), mention_author=False)
                else:
                    await ctx.reply(embed=self.run_config_change_command(ctx, setting_name, value, value_two), mention_author=False)
            except ValueError:
                await ctx.reply(embed=discord.Embed(description=f'Setting name `{input_name}` not found!', color=16741747), mention_author=False)

    def settings_permission_allowed(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        member_role_ids = [role.id for role in member.roles]
        for role_id in fetch_setting(member.guild.id, 'settings_roles'):
            if role_id in member_role_ids:
                return True
        return False
    
    def get_all_config_list_embed(self, page: int) -> discord.Embed:
        max_page = max((len(DEFAULT_SETTINGS) - 1)//10, 0)
        page = min(max_page, max(page, 0))
        embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ Settings ☾∘∙⊱⋅•⋅', description='Bot configuration options', color=7528669)
        sorted_keys = list(DEFAULT_SETTINGS.keys())
        sorted_keys.sort()
        for setting_name in sorted_keys[10*page: 10*(page + 1)]:
            embed.add_field(name=f'{SETTINGS_NAMES[setting_name]}', value=SETTINGS_DESCRIPTIONS[setting_name])
        embed.set_footer(text=f'Page {min(page+1, max_page + 1)} of {max_page + 1}')
        value = 1 if True else value
        return embed

    def get_config_info_embed(self, guild_id, setting_name):  #Assumes valid setting name
        if SETTINGS_TYPES[setting_name] == list:  #Use a different format for showing list configs
            setting_value = fetch_setting(guild_id, setting_name)
            embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ {SETTINGS_NAMES[setting_name]} ☾∘∙⊱⋅•⋅', description=f'{SETTINGS_DESCRIPTIONS[setting_name]}', color=7528669)
            embed.add_field(name=f'Current list:', value=self.get_display_formatted_value(setting_value, setting_name))
            embed.set_footer(text=f'Change this with /config <{setting_name}> add/remove <value>')
            return embed
        else:
            setting_value = fetch_setting(guild_id, setting_name)
            embed=discord.Embed(title=f'⋅•⋅⊰∙∘☽ {SETTINGS_NAMES[setting_name]} ☾∘∙⊱⋅•⋅', description=f'{SETTINGS_DESCRIPTIONS[setting_name]}', color=7528669)
            embed.add_field(name=f'Currently set to:', value=self.get_display_formatted_value(setting_value, setting_name))
            embed.set_footer(text=f'Change this with /config <{setting_name}> <value>')
            return embed
        
    #region AAAAAAAA

    def get_display_formatted_value(self, converted_setting_value, setting_name=None) -> str:  #Returns nicely formatted string
        #Setting name is used for determining if the value should be formatted as a channel/role mention
        if converted_setting_value is None:
            return 'None'
        if isinstance(converted_setting_value, list):
            if len(converted_setting_value) > 0:
                return ', '.join([self.get_display_formatted_value(value_from_list, setting_name) for value_from_list in converted_setting_value])
            else:
                return 'Empty'
        elif setting_name is not None and setting_name in ROLE_ID_SETTINGS and (isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str)):
            return f'<@&{converted_setting_value}>'
        elif setting_name is not None and setting_name in CHANNEL_ID_SETTINGS and (isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str)):
            return f'<#{converted_setting_value}>'
        elif isinstance(converted_setting_value, bool):
            if converted_setting_value: return 'On'
            else: return 'Off'
        elif isinstance(converted_setting_value, int) or isinstance(converted_setting_value, str) or isinstance(converted_setting_value, float):
            return str(converted_setting_value)
        else:
            return str(converted_setting_value)

    def get_channel_id_for_input(self, value, guild: discord.Guild):  #Returns channel id for given value. Attempts to convert channel names given into ids. Value error is raised when id can't be found or is invalid for guild
        if isinstance(value, str) and fnmatch(value, "<#*>"):
            value = value.replace('<#', '').replace('>','')
        elif isinstance(value, str):
            for channel in guild.channels:
                if value.replace('#','').replace('-','').replace(' ','') == channel.name.replace('-','').replace(' ',''):
                    value = channel.id
                    break
        try:
            int_value = int(value)
            if int_value not in [channel.id for channel in guild.channels]:
                raise ValueError(int_value)
            return int_value
        except ValueError as e:
            raise e

    def get_role_id_for_input(self, value, guild: discord.Guild):  #Returns role id for given value. Value error is raised when id can't be found or is invalid for guild
        if isinstance(value, str) and fnmatch(value, "<@&*>"):
            value = value.replace('<@&', '').replace('>','')
        try:
            int_value = int(value)
            if int_value not in [role.id for role in guild.roles]:
                raise ValueError(int_value)
            return int_value
        except ValueError as e:
            raise e

    def convert_user_input_to_type(self, value, setting_type):
        if setting_type == str:
            return str(value)
        elif setting_type == bool:
            if value.lower() in TRUE_ALIASES: return True
            if value.lower() in FALSE_ALIASES: return False
            raise ValueError(value)
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
                return discord.Embed(description=f'Specify add or remove, not `{raw_input}`!', color=16741747)
            setting_type = LIST_TYPES[setting_name] if setting_name in LIST_TYPES else int  #Default to int if no type is provided
            input_value: str = raw_input_two[:1000]

        else:
            setting_type = SETTINGS_TYPES[setting_name]
            input_value: str = raw_input[:1000]
        
        #Converter section

        try:
            if input_value.lower() in RESET_ALIASES and not SETTINGS_TYPES[setting_name] == list:
                converted_value = None
            elif setting_name in ROLE_ID_SETTINGS:
                converted_value = self.get_role_id_for_input(input_value, ctx.guild)
            elif setting_name in CHANNEL_ID_SETTINGS:
                converted_value = self.get_channel_id_for_input(input_value, ctx.guild)
            else:
                converted_value = self.convert_user_input_to_type(input_value, setting_type)
        except ValueError:
            return discord.Embed(description=f'Invalid input value `{input_value}`!', color=16741747)

        if setting_name == 'prefix' and converted_value is not None and len(converted_value) > 5:
            return discord.Embed(description=f'Prefix `{input_value}` is too long!', color=16741747)

        #Actually do the thing

        if SETTINGS_TYPES[setting_name] == list:
            return self.list_config_change(ctx, setting_name, converted_value, is_add)
        else:
            return self.simple_config_change(ctx, setting_name, converted_value)
            
            

    def simple_config_change(self, ctx, setting_name, converted_value):
        set_value = set_setting(ctx.guild.id, setting_name, converted_value)
        return discord.Embed(description=f'Changed {SETTINGS_NAMES[setting_name]} to {self.get_display_formatted_value(set_value, setting_name)}!', color=7528669)

    def list_config_change(self, ctx, setting_name, converted_value, is_add: True):
        current_list: list = fetch_setting(ctx.guild.id, setting_name)
        if is_add:
            if converted_value in current_list:
                return discord.Embed(description=f'{self.get_display_formatted_value(converted_value, setting_name)} is already in {SETTINGS_NAMES[setting_name]}!', color=16741747)
            current_list.append(converted_value)
            set_value = set_setting(ctx.guild.id, setting_name, current_list)
            return discord.Embed(description=f'Added {self.get_display_formatted_value(converted_value, setting_name)} to {SETTINGS_NAMES[setting_name]}!', color=7528669)
        else:
            if converted_value not in current_list:
                return discord.Embed(description=f'{self.get_display_formatted_value(converted_value, setting_name)} is not in the list!', color=16741747)
            current_list: list = fetch_setting(ctx.guild.id, setting_name)
            current_list.remove(converted_value)
            set_value = set_setting(ctx.guild.id, setting_name, current_list)
            return discord.Embed(description=f'Removed {self.get_display_formatted_value(converted_value, setting_name)} from {SETTINGS_NAMES[setting_name]}!', color=7528669)
    #endregion
        
    def get_internal_setting_name(self, input_name: str):
        #Assumes internal names are lower case!
        if input_name.lower() in [name.lower() for name in SETTINGS_NAMES.keys()]:
            index = [name.lower() for name in SETTINGS_NAMES.keys()].index(input_name.lower())
            return list(SETTINGS_NAMES.keys())[index]
        if input_name.lower() in [name.lower() for name in SETTINGS_NAMES.values()]:
            index = [name.lower() for name in SETTINGS_NAMES.values()].index(input_name.lower())
            return list(SETTINGS_NAMES.keys())[index]
        for alias_list in SETTINGS_ALIASES.values():
            if input_name.lower() in [alias.lower() for alias in alias_list]:
                index = list(SETTINGS_ALIASES.values()).index(alias_list)
                return list(SETTINGS_ALIASES.keys())[index]
        raise ValueError(input_name)  #If all searches fail then setting name can't be found and is invalid

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
            continue
        if SETTINGS_TYPES[name] == list and name not in LIST_TYPES:
            del(DEFAULT_SETTINGS[name])
            logger.warn(f'Setting {name=} is a list, but does not have a list type, removing...')
            continue
        if (name in ROLE_ID_SETTINGS or name in CHANNEL_ID_SETTINGS):
            if SETTINGS_TYPES[name] != int and SETTINGS_TYPES[name] == list and LIST_TYPES[name] != int:
                del(DEFAULT_SETTINGS[name])
                logger.warn(f'Setting {name=} is role/channel id but not of type int, removing...')
                continue
          


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
        for setting in str(raw_setting).split('%list_separator;%')[:-1]:  #Ignore last item, it should be blank because the string will end with the separator
            if list_type == bool:
                if setting == 'True':  #Assumes that original list was serialized using set_setting, thus the format for bools will match this pattern
                    base_list.append(True)
                elif setting == 'False':
                    base_list.append(False)
            else:
                try:
                    base_list.append(process_setting_value(setting, list_type))
                except ValueError as e:
                    logger.warn(f'Processing setting list value {setting=} with type {list_type=} failed')
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
    #Special case to avoid spamming the database
    if setting == 'prefix':
        if guild_id in global_prefix_dict:
            return global_prefix_dict[guild_id]  #Should only ever be set to a string so it should be fine
    if setting == 'verification_system':
        if guild_id in global_verification_system_dict:
            return global_verification_system_dict[guild_id]  #Should only ever be set to an int so it should be fine
    if setting == 'unverified_role':
        if guild_id in global_unverified_role_dict:
            return global_unverified_role_dict[guild_id]  #Should only ever be set to an int so it should be fine
    #If not cached then continue on as normal

    logger.info(f'Fetching {setting=} for {guild_id=}')

    if setting not in DEFAULT_SETTINGS: raise ValueError(setting)
    raw_setting = fetch_all_settings(guild_id)[setting]
    if raw_setting == 'NULL' or raw_setting is None:
        if setting == 'prefix':  #If this is true then the prefix is not cached as that would be caught earlier
            global_prefix_dict[guild_id] = DEFAULT_SETTINGS[setting]  #Reset cache
        if setting == 'verification_system':  #If this is true then the prefix is not cached as that would be caught earlier
            global_verification_system_dict[guild_id] = DEFAULT_SETTINGS[setting]
        if setting == 'unverified_role':  #If this is true then the prefix is not cached as that would be caught earlier
            global_unverified_role_dict[guild_id] = DEFAULT_SETTINGS[setting]
        return DEFAULT_SETTINGS[setting]
    else:
        setting_type = SETTINGS_TYPES[setting] if setting in SETTINGS_TYPES else int
        list_type = LIST_TYPES[setting] if setting in LIST_TYPES else None
        if setting == 'prefix':  #If this is true then the prefix is not cached as that would be caught earlier
            value = process_setting_value(raw_setting, setting_type, list_type)
            global_prefix_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
        if setting == 'verification_system':  #If this is true then the prefix is not cached as that would be caught earlier
            value = process_setting_value(raw_setting, setting_type, list_type)
            global_verification_system_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
        if setting == 'unverified_role':  #If this is true then the prefix is not cached as that would be caught earlier
            value = process_setting_value(raw_setting, setting_type, list_type)
            global_unverified_role_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
        return process_setting_value(raw_setting, setting_type, list_type)

def fetch_all_settings(guild_id):
    '''
        Returns the setting row requested by guild id. Returns default values if guild is not in database

        Parameters:
            - `guild_id`: int; The guild id to get the settings for

        Returns:
            `sqlite3.Row`; The settings row
    '''
    log_event('config_fetch', modes=['global', 'guild'], id=guild_id)
    try:
        if DBManager.is_row_known('settings', DBManager.global_database_path, 'guild_id', guild_id):
            with sqlite3.connect(DBManager.global_database_path) as con:
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                row = cur.execute(f"SELECT * FROM settings WHERE guild_id = {guild_id}").fetchone()
                #logger.info(f'Fetched all settings for {guild_id=}')
                return row
        else:
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f'Failed to fetch all settings from database row {guild_id=}', exc_info=e)
        raise e

def serialize_list(list):
    base_str = ''
    for item in list:
        base_str += str(item)
        base_str += '%list_separator;%'
    return base_str

def set_setting(guild_id, setting, value):
    '''
        Changes the setting requested by name for the given guild id to the given value

        Parameters:
            - `guild_id`: int; The guild id to set the setting for
            - `setting`: str; The setting name
            - `value`: Any; The setting value

        Returns;
            `str`; The new setting value
    '''
    log_event('config_chnage', modes=['global', 'guild'], id=guild_id)
    if value is not None and type(value) != SETTINGS_TYPES[setting]: raise TypeError(value)

    if setting == 'prefix' and value is not None:  # Special case for the prefix
        value = value [:5]
        value.replace(' ', '')
        value = value.lower()

    if not DBManager.is_row_known('settings', DBManager.global_database_path, 'guild_id', guild_id):
        DBManager.initialize_row('settings', DBManager.global_database_path, 'guild_id', guild_id)
    try:
        if isinstance(value, list):
            value = serialize_list(value)
        with sqlite3.connect(DBManager.global_database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE settings SET {setting} = (?) WHERE guild_id = {guild_id}", [value])
            logger.info(f'Changed setting {setting} to {value} for {guild_id=}')
    except Exception as e:
        logger.error(f'Changing setting {setting} to {value} failed', exc_info=e)
        raise e

    if setting == 'prefix':  #If this is true then update the cache
        if value is None and guild_id in global_prefix_dict:
            del(global_prefix_dict[guild_id])
            logger.info(f'Removed cached setting {setting} for {guild_id=}')
        else:
            global_prefix_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
    if setting == 'verification_system':  #If this is true then update the cache
        if value is None and guild_id in global_verification_system_dict:
            del(global_verification_system_dict[guild_id])
            logger.info(f'Removed cached setting {setting} for {guild_id=}')
        else:
            global_verification_system_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
    if setting == 'unverified_role':  #If this is true then update the cache
        if value is None and guild_id in global_unverified_role_dict:
            del(global_unverified_role_dict[guild_id])
            logger.info(f'Removed cached setting {setting} for {guild_id=}')
        else:
            global_unverified_role_dict[guild_id] = value
            logger.info(f'Changed cached setting {setting} to {value} for {guild_id=}')
    return value

def set_default_settings(guild_id):
    '''
        Removes the given guild id from the database

        Parameters:
            - `guild_id`: int; The guild id to remove
    '''
    try:
        if DBManager.is_row_known('settings', DBManager.global_database_path, 'guild_id', guild_id):
            with sqlite3.connect(DBManager.global_database_path) as con:
                cur = con.cursor()
                cur.execute(f"DELETE FROM settings WHERE guild_id = {guild_id}")
                logger.info(f'Deleting server row {guild_id} to reset to default')
    except Exception as e:
        logger.error(f'Failed to delete settings database row {guild_id=}', exc_info=e)
        raise e

    if guild_id in global_prefix_dict:  #If this is true then remove that cached value
        del(global_prefix_dict[guild_id])
        logger.info(f'Removed cached setting prefix for {guild_id=}')
    if guild_id in global_verification_system_dict:  #If this is true then remove that cached value
        del(global_verification_system_dict[guild_id])
        logger.info(f'Removed cached setting verifcation_system for {guild_id=}')
    if guild_id in global_unverified_role_dict:  #If this is true then remove that cached value
        del(global_unverified_role_dict[guild_id])
        logger.info(f'Removed cached setting unverified_role for {guild_id=}')
#endregion

if __name__ == '__main__':

    def fetch_table(table_name):
        with sqlite3.connect(DBManager.global_database_path) as con:
            cur = con.cursor()
            table = cur.execute(f"SELECT * from {table_name}").fetchall()
            return table

    def delete_table(table_name):
        with sqlite3.connect(DBManager.global_database_path) as con:
            cur = con.cursor()
            cur.execute(f"DROP TABLE {table_name}")

    def list_columns(table_name):
        with sqlite3.connect(DBManager.global_database_path) as con:
            cur = con.cursor()
            columns = cur.execute(f'PRAGMA table_info({table_name})').fetchall()
            return columns

    