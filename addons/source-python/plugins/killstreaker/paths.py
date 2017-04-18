# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python
from paths import CFG_PATH

# Killstreaker
from .info import info


# =============================================================================
# >> GLOBAL VARIABLES
# =============================================================================
DOWNLOADLISTS_DIR_PATH = CFG_PATH / info.name / "downloadlists"
DOWNLOADLIST_PATH = DOWNLOADLISTS_DIR_PATH / "main.txt"
KS_DIR_PATH = CFG_PATH / info.name / "killstreaks"
