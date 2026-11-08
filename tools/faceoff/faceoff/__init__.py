"""Faceoff: a launcher for the KytyPS5-nhl27-enhanced build of NHL 27."""
import os
import sys

__version__ = "1.0.0"
TITLE_ID = "PPSA34063"


def home():
    """The build folder (the one holding kyty_emulator.exe): next to Faceoff.exe, or FACEOFF_HOME, or the current
    folder when run from source."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.environ.get("FACEOFF_HOME") or os.getcwd())
