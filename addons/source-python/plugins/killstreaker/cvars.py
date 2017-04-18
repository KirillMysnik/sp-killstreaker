# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from core import echo_console

# Custom Package
from controlled_cvars import ControlledConfigManager, InvalidValue
from controlled_cvars.handlers import (
    bool_handler, float_handler, sound_nullable_handler, string_handler)

# Killstreaker
from .info import info
from .ks_database import reload_scheme
from .strings import config_strings


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def ks_scheme_handler(cvar):
    value = string_handler(cvar)
    try:
        reload_scheme(value)
    except FileNotFoundError:
        echo_console(
            "Error: '{}' killstreak scheme was not found".format(value))

        raise InvalidValue


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
with ControlledConfigManager(
        info.name + "/main", cvar_prefix='ks_') as config_manager:

    config_manager.section(config_strings['section hitsound'])
    config_manager.controlled_cvar(
        sound_nullable_handler,
        'hitsound',
        "killstreaker/hitsound.mp3",
        config_strings['desc hitsound']
    )

    config_manager.section(config_strings['section hitmarker'])
    config_manager.controlled_cvar(
        string_handler,
        'hitmarker',
        "overlays/killstreaker/hitmarker",
        config_strings['desc hitmarker']
    )
    config_manager.controlled_cvar(
        float_handler,
        'hitmarker_visible_for',
        0.2,
        config_strings['desc hitmarker_visible_for']
    )

    config_manager.section(config_strings['section showdamage'])
    config_manager.controlled_cvar(
        bool_handler,
        'showdamage',
        1,
        config_strings['desc showdamage']
    )
    config_manager.controlled_cvar(
        float_handler,
        'showdamage_visible_for',
        2.0,
        config_strings['desc showdamage_visible_for']
    )

    config_manager.section(config_strings['section killstreaks'])
    config_manager.controlled_cvar(
        bool_handler,
        'killstreaks',
        1,
        config_strings['desc killstreaks']
    )
    config_manager.controlled_cvar(
        bool_handler,
        'killstreaks_reset_every_round',
        1,
        config_strings['desc killstreaks_reset_every_round']
    )
    config_manager.controlled_cvar(
        ks_scheme_handler,
        'killstreaks_scheme',
        "default",
        config_strings['desc killstreaks_scheme']
    )
    config_manager.controlled_cvar(
        float_handler,
        'killstreaks_visible_for',
        2.0,
        config_strings['desc killstreaks_visible_for']
    )

    config_manager.section(config_strings['section advanced'])
    config_manager.controlled_cvar(
        float_handler,
        'queue_timeout',
        0.15,
        config_strings['desc queue_timeout']
    )
