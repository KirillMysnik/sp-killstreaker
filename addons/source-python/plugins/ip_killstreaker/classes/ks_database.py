from engines.sound import Sound
from paths import CFG_PATH

from advanced_ts import BaseLangStrings

from ..info import info


DOWNLOADLISTS_DIR = CFG_PATH / info.basename


class KillstreakTarget:
    NONE = 0
    ATTACKER = 1
    VICTIM = 2
    TEAMMATES = 4
    ENEMIES = 8


class Killstreak:
    priority = 0
    text = None
    text_on_killstreak = None
    targets = KillstreakTarget.NONE
    show_kills = False
    sound = None

    def __init__(self, id_):
        self.id = id_


class KillstreakDatabase(dict):
    def __init__(self):
        super().__init__(self)

        self._downloadables = None
        self._strings = None
        self.text = ""

    def load_from_json(self, json):
        from ..ip_killstreaker import load_downloadables
        self.clear()

        if self._downloadables is not None:
            self._downloadables.clear()
            self._downloadables._unload_instance()

        if 'downloadables' in json:
            self._downloadables = load_downloadables(
                DOWNLOADLISTS_DIR / json['downloadables'])

        self._strings = BaseLangStrings(
            info.basename + "/killstreaks/" + json['strings'])

        self.text = self._strings[json['text']]

        for killstreak_id, killstreak_json in json['killstreaks'].items():
            self[killstreak_id] = killstreak = Killstreak(killstreak_id)

            killstreak.priority = killstreak_json.get('priority', 0)

            text = killstreak_json.get('text')
            if text is not None:
                killstreak.text = self._strings[text]

            text_on_killstreak = killstreak_json.get('text_on_killstreak')
            if text_on_killstreak is not None:
                killstreak.text_on_killstreak = (
                    self._strings[text_on_killstreak])

            killstreak.targets = killstreak_json.get(
                'recipients', KillstreakTarget.NONE)

            killstreak.show_kills = killstreak_json.get('show_kills', False)

            sound = killstreak_json.get('sound')
            if sound is not None:
                killstreak.sound = Sound(sound)

ks_database = KillstreakDatabase()
