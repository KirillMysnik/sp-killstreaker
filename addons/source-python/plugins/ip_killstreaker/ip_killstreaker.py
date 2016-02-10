from json import load as json_load

from core import echo_console
from events import Event
from filters.players import PlayerIter
from listeners import OnClientActive
from listeners import OnClientDisconnect
from listeners import OnLevelInit
from paths import CFG_PATH
from players.entity import Player
from players.helpers import userid_from_index
from stringtables.downloads import Downloadables

from .info import info

from .classes.ks_database import ks_database
from .classes.user import update_from_cvars
from .classes.user import user_manager

from .namespaces import status

from .resource.config_cvars import cvar_killstreak_scheme
from .resource.config_cvars import cvar_killstreak_reset_every_round


DOWNLOADLIST = CFG_PATH / info.basename / "downloadlist.txt"
KS_DIR = CFG_PATH / info.basename / "killstreaks"


def load_downloadables(filepath):
    downloadables = Downloadables()

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables

downloadables_global = load_downloadables(DOWNLOADLIST)


def reload_scheme(filename):
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = KS_DIR / filename
    if not filepath.isfile():
        raise FileNotFoundError("Cannot find {}".format(filename))

    with open(str(filepath)) as f:
        ks_database.load_from_json(json_load(f))


def load():
    for player in PlayerIter():
        user_manager.create(player)

    update_from_cvars()

    filename = cvar_killstreak_scheme.get_string().lower()
    try:
        reload_scheme(filename)
    except FileNotFoundError:
        echo_console(
            "Error: '{}' killstreak scheme was not found".format(filename))


@Event('player_hurt')
def on_player_hurt(game_event):
    userid = game_event.get_int('userid')
    attackerid = game_event.get_int('attacker')
    if attackerid == 0 or attackerid == userid:
        return

    user_manager[attackerid].count_damage(game_event)


@Event('player_death')
def on_player_death(game_event):
    userid = game_event.get_int('userid')
    attackerid = game_event.get_int('attacker')

    user_manager[userid].count_death(game_event)
    if attackerid != 0 and attackerid != userid:
        user_manager[attackerid].count_kill(game_event)


@Event('round_start')
def on_round_start(game_event):
    status.firstblood_triggered = False

    if cvar_killstreak_reset_every_round.get_bool():
        for user in user_manager.values():
            user.reset_killstreaks()


@Event('server_cvar')
def on_server_cvar(game_event):
    cvarname = game_event.get_string('cvarname').lower()

    if cvarname == "ipk_killstreak_scheme":
        filename = cvar_killstreak_scheme.get_string().lower()
        try:
            reload_scheme(filename)
            echo_console("Successfully loaded '{}'".format(filename))
        except FileNotFoundError:
            echo_console(
                "Error: '{}' killstreak scheme was not found".format(filename))

        return

    if cvarname in (
        'ipk_hitsound',
        'ipk_hitmarker',
        'ipk_hitmarker_visible_timeout',
        'ipk_showdamage_enabled',
        'ipk_damage_visible_timeout',
        'ipk_killstreak_enabled',
        'ipk_killstreak_visible_timeout',
        'ipk_queue_timeout',
    ):

        echo_console("Updating local variables...")
        update_from_cvars()
        echo_console("Successful.")
        return


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    user_manager.create(player)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    user = user_manager.get(userid_from_index(index))
    if user is not None:
        user_manager.delete(user)


@OnLevelInit
def listener_on_level_init(map_name):
    user_manager.clear()