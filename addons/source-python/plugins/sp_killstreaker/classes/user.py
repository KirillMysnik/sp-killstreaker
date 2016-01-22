from colors import Color
from engines.sound import Sound
from listeners.tick import Delay
from messages import HudMsg
from messages import TextMsg
from players import Player
from players.helpers import userid_from_index
from players.helpers import index_from_userid

from .ks_database import ks_database
from .ks_database import KillstreakTarget

from ..resource.config_cvars import cvar_damage_visible_timeout
from ..resource.config_cvars import cvar_hitmarker
from ..resource.config_cvars import cvar_hitmarker_visible_timeout
from ..resource.config_cvars import cvar_hitsound
from ..resource.config_cvars import cvar_killstreak_visible_timeout
from ..resource.config_cvars import cvar_queue_timeout

from ..resource.strings import strings_popups


KS_MSG_COLOR = Color(124, 173, 255)
KS_MSG_X = -1
KS_MSG_Y = 0.05
KS_MSG_EFFECT = 2
KS_MSG_FADEIN = 0.05
KS_MSG_FADEOUT = 0
KS_MSG_HOLDTIME = 1.5
KS_MSG_FXTIME = 0
KS_MSG_CHANNEL = 1

SPECIAL_WEAPONS = ['knife', 'hegrenade']


damage_text_visible_timeout = 2
killstreak_text_visible_timeout = 2
marker_visible_timeout = 0.2
queue_timeout = 0.15

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
                    is_on_killstreak=killstreak.text_on_killstreak,
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
        if self._current_damage > 0 and self._current_killstreak_text is None:

            # Display damage only
            ts = strings_popups['showdamage hp'].tokenize(
                hp=self._current_damage
            )

        elif (self._current_damage <= 0 and
              self._current_killstreak_text is not None):

            # Display killstreak only
            ts = strings_popups['showdamage ks'].tokenize(
                killstreak_text=self._current_killstreak_text
            )

        elif (self._current_damage > 0 and
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
        if (self._clear_queue_delay is not None and
                self._clear_queue_delay.running):

            self._clear_queue_delay.cancel()

        self._clear_queue_delay = Delay(queue_timeout, self._clear_queue)

    def _clear_queue(self):
        queue = sorted(self._queue, key=lambda ks: ks.priority, reverse=True)
        self._queue.clear()
        self._multikill = 0

        if not queue:
            return

        killstreak = queue[0]
        if (killstreak.text is not None and
                killstreak.targets & KillstreakTarget.ATTACKER):

            self._current_killstreak_text = killstreak.text
            self._display_text()

            if (self._reset_killstreak_text_delay is not None and
                    self._reset_killstreak_text_delay.running):

                self._reset_killstreak_text_delay.cancel()

            self._reset_killstreak_text_delay = Delay(
                killstreak_text_visible_timeout, self._reset_killstreak_text)

        user_manager.announce_killstreak(self, killstreak)

    @property
    def killstreak(self):
        return self._killstreak

    def count_damage(self, game_event):
        self._current_damage += max(0, game_event.get_int('dmg_health'))

        # Display damage amount
        self._display_text()

        # Play hit sound
        if hit_sound is not None:
            hit_sound.play(self.player.index)

        # Show hit marker
        if marker_material is not None:
            self.player.client_command(
                'r_screenoverlay {}'.format(marker_material))

        # Cancel delays if any
        if (self._reset_damage_text_delay is not None and
                self._reset_damage_text_delay.running):

            self._reset_damage_text_delay.cancel()

        if (self._reset_marker_delay is not None and
                self._reset_marker_delay.running):

            self._reset_marker_delay.cancel()

        # Relaunch delays
        self._reset_damage_text_delay = Delay(
            damage_text_visible_timeout, self._reset_damage_text)

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

        victimid = game_event.get_int('userid')
        if victimid == self.player.userid:
            return

        victim = Player(index_from_userid(victimid))

        if victim.team == self.player.team:
            self._add_to_queue("SPECIAL_TEAMKILL")

        weapon = game_event.get_string('weapon')
        if weapon in SPECIAL_WEAPONS:
            self._add_to_queue("SPECIAL_{}".format(weapon.upper()))

    def count_death(self, game_event):
        self._multikill = 0
        self._killstreak_heads = 0
        self._killstreak = 0
        self._current_damage = 0

        attackerid = game_event.get_int('attacker')
        if attackerid == 0 or attackerid == self.player.userid:
            self._add_to_queue("SPECIAL_SUICIDE")


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

