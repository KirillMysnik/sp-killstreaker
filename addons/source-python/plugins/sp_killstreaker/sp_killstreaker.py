from json import load as json_load

from commands.server import ServerCommand
from engines.server import engine_server
from events import Event
from paths import CFG_PATH

from .info import info

from .classes.ks_database import ks_database
from .classes.user import update_from_cvars
from .classes.user import user_manager

from .resource.config_cvars import cvar_killstreak_scheme


KS_DIR = CFG_PATH / info.basename / "killstreaks"


def reload_scheme(filename):
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = KS_DIR / filename
    if not filepath.isfile():
        raise FileNotFoundError("Cannot find {}".format(filename))

    with open(filepath) as f:
        ks_database.load_from_json(json_load(f))


def load():
    update_from_cvars()


@Event('player_hurt')
def on_player_hurt(game_event):
    userid = game_event.get_int('userid')
    attackerid = game_event.get_int('attacker')
    if attackerid == 0 or attackerid == userid:
        return

    user_manager[userid].count_damage(game_event.get_int('dmg_health'))


@Event('player_death')
def on_player_death(game_event):
    userid = game_event.get_int('userid')
    attackerid = game_event.get_int('attacker')

    user_manager[userid].count_death()
    if attackerid != 0 and attackerid != userid:
        user_manager[attackerid].count_kill()


@Event('round_start')
def on_round_start(game_event):
    update_from_cvars()


@Event('server_cvar')
def on_server_cvar(game_event):
    cvarname = game_event.get_string('cvarname').lower()

    if cvarname == "spk_killstreak_scheme":
        filename = cvar_killstreak_scheme.get_string().lower()
        try:
            reload_scheme(filename)
            engine_server.echo("Successfully loaded '{}'".format(filename))
        except FileNotFoundError:
            engine_server.echo_console(
                "Error: '{}' killstreak scheme was not found".format(filename))

        return

    if cvarname in (
        'spk_hitsound',
        'spk_hitmarker',
        'spk_hitmarker_visible_timeout',
        'spk_damage_visible_timeout',
        'spk_killstreak_visible_timeout',
        'spk_queue_timeout',
    ):

        engine_server.echo_console("Updating local variables...")
        update_from_cvars()
        engine_server.echo_console("Successful.")
        return
