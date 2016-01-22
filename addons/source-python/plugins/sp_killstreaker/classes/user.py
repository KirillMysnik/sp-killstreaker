from colors import Color
from engines.sound import Sound
from listeners.tick import Delay
from messages import HudMsg
from messages import TextMsg
from players.entity import Player
from players.helpers import userid_from_index
from players.helpers import index_from_userid

from .ks_database import ks_database
from .ks_database import KillstreakTarget

from ..namespaces import status

from ..resource.config_cvars import cvar_damage_visible_timeout
from ..resource.config_cvars import cvar_hitmarker
from ..resource.config_cvars import cvar_hitmarker_visible_timeout
from ..resource.config_cvars import cvar_hitsound
from ..resource.config_cvars import cvar_killstreak_enabled
from ..resource.config_cvars import cvar_killstreak_visible_timeout
from ..resource.config_cvars import cvar_queue_timeout
from ..resource.config_cvars import cvar_showdamage_enabled

from ..resource.strings import strings_popups


KS_MSG_COLOR = Color(196, 0, 0)
KS_MSG_X = -1
KS_MSG_Y = 0.2
KS_MSG_EFFECT = 2
KS_MSG_FADEIN = 0.01
KS_MSG_FADEOUT = 0
KS_MSG_HOLDTIME = 1.5
KS_MSG_FXTIME = 0
KS_MSG_CHANNEL = 1

SPECIAL_WEAPONS = ['knife', 'hegrenade']


damage_text_visible_timeout = 2
killstreak_enabled = True
killstreak_text_visible_timeout = 2
marker_visible_timeout = 0.2
queue_timeout = 0.15
showdamage_enabled = True

hit_sound = None
marker_material = None


