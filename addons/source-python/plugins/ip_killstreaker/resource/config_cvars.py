from config.manager import ConfigManager
from cvars.flags import ConVarFlags

from ..info import info

from .strings import strings_config


with ConfigManager(info.basename, cvar_prefix='ipk_') as config_manager:
    config_manager.section(strings_config['section_hitsound'])
    cvar_hitsound = config_manager.cvar(
        name="hitsound",
        default="arcjail/hitsound.wav",
        description=strings_config['hitsound'],
        flags=ConVarFlags.NOTIFY,
    )
    config_manager.section(strings_config['section_hitmarker'])
    cvar_hitmarker = config_manager.cvar(
        name="hitmarker",
        default="overlays/ip_killstreaker/hitmarker",
        description=strings_config['hitmarker'],
        flags=ConVarFlags.NOTIFY,
    )
    cvar_hitmarker_visible_timeout = config_manager.cvar(
        name="hitmarker_visible_timeout",
        default=0.2,
        description=strings_config['hitmarker_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
    )
    config_manager.section(strings_config['section_showdamage'])
    cvar_showdamage_enabled = config_manager.cvar(
        name="showdamage_enabled",
        default=1,
        description=strings_config['showdamage_enabled'],
        flags=ConVarFlags.NOTIFY,
        min_value=0.0,
    )
    cvar_damage_visible_timeout = config_manager.cvar(
        name="damage_visible_timeout",
        default=2.0,
        description=strings_config['damage_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0.0,
        max_value=10.0,
    )
    config_manager.section(strings_config['section_killstreaks'])
    cvar_killstreak_enabled = config_manager.cvar(
        name="killstreak_enabled",
        default=1,
        description=strings_config['killstreak_enabled'],
        flags=ConVarFlags.NOTIFY,
        min_value=0.0,
    )
    cvar_killstreak_reset_every_round = config_manager.cvar(
        name="killstreak_reset_every_round",
        default=1,
        description=strings_config['killstreak_reset_every_round'],
        min_value=0.0,
    )
    cvar_killstreak_scheme = config_manager.cvar(
        name="killstreak_scheme",
        default="default",
        description=strings_config['killstreak_scheme'],
        flags=ConVarFlags.NOTIFY,
    )
    cvar_killstreak_visible_timeout = config_manager.cvar(
        name="killstreak_visible_timeout",
        default=2,
        description=strings_config['killstreak_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0,
    )
    config_manager.section(strings_config['section_advanced'])
    cvar_queue_timeout = config_manager.cvar(
        name="queue_timeout",
        default=0.15,
        description=strings_config['queue_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0,
    )
