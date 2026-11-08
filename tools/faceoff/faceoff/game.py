"""The player's NHL 27 folder: is it there, what version, and its own icon (read from the dump, never shipped)."""
import base64
import json
import os

from . import TITLE_ID


def normalize(path):
    """A picked path -> the game folder (eboot.bin itself -> its folder)."""
    path = (path or "").strip().strip('"')
    if path and os.path.basename(path).lower() == "eboot.bin":
        path = os.path.dirname(path)
    return path


def inspect(path):
    """{'ok', 'status', 'path', 'title', 'version', 'title_id', 'icon'} for a game folder."""
    path = normalize(path)
    info = {"ok": False, "path": path, "title": "NHL 27", "version": "", "title_id": "", "icon": None}
    if not path:
        info["status"] = "No game folder chosen"
        return info
    if not os.path.isdir(path):
        info["status"] = "Game folder not found"
        return info
    if not os.path.isfile(os.path.join(path, "eboot.bin")):
        info["status"] = "No eboot.bin in this folder"
        return info
    info["ok"] = True
    info["status"] = "Ready"
    try:
        with open(os.path.join(path, "sce_sys", "param.json"), encoding="utf-8-sig") as f:
            param = json.load(f)
        info["version"] = param.get("contentVersion", "")
        info["title_id"] = param.get("titleId", "")
        name = param.get("localizedParameters", {}).get("en-US", {}).get("titleName")
        if name:
            info["title"] = name.replace("®", "").replace("  ", " ").strip()
    except (OSError, ValueError, AttributeError):
        pass
    if info["title_id"] and info["title_id"] != TITLE_ID:
        info["status"] = f"Ready (title {info['title_id']}, this build is made for {TITLE_ID})"
    icon = os.path.join(path, "sce_sys", "icon0.png")
    try:
        if os.path.getsize(icon) < 8 * 1024 * 1024:
            with open(icon, "rb") as f:
                info["icon"] = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
    except OSError:
        pass
    return info