class UserManager(dict):
    def create(self, player):
        self[player.userid] = User(self, player)
        return self[player.userid]

    def delete(self, user):
        del self[user.player.userid]

    def get_by_index(self, index):
        return self[userid_from_index(index)]

    def announce_killstreak(self, user, killstreak):

        # Get target indexes
        indexes = set()

        if killstreak.targets & KillstreakTarget.TEAMMATES:
            for user_ in self.values():
                if user_.player.team == user.player.team:
                    indexes.add(user_.player.index)

        if killstreak.targets & KillstreakTarget.ENEMIES:
            for user_ in self.values():
                if user_.player.team != user.player.team:
                    indexes.add(user_.player.index)

        if killstreak.targets & KillstreakTarget.ATTACKER:
            indexes.add(user.player.index)

        # Play sound
        if killstreak.sound is not None:
            killstreak.sound.play(*indexes)

        # Show HudMsg
        if killstreak.text_on_killstreak is not None:
            if killstreak.show_kills:
                is_on_killstreak_string = 'is_on_killstreak show_kills'
            else:
                is_on_killstreak_string = 'is_on_killstreak'

            hud_msg = HudMsg(
                strings_popups[is_on_killstreak_string].tokenize(
                    name=user.player.name,
                    on_killstreak_text=killstreak.text_on_killstreak,
                    kills=user.killstreak,
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

user_manager = UserManager()


class User:
    def __init__(self, user_manager, player):
        self._user_manager = user_manager
        self.player = player

        self._queue = set()
        self._current_damage = 0
        self._killstreak = 0
        self._killstreak_heads = 0
        self._multikill = 0
        self._current_killstreak_text = None

        self._reset_damage_text_delay = None
        self._reset_killstreak_text_delay = None
        self._reset_marker_delay = None
        self._clear_queue_delay = None

    def _display_text(self):
        if (showdamage_enabled and
                self._current_damage > 0 and
                self._current_killstreak_text is None):

            # Display damage only
            ts = strings_popups['showdamage hp'].tokenize(
                hp=self._current_damage
            )

        elif (self._current_damage <= 0 and
              self._current_killstreak_text is not None and
              killstreak_enabled):

            # Display killstreak only
            ts = strings_popups['showdamage ks'].tokenize(
                killstreak_text=self._current_killstreak_text
            )

        elif (showdamage_enabled and
              self._current_damage > 0 and
              killstreak_enabled and
              self._current_killstreak_text is not None):

            # Display both damage and killstreak
            ts = strings_popups['showdamage both'].tokenize(
                hp=self._current_damage,
                killstreak_text=self._current_killstreak_text
            )

        else:

            # Hide all
            ts = ""

        TextMsg(ts).send(self.player.index)

    def _reset_damage_text(self):
        self._current_damage = 0
        self._display_text()

    def _reset_killstreak_text(self):
        self._current_killstreak_text = None
        self._display_text()

    def _reset_marker(self):
        self.player.client_command('r_screenoverlay off')

    def _add_to_queue(self, killstreak_id):
        killstreak = ks_database.get(killstreak_id)
        if killstreak is None:
            return

        self._queue.add(killstreak)

    def _delay_queue_clearing(self):
        if (self._clear_queue_delay is not None and
                self._clear_queue_delay.running):

            self._clear_queue_delay.cancel()

        self._clear_queue_delay = Delay(queue_timeout, self._clear_queue)

    def _clear_queue(self):
        if (self._reset_damage_text_delay is not None and
                self._reset_damage_text_delay.running):

            self._reset_damage_text_delay.cancel()

        if damage_text_visible_timeout > 0:
            self._reset_damage_text_delay = Delay(
                damage_text_visible_timeout, self._reset_damage_text)

        queue = sorted(self._queue, key=lambda ks: ks.priority, reverse=True)
        self._queue.clear()
        self._multikill = 0

        if queue:
            killstreak = queue[0]

            if (killstreak.text is not None and
                    killstreak.targets & KillstreakTarget.ATTACKER):

                self._current_killstreak_text = killstreak.text

                if (self._reset_killstreak_text_delay is not None and
                        self._reset_killstreak_text_delay.running):

                    self._reset_killstreak_text_delay.cancel()

                if killstreak_text_visible_timeout > 0:
                    self._reset_killstreak_text_delay = Delay(
                        killstreak_text_visible_timeout,
                        self._reset_killstreak_text
                    )

            user_manager.announce_killstreak(self, killstreak)

        self._display_text()

    @property
    def killstreak(self):
        return self._killstreak

    def count_damage(self, game_event):
        self._current_damage += max(0, game_event.get_int('dmg_health'))

        # Delayed queue clearing
        self._delay_queue_clearing()

        if hit_sound is not None:

            # Play hit sound
            hit_sound.play(self.player.index)

        if marker_material is not None and marker_visible_timeout > 0:

            # Show hit marker
            self.player.client_command(
                'r_screenoverlay {}'.format(marker_material))

            # Cancel hit marker delay (if any)
            if (self._reset_marker_delay is not None and
                    self._reset_marker_delay.running):

                self._reset_marker_delay.cancel()

            # Relaunch delay
            self._reset_marker_delay = Delay(
                marker_visible_timeout, self._reset_marker)

    def count_kill(self, game_event):
        self._killstreak += 1
        self._multikill += 1
        self._add_to_queue("KILL_X{}".format(self._killstreak))
        self._add_to_queue("MULTIKILL_X{}".format(self._multikill))

        if game_event.get_bool('headshot'):
            self._killstreak_heads += 1
            self._add_to_queue("SPECIAL_HEADSHOT")
            self._add_to_queue("HEADSHOTS_X{}".format(self._killstreak_heads))

        victimid = game_event.get_int('userid')
        victim = Player(index_from_userid(victimid))

        if victim.team == self.player.team:
            self._add_to_queue("SPECIAL_TEAMKILL")

        weapon = game_event.get_string('weapon')
        if weapon in SPECIAL_WEAPONS:
            self._add_to_queue("SPECIAL_{}".format(weapon.upper()))

        if not status.firstblood_triggered:
            self._add_to_queue("SPECIAL_FIRSTBLOOD")
            status.firstblood_triggered = True

        self._delay_queue_clearing()

    def count_death(self, game_event):
        self._multikill = 0
        self._killstreak_heads = 0
        self._killstreak = 0
        self._current_damage = 0

        attackerid = game_event.get_int('attacker')
        if attackerid == 0 or attackerid == self.player.userid:
            self._add_to_queue("SPECIAL_SUICIDE")
            self._delay_queue_clearing()


def update_from_cvars():

    # Update from spk_hitsound
    global hit_sound
    hit_sound_path = cvar_hitsound.get_string()
    if hit_sound_path == "":
        hit_sound = None
    else:
        hit_sound = Sound(hit_sound_path)

    # Update from spk_hitmarker
    global marker_material
    marker_material = cvar_hitmarker.get_string() or None

    # Update from spk_hitmarker_visible_timeout
    global marker_visible_timeout
    marker_visible_timeout = cvar_hitmarker_visible_timeout.get_float()

    # Update from spk_damage_visible_timeout
    global damage_text_visible_timeout
    damage_text_visible_timeout = cvar_damage_visible_timeout.get_float()

    # Update from spk_killstreak_visible_timeout
    global killstreak_text_visible_timeout
    killstreak_text_visible_timeout = (
        cvar_killstreak_visible_timeout.get_float())

    # Update from spk_queue_timeout
    global queue_timeout
    queue_timeout = cvar_queue_timeout.get_float()

    # Update from spk_showdamage_enabled
    global showdamage_enabled
    showdamage_enabled = cvar_showdamage_enabled.get_bool()

    # Update from spk_killstreak_enabled
    global killstreak_enabled
    killstreak_enabled = cvar_killstreak_enabled.get_bool()


