"""Explicit native-Steam library selection inside RE6's Proton/Wine environment."""
import ctypes
import os
from pathlib import Path

from patch_candidate import Rejected


def wine_version():
    if os.name != "nt":
        raise Rejected("Use run-proton.sh on Linux to start the helper inside RE6's Proton environment.")
    try:
        function = ctypes.CDLL("ntdll").wine_get_version
        function.argtypes = []
        function.restype = ctypes.c_char_p
        version = function()
        if not version:
            raise AttributeError("Empty Wine version")
        return version.decode("utf-8", errors="replace")
    except (OSError, AttributeError) as exc:
        raise Rejected("--proton-library is only available inside Proton/Wine.") from exc


def checked_library(path):
    version = wine_version()
    library = Path(path).resolve(strict=True)
    if not (library / "steamapps" / "appmanifest_221040.acf").is_file():
        raise Rejected("The selected Proton library has no RE6 Steam app manifest.")
    # discover_installs verifies app ID and containment; validate_process still
    # verifies the exact disk hash, live image and instruction contexts.
    return library, version
