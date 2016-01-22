from advanced_ts import BaseLangStrings

from ..info import info


class KillstreakTarget:
    NONE = 0
    ATTACKER = 1
    VICTIM = 2
    TEAMMATES = 4
    ENEMIES = 8


class Killstreak:
    text = None
    text_on_killstreak = None
    targets = KillstreakTarget.NONE
    show_kills = False


class KillstreakDatabase(dict):
    def __init__(self):
        super().__init__(self)

        self._strings = None
        self.text = ""

    def load_from_json(self, json):
        self.clear()

        self._strings = BaseLangStrings(
            info.basename + "/killstreaks" + json['strings'])

        self.text = self._strings[json['text']]

        for killstreak_id, killstreak_json in json['killstreaks'].items():
            self[killstreak_id] = killstreak = Killstreak()
            killstreak.text = killstreak_json.get('text')
            killstreak.text_on_killstreak = killstreak_json.get(
                'text_on_killstreak')

            killstreak.targets = killstreak_json.get(
                'targets', KillstreakTarget.NONE)

            killstreak.show_kills = killstreak_json.get('show_kills', False)

ks_database = KillstreakDatabase()
