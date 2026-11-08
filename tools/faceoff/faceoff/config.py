"""cfgGlobal.json (the emulator settings the start script reads) and game_path.txt.

Writes change only the value of the key in place, so the file keeps its layout, comments-by-grouping and every other
key. A key that is not there yet is added through a full JSON rewrite."""
import json
import os
import re

CFG = "cfgGlobal.json"
GAME_PATH = "game_path.txt"

RESOLUTIONS = {
    "R1280X720": (1280, 720),
    "R1920X1080": (1920, 1080),
    "R2560X1440": (2560, 1440),
    "R3840X2160": (3840, 2160),
}
RES_SCALE_KEY = "KYTY_NHL_RES_SCALE"
DEFAULTS = {"resolution": "R2560X1440", "fullscreen": False, "scale": 0.6667, "trophies": True}


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_settings(folder):
    """The four settings Faceoff shows, from cfgGlobal.json (defaults for what is missing)."""
    s = dict(DEFAULTS)
    try:
        emu = read_json(os.path.join(folder, CFG)).get("emu", {})
    except (OSError, ValueError):
        return s
    if emu.get("screen_resolution") in RESOLUTIONS:
        s["resolution"] = emu["screen_resolution"]
    s["fullscreen"] = bool(emu.get("fullscreen_enabled", False))
    s["trophies"] = bool(emu.get("trophy_enabled", True))
    try:
        scale = float(emu.get("env", {}).get(RES_SCALE_KEY, ""))
        if 0.25 <= scale <= 1.0:
            s["scale"] = scale
    except ValueError:
        pass
    return s


def _json_value(v):
    return json.dumps(v)


def _replace(text, key, value):
    """Replace `"key": <scalar>` once; None when the key is not in the text."""
    pattern = re.compile(r'("' + re.escape(key) + r'"\s*:\s*)("(?:[^"\\]|\\.)*"|true|false|null|-?[0-9.eE+-]+)')
    new, n = pattern.subn(lambda m: m.group(1) + _json_value(value), text, count=1)
    return new if n else None


def save_setting(folder, name, value):
    """Store one setting (resolution, fullscreen, scale, trophies) in cfgGlobal.json."""
    if name == "resolution":
        if value not in RESOLUTIONS:
            raise ValueError(f"unknown resolution {value}")
        key, stored, in_env = "screen_resolution", value, False
    elif name == "fullscreen":
        key, stored, in_env = "fullscreen_enabled", bool(value), False
    elif name == "trophies":
        key, stored, in_env = "trophy_enabled", bool(value), False
    elif name == "scale":
        scale = float(value)
        if not 0.25 <= scale <= 1.0:
            raise ValueError("render scale must be 0.25 to 1.0")
        key, stored, in_env = RES_SCALE_KEY, f"{scale:g}", True
    else:
        raise ValueError(f"unknown setting {name}")

    path = os.path.join(folder, CFG)
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    new = _replace(text, key, stored)
    if new is None:
        data = json.loads(text)
        emu = data.setdefault("emu", {})
        (emu.setdefault("env", {}) if in_env else emu)[key] = stored
        new = json.dumps(data, indent=2) + "\n"
    json.loads(new)                                   # never write a broken file
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    os.replace(tmp, path)
    return load_settings(folder)


def load_game_path(folder):
    try:
        with open(os.path.join(folder, GAME_PATH), encoding="utf-8-sig") as f:
            return f.readline().strip()
    except OSError:
        return ""


def save_game_path(folder, game):
    with open(os.path.join(folder, GAME_PATH), "w", encoding="utf-8") as f:
        f.write(game + "\n")
