# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from colors import Color
from core import echo_console
from events import Event
from listeners.tick import Delay
from messages import HudMsg, TextMsg
from players.dictionary import PlayerDictionary
from players.entity import Player
from stringtables.downloads import Downloadables

# Killstreaker
from .cvars import config_manager
from .ks_database import ks_database, KillstreakTarget, reload_scheme
from .paths import DOWNLOADLIST_PATH
from .strings import common_strings


# =============================================================================
# >> FUNCTIONS
# =============================================================================
def load_downloadables(filepath):
    downloadables = Downloadables()

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables


def announce_killstreak(ks_player, ks):
    indexes = set()

    if ks.targets & KillstreakTarget.TEAMMATES:
        for ks_player_ in ks_players.values():
            if ks_player_.player.team == ks_player.player.team:
                indexes.add(ks_player_.player.index)

    if ks.targets & KillstreakTarget.ENEMIES:
        for ks_player_ in ks_players.values():
            if ks_player_.player.team != ks_player.player.team:
                indexes.add(ks_player_.player.index)

    if ks.targets & KillstreakTarget.ATTACKER:
        indexes.add(ks_player.player.index)

    indexes = list(
        ks_player_.player.index for ks_player_ in ks_players.values()
        if not ks_player_.is_bot)

    if ks.sound is not None:
        ks.sound.play(*indexes)

    if ks.text_on_killstreak is not None:
        if ks.show_kills:
            lang_string = common_strings['is_on_ks with_kills']
        else:
            lang_string = common_strings['is_on_ks without_kills']

        hud_msg = HudMsg(
            lang_string.tokenized(
                name=ks_player.player.name,
                on_killstreak_text=ks.text_on_killstreak,
                kills=ks_player.killstreak,
            ),
            color1=KS_MSG_COLOR,
            x=KS_MSG_X,
            y=KS_MSG_Y,
            effect=KS_MSG_EFFECT,
            fade_in=KS_MSG_FADEIN,
            fade_out=KS_MSG_FADEOUT,
            hold_time=KS_MSG_HOLDTIME,
            fx_time=KS_MSG_FXTIME,
            channel=KS_MSG_CHANNEL,
        )
        hud_msg.send(*indexes)


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
_downloadables = load_downloadables(DOWNLOADLIST_PATH)

# Weapons that trigger SPECIAL_<weapon_name> killstreaks
SPECIAL_WEAPONS = ['knife', 'hegrenade']

# HudMsg properties
KS_MSG_COLOR = Color(196, 0, 0)
KS_MSG_X = -1
KS_MSG_Y = 0.2
KS_MSG_EFFECT = 2
KS_MSG_FADEIN = 0.01
KS_MSG_FADEOUT = 0
KS_MSG_HOLDTIME = 1.5
KS_MSG_FXTIME = 0
KS_MSG_CHANNEL = 1
DMG_MSG_COLOR = Color(255, 255, 255)
DMG_MSG_X = -1
DMG_MSG_Y = 0.4
DMG_MSG_EFFECT = 0
DMG_MSG_FADEIN = 0.0
DMG_MSG_FADEOUT = 0
DMG_MSG_HOLDTIME = 1.5
DMG_MSG_FXTIME = 0
DMG_MSG_CHANNEL = 2


# =============================================================================
# >> CLASSES
# =============================================================================
class GlobalStatus:
    firstblood_triggered = False


