# =============================================================================
# >> IMPORTS
# =============================================================================
# Python
import json

# Source.Python
from core import GAME_NAME
from engines.sound import Sound, StreamSound
from stringtables.downloads import Downloadables
from translations.strings import LangStrings

# Killstreaker
from .info import info
from .paths import DOWNLOADLISTS_DIR_PATH, KS_DIR_PATH


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def reload_scheme(filename):
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = KS_DIR_PATH / filename
    if not filepath.isfile():
        raise FileNotFoundError("Cannot find {}".format(filename))

    with open(filepath) as f:
        ks_database.from_dict(json.load(f))


# =============================================================================
# >> CLASSES
# =============================================================================
if GAME_NAME in ('csgo',):
    sound_class = StreamSound
else:
    sound_class = Sound


class KillstreakTarget:
    NONE = 0
    ATTACKER = 1
    VICTIM = 2
    TEAMMATES = 4
    ENEMIES = 8


class Killstreak:
    def __init__(self, id_, dict_):
        self.id = id_
        self.priority = dict_.get('priority', 0)

        self.text = None
        if 'text' in dict_:
            self.text = ks_database.strings[dict_['text']]

        self.text_on_killstreak = None
        if 'text_on_killstreak' in dict_:
            self.text_on_killstreak = ks_database.strings[
                dict_['text_on_killstreak']]

        self.targets = dict_.get('recipients', KillstreakTarget.NONE)

        self.show_kills = dict_.get('show_kills', False)

        self.sound = None
        if 'sound' in dict_:
            self.sound = sound_class(dict_['sound'])


class KillstreakDatabase(dict):
    def __init__(self):
        super().__init__()

        self._downloadables = Downloadables()
        self.strings = None
        self.text = ""

    def from_dict(self, dict_):
        self.clear()
        self._downloadables.clear()

        if 'downloadables' in dict_:
            path = DOWNLOADLISTS_DIR_PATH / dict_['downloadables']
            if path.isfile():
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        self._downloadables.add(line)

        self.strings = LangStrings(
            info.name + "/killstreaks/" + dict_['strings'])

        self.text = self.strings[dict_['text']]

        for ks_id, ks_dict in dict_['killstreaks'].items():
            self[ks_id] = Killstreak(ks_id, ks_dict)

ks_database = KillstreakDatabase()
