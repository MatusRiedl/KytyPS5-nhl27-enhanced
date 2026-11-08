"""Start the emulator the way play-nhl27.ps1 does: the same environment, the same command line, the same logs."""
import json
import os
import shutil
import subprocess
import threading
import time

from . import TITLE_ID
from .config import RESOLUTIONS

EXE = "kyty_emulator.exe"
LOG = "play_log.txt"
LOG_PREVIOUS = "play_log_previous.txt"
LOG_ERRORS = "play_log_errors.txt"
CONFIGS = ("cfgGlobal.json", f"cfg{TITLE_ID}.json")


def plan(folder, game):
    """(environment additions, argument string) for this build folder and game folder, as the ps1 builds them."""
    env, args = {}, ["--game", f'"{game}"']
    for name in CONFIGS:
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8-sig") as f:
            emu = json.load(f).get("emu") or {}
        for key, value in (emu.get("env") or {}).items():
            env[key] = ps_string(value)
        size = RESOLUTIONS.get(str(emu.get("screen_resolution")))
        if size:
            args += ["--screen-width", str(size[0]), "--screen-height", str(size[1])]
        if emu.get("fullscreen_enabled"):
            args.append("--fullscreen")
        if emu.get("extra_args"):
            extra = emu["extra_args"]
            args += [str(a) for a in extra] if isinstance(extra, list) else [str(extra)]
    return env, " ".join(args)


def ps_string(value):
    """What PowerShell's [string] gives for a JSON value (True/False for booleans)."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    return str(value)


class Game:
    """One running emulator at a time, watched on a thread."""

    def __init__(self, folder):
        self.folder = folder
        self.process = None
        self.started = None
        self.last_exit = None
        self.error = None
        self._lock = threading.Lock()

    def running(self):
        return self.process is not None and self.process.poll() is None

    def state(self):
        with self._lock:
            run = self.running()
            return {
                "running": run,
                "elapsed": int(time.time() - self.started) if run and self.started else 0,
                "last_exit": self.last_exit,
                "error": self.error,
            }

    def start(self, game):
        with self._lock:
            if self.running():
                return False
            exe = os.path.join(self.folder, EXE)
            if not os.path.isfile(exe):
                self.error = f"{EXE} is not next to Faceoff. Put Faceoff.exe in the build folder."
                return False
            env_add, args = plan(self.folder, game)
            env = dict(os.environ)
            env.update(env_add)
            log = os.path.join(self.folder, LOG)
            if os.path.exists(log):
                shutil.move(log, os.path.join(self.folder, LOG_PREVIOUS))
            out = open(log, "wb")
            err = open(os.path.join(self.folder, LOG_ERRORS), "wb")
            try:
                self.process = subprocess.Popen(f'"{exe}" {args}', cwd=self.folder, env=env, stdout=out, stderr=err,
                                                stdin=subprocess.DEVNULL,
                                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except OSError as e:
                out.close()
                err.close()
                self.error = f"Could not start the emulator: {e}"
                return False
            self.started = time.time()
            self.last_exit = None
            self.error = None
            threading.Thread(target=self._wait, args=(self.process, out, err), daemon=True).start()
            return True

    def _wait(self, process, out, err):
        code = process.wait()
        out.close()
        err.close()
        with self._lock:
            self.last_exit = code
