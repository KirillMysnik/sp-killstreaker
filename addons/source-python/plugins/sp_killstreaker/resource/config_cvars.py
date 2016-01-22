from config.manager import ConfigManager
from cvars.flags import ConVarFlags

from ..info import info

from .strings import strings_config


with ConfigManager(info.basename, cvar_prefix='spk_') as config_manager:
    config_manager.section("Logging")
    cvar_logging_level = config_manager.cvar(
        name="logging_level",
        default=4,
        description=strings_config['logging_level'],
    )
    cvar_damage_visible_timeout = config_manager.cvar(
        name="damage_visible_timeout",
        default=2.0,
        description=strings_config['damage_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0.0,
        max_value=10.0,
    )
    cvar_hitmarker = config_manager.cvar(
        name="hitmarker",
        default="overlays/sp_killstreaker/hitmarker",
        description=strings_config['hitmarker'],
        flags=ConVarFlags.NOTIFY,
    )
    cvar_hitmarker_visible_timeout = config_manager.cvar(
        name="hitmarker_visible_timeout",
        default=0.2,
        description=strings_config['hitmarker_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
    )
    cvar_hitsound = config_manager.cvar(
        name="hitsound",
        default="arcjail/hitsound.wav",
        description=strings_config['hitsound'],
        flags=ConVarFlags.NOTIFY,
    )
    cvar_killstreak_visible_timeout = config_manager.cvar(
        name="killstreak_visible_timeout",
        default=2,
        description=strings_config['killstreak_visible_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0,
    )
    cvar_queue_timeout = config_manager.cvar(
        name="queue_timeout",
        default=0.15,
        description=strings_config['queue_timeout'],
        flags=ConVarFlags.NOTIFY,
        min_value=0,
    )
    cvar_killstreak_scheme = config_manager.cvar(
        name="killstreak_scheme",
        default="",
        description=strings_config['killstreak_scheme'],
        flags=ConVarFlags.NOTIFY,
    )