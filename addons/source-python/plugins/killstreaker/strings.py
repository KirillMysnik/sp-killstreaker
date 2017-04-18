# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from colors import Color
from translations.strings import LangStrings

# Killstreaker
from .info import info


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
# Map color variables in translation files to actual Color instances
COLOR_SCHEME = {
    'color_tag': Color(242, 242, 242),
    'color_lightgreen': Color(67, 121, 183),
    'color_default': Color(242, 242, 242),
    'color_error': Color(255, 54, 54),
}

common_strings = LangStrings(info.name + "/common")
config_strings = LangStrings(info.name + "/config")