class KillstreakPlayer:
    def __init__(self, index):
        self.player = Player(index)

        self._queue = set()
        self._current_damage = 0
        self._killstreak = 0
        self._headstreak = 0
        self._multikill = 0
        self._current_killstreak_text = None

        self._reset_damage_text_delay = None
        self._reset_killstreak_text_delay = None
        self._reset_marker_delay = None
        self._clear_queue_delay = None

        self._is_bot = 'BOT' in self.player.steamid

    @property
    def is_bot(self):
        return self._is_bot

    @property
    def killstreak(self):
        return self._killstreak

    def _display_text(self):
        if self.is_bot:
            return

        if (
                config_manager['showdamage'] and
                self._current_damage > 0 and
                self._current_killstreak_text is None):

            # Display damage only
            ts = common_strings['showdamage hp'].tokenized(
                hp=self._current_damage)

        elif (
                self._current_damage <= 0 and
                self._current_killstreak_text is not None):

            # Display killstreak only
            ts = common_strings['showdamage ks'].tokenized(
                ks=self._current_killstreak_text)

        elif (
                config_manager['showdamage'] and
                self._current_damage > 0 and
                self._current_killstreak_text is not None):

            # Display both damage and killstreak
            ts = common_strings['showdamage both'].tokenized(
                ks=self._current_killstreak_text,
                hp=self._current_damage
            )

        else:

            # Hide all
            ts = ""

        # TextMsg(ts).send(self.player.index)
        HudMsg(
            ts,
            color1=DMG_MSG_COLOR,
            x=DMG_MSG_X,
            y=DMG_MSG_Y,
            effect=DMG_MSG_EFFECT,
            fade_in=DMG_MSG_FADEIN,
            fade_out=DMG_MSG_FADEOUT,
            hold_time=DMG_MSG_HOLDTIME,
            fx_time=DMG_MSG_FXTIME,
            channel=DMG_MSG_CHANNEL,
        ).send(self.player.index)

    def _reset_damage_text(self):
        self._current_damage = 0
        self._display_text()

    def _reset_killstreak_text(self):
        self._current_killstreak_text = None
        self._display_text()

    def _reset_marker(self):
        self.player.client_command('r_screenoverlay off')

    def _add_to_queue(self, ks_id):
        if not config_manager['killstreaks']:
            return

        if ks_id not in ks_database:
            return

        self._queue.add(ks_database[ks_id])

    def _delay_queue_clearing(self):
        if (
                self._clear_queue_delay is not None and
                self._clear_queue_delay.running):

            self._clear_queue_delay.cancel()

        self._clear_queue_delay = Delay(
            config_manager['queue_timeout'], self._clear_queue)

    def _clear_queue(self):
        if (
                self._reset_damage_text_delay is not None and
                self._reset_damage_text_delay.running):

            self._reset_damage_text_delay.cancel()

        if config_manager['showdamage_visible_for'] > 0:
            self._reset_damage_text_delay = Delay(
                config_manager['showdamage_visible_for'],
                self._reset_damage_text
            )

        queue = sorted(self._queue, key=lambda ks: ks.priority, reverse=True)
        self._queue.clear()
        self._multikill = 0

        if queue:
            ks = queue[0]

            if (ks.text is not None and
                    ks.targets & KillstreakTarget.ATTACKER):

                self._current_killstreak_text = ks.text

            if (self._reset_killstreak_text_delay is not None and
                    self._reset_killstreak_text_delay.running):

                self._reset_killstreak_text_delay.cancel()

            if config_manager['killstreaks_visible_for'] > 0:
                self._reset_killstreak_text_delay = Delay(
                    config_manager['killstreaks_visible_for'],
                    self._reset_killstreak_text
                )

            announce_killstreak(self, ks)

        self._display_text()

    def reset_killstreaks(self):
        self._multikill = 0
        self._killstreak = 0
        self._headstreak = 0
        self._current_damage = 0

    def count_damage(self, damage):
        self._current_damage += max(0, damage)

        # Delayed queue clearing
        self._delay_queue_clearing()

        if config_manager['hitsound'] is not None:
            config_manager['hitsound'].play(self.player.index)

        if (config_manager['hitmarker'] != "" and
                config_manager['hitmarker_visible_for'] > 0):

            self.player.client_command('r_screenoverlay {}'.format(
                config_manager['hitmarker']))

            if (self._reset_marker_delay is not None and
                    self._reset_marker_delay.running):

                self._reset_marker_delay.cancel()

            self._reset_marker_delay = Delay(
                config_manager['hitmarker_visible_for'],
                self._reset_marker
            )

    def count_kill(self, victim, headshot, weapon):
        self._killstreak += 1
        self._multikill += 1
        self._add_to_queue("KILL_X{}".format(self._killstreak))
        self._add_to_queue("MULTIKILL_X{}".format(self._multikill))

        if headshot:
            self._headstreak += 1
            self._add_to_queue("SPECIAL_HEADSHOT")
            self._add_to_queue("HEADSHOTS_X{}".format(self._headstreak))

        if victim.team == self.player.team:
            self._add_to_queue("SPECIAL_TEAMKILL")

        if weapon in SPECIAL_WEAPONS:
            self._add_to_queue("SPECIAL_{}".format(weapon.upper()))

        if not GlobalStatus.firstblood_triggered:
            self._add_to_queue("SPECIAL_FIRSTBLOOD")
            GlobalStatus.firstblood_triggered = True

        self._delay_queue_clearing()

    def count_death(self, suicide):
        self.reset_killstreaks()

        if suicide:
            self._add_to_queue("SPECIAL_SUICIDE")
            self._delay_queue_clearing()


# =============================================================================
# >> PLAYER DICTIONARIES
# =============================================================================
ks_players = PlayerDictionary(factory=KillstreakPlayer)


# =============================================================================
# >> EVENTS
# =============================================================================
@Event('player_hurt')
def on_player_hurt(game_event):
    userid = game_event['userid']
    attackerid = game_event['attacker']
    if attackerid in (0, userid):
        return

    ks_player = ks_players.from_userid(attackerid)
    ks_player.count_damage(game_event['dmg_health'])


@Event('player_death')
def on_player_death(game_event):
    userid = game_event['userid']
    attackerid = game_event['attacker']

    ks_player = ks_players.from_userid(userid)
    if attackerid in (0, userid):
        ks_player.count_death(True)
    else:
        ks_player.count_death(False)
        ks_attacker = ks_players.from_userid(attackerid)
        ks_attacker.count_kill(
            ks_player.player,
            game_event.get_bool('headshot'),
            game_event.get_string('weapon')
        )


@Event('round_start')
def on_round_start(game_event):
    GlobalStatus.firstblood_triggered = False

    if config_manager['killstreaks_reset_every_round']:
        for ks_player in ks_players.values():
            ks_player.reset_killstreaks()
