"""What the page can ask for (window.pywebview.api.*). Every call returns plain JSON-able data."""
import glob
import os

from . import TITLE_ID, __version__, config, game, launch

CACHE_DIR = "_PipelineCache"
SAVE_DIR = "_SaveData"
WARM_BYTES = 40 * 1024 * 1024       # below this the first arena load still compiles most shaders


class Api:
    def __init__(self, folder):
        self._folder = folder
        self._game = launch.Game(folder)
        self._window = None
        self._store_memo = None

    # ---- state -----------------------------------------------------------------------------------------------
    def state(self):
        return {
            "version": __version__,
            "folder": self._folder,
            "emulator": os.path.isfile(os.path.join(self._folder, launch.EXE)),
            "game": game.inspect(config.load_game_path(self._folder)),
            "settings": config.load_settings(self._folder),
            "cache": self.cache_info(),
            "saves": self.saves(),
            "run": self._game.state(),
        }

    def run_state(self):
        return self._game.state()

    def _store_ids_in_exe(self, ids):
        """Which shader-store ids (the 12 hex digits in PPSA34063.<s+id>.programs) this emulator build uses. The
        emulator names its store after its shader-sources hash (pipelineCache.cpp, KYTY_GIT_SHADER_TREE), which is
        a string inside the exe."""
        exe = os.path.join(self._folder, launch.EXE)
        try:
            key = (exe, os.path.getmtime(exe), tuple(sorted(ids)))
            if self._store_memo and self._store_memo[0] == key:
                return self._store_memo[1]
            with open(exe, "rb") as f:
                data = f.read()
        except OSError:
            return set()
        found = {i for i in ids if i.encode("ascii") in data}
        self._store_memo = (key, found)
        return found

    def cache_info(self):
        """The shader cache: its size, and whether this build can use it. A store from another build (an older RC
        folder copied over) is not used: the next start compiles again."""
        files = [p for p in glob.glob(os.path.join(self._folder, CACHE_DIR, f"{TITLE_ID}.*")) if os.path.isfile(p)]
        stores = {}
        for p in files:
            parts = os.path.basename(p).split(".")
            if len(parts) == 3 and parts[2] == "programs":
                stores[parts[1].lstrip("s")] = p
        current = self._store_ids_in_exe(stores)
        current_bytes = sum(os.path.getsize(stores[i]) for i in current)
        size = sum(os.path.getsize(p) for p in files)
        old = sum(os.path.getsize(p) for i, p in stores.items() if i not in current)
        stale = old > 1024 * 1024 and current_bytes <= 1024 * 1024
        warm = current_bytes > 1024 * 1024 and size >= WARM_BYTES
        return {"bytes": size, "files": len(files), "warm": warm, "stale": stale}

    def saves(self):
        root = os.path.join(self._folder, SAVE_DIR, TITLE_ID)
        try:
            return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
        except OSError:
            return []

    # ---- actions ---------------------------------------------------------------------------------------------
    def pick_folder(self):
        import webview
        picked = self._window.create_file_dialog(webview.FileDialog.FOLDER) if self._window else None
        if not picked:
            return None
        path = game.normalize(picked[0] if isinstance(picked, (list, tuple)) else picked)
        info = game.inspect(path)
        if info["ok"]:
            config.save_game_path(self._folder, path)
        return info

    def save_setting(self, name, value):
        try:
            return {"ok": True, "settings": config.save_setting(self._folder, name, value)}
        except (OSError, ValueError) as e:
            return {"ok": False, "error": str(e), "settings": config.load_settings(self._folder)}

    def play(self):
        info = game.inspect(config.load_game_path(self._folder))
        if not info["ok"]:
            return {"ok": False, "error": info["status"]}
        ok = self._game.start(info["path"])
        return {"ok": ok, "error": None if ok else (self._game.error or "The game is already running")}

    def clear_cache(self):
        if self._game.running():
            return {"ok": False, "error": "Close the game first"}
        for p in glob.glob(os.path.join(self._folder, CACHE_DIR, f"{TITLE_ID}*")):
            try:
                os.remove(p)
            except OSError as e:
                return {"ok": False, "error": str(e)}
        return {"ok": True, "cache": self.cache_info()}

    def open(self, what):
        targets = {
            "folder": self._folder,
            "saves": os.path.join(self._folder, SAVE_DIR),
            "log": os.path.join(self._folder, launch.LOG),
            "cache": os.path.join(self._folder, CACHE_DIR),
            "game": config.load_game_path(self._folder),
        }
        path = targets.get(what)
        if path and os.path.exists(path):
            os.startfile(path)
            return True
        return False
